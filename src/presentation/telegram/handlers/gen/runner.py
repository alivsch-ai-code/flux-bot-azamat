"""
runner.py – Generierungs-Ausführung (run_generation)

Enthält die zentrale Funktion create_run_generation, die die eigentliche run_generation-Funktion
zurückgibt. run_generation:
- Prüft Credits
- Ruft generation_service.process_request auf (mit Retry bei 429)
- Bei technischem Fehler: Fallback-Modell versuchen
- Bei Erfolg: result (inkl. URL/FileOutput von Replicate) unverändert an parse_and_deliver
- parse_and_deliver nutzt src.utils.media_utils.detect_media_from_bytes und download_url_to_bytes
- Bereinigt Media-Temp-Dateien und Context (bei nicht-Chat)

WICHTIG: Der Link zur Datei (replicate.delivery) kommt als Teil von result von process_request.
 unified_client gibt FileOutput-Objekte (.url, .read()) durch; parse_and_deliver extrahiert URL/Bytes.
"""

import logging
import os
import time

from telebot import types

from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import clear_context, get_context
from src.presentation.telegram.handlers.gen import (
    is_rate_limit,
    is_technical_error,
    parse_and_deliver,
    smart_update_status,
)
from src.presentation.telegram.handlers.gen.chat_sessions import append_with_summary_if_needed
from src.utils.gimmicks import get_random_tip
from src.utils.strings import get_text

logger = logging.getLogger(__name__)


def create_run_generation(bot, db, generation_service, get_lang):
    """
    Erstellt die run_generation-Funktion mit gebundenen Abhängigkeiten.
    Gibt eine Funktion (user_id, model_key, prompt, media_files, is_chat=False) zurück.
    """

    def run_generation(user_id, model_key, prompt, media_files, is_chat=False):
        ctx = get_context(user_id)
        lang = get_lang(user_id)
        model = db.get_model_by_key(model_key)
        if not model:
            return
        keep_context_for_image_loop = False
        try:
            cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
            if int(db.get_user_credits(user_id)) < cost:
                smart_update_status(bot, user_id, get_text("err_no_credits", lang), ctx)
                return
            wait_msg_id = smart_update_status(bot, user_id, get_text("status_generating", lang).format(tip=get_random_tip(lang)), ctx)
            bot.send_chat_action(user_id, 'typing' if is_chat else 'upload_photo')

            success, result = generation_service.process_request(user_id, model, prompt, media_files)
            for _ in range(4):
                if success or not is_rate_limit(result):
                    break
                smart_update_status(bot, user_id, get_text("please_wait_longer", lang), ctx)
                time.sleep(20)
                success, result = generation_service.process_request(user_id, model, prompt, media_files)

            if not success and is_technical_error(result):
                fallback_model = db.get_fallback_model(model)
                if fallback_model:
                    logger.info("Fallback zu %s...", fallback_model.name)
                    smart_update_status(bot, user_id, get_text("fallback_attempt", lang).format(model=model.name, fallback=fallback_model.name), ctx)
                    success, result = generation_service.process_request(user_id, fallback_model, prompt, media_files)
                    if success:
                        model, cost = fallback_model, int(fallback_model.custom_price or fallback_model.internal_cost)

            try:
                bot.delete_message(user_id, wait_msg_id)
            except Exception:
                pass

            if success:
                parse_and_deliver(bot, user_id, result, model, cost, lang, ctx, is_chat, prompt, keyboards)

                # Chat-Historie für Textmodelle persistent speichern (mit Auto-Summary)
                if is_chat and model.type and "text" in model.type:
                    try:
                        raw = result[0] if isinstance(result, list) and result else result
                        if isinstance(raw, str):
                            append_with_summary_if_needed(
                                db,
                                user_id,
                                model_key,
                                {"role": "assistant", "content": raw},
                            )
                    except Exception:
                        pass

                # Verhalten nach Erfolg:
                # - Chat-Modus: nur Antwort anzeigen (kein Hauptmenü).
                # - Image-Modelle im normalen Modus: im selben Modell bleiben und nach neuem Prompt fragen.
                # - Andere Modelle: wie bisher zurück ins Hauptmenü.
                if not is_chat:
                    if model.type and "image" in model.type:
                        keep_context_for_image_loop = True
                        from src.presentation.telegram.handlers.common import set_context

                        menu_path = (ctx or {}).get("menu_path", model.menu_path or "image")
                        new_ctx = {
                            "model_key": model.key,
                            "step": "waiting_for_prompt",
                            "media_paths": [],
                            "menu_path": menu_path,
                        }
                        set_context(user_id, new_ctx)
                        menu_mode = db.get_bot_setting("menu_mode", "commands")
                        if menu_mode == "keyboard":
                            bot.send_message(
                                user_id,
                                get_text("model_req_prompt", lang),
                                parse_mode="HTML",
                            )
                        else:
                            from src.config.settings import config
                            webapp_url = (config.APP_URL or "").rstrip("/")
                            back_markup = keyboards.get_image_loop_buttons(
                                lang, menu_mode, webapp_url, model.key, menu_path or "image",
                            )
                            bot.send_message(
                                user_id,
                                get_text("model_req_prompt", lang),
                                reply_markup=back_markup,
                                parse_mode="HTML",
                            )
                    else:
                        time.sleep(1)
                        menu_mode = db.get_bot_setting("menu_mode", "commands")
                        menu_path = ctx.get("menu_path", "root") if ctx else "root"
                        all_models = db.get_all_models()
                        if menu_mode == "keyboard":
                            next_markup = keyboards.get_path_reply_keyboard(all_models, lang, menu_path)
                        elif menu_mode == "webapp":
                            from src.config.settings import config
                            from urllib.parse import quote
                            if config.APP_URL:
                                base = config.APP_URL.rstrip("/") + "/webapp"
                                webapp_url = base + ("?path=" + quote(menu_path, safe="") if menu_path and menu_path != "root" else "")
                                next_markup = types.InlineKeyboardMarkup()
                                next_markup.add(types.InlineKeyboardButton(
                                    get_text("menu_mode_webapp", lang),
                                    web_app=types.WebAppInfo(url=webapp_url)
                                ))
                            else:
                                next_markup = keyboards.get_dynamic_model_menu(all_models, lang, menu_path)
                        else:
                            next_markup = keyboards.get_dynamic_model_menu(all_models, lang, menu_path)
                        bot.send_message(
                            user_id,
                            get_text("msg_next_step", lang),
                            reply_markup=next_markup,
                            parse_mode="HTML",
                        )
            else:
                logger.error("Generation failed: %s", result)
                try:
                    db.insert_generation_error(user_id, model_key, str(result))
                except Exception:
                    pass
                smart_update_status(bot, user_id, get_text("err_gen_failed", lang).format(result=result), ctx)

        except Exception as e:
            logger.exception("System Error: %s", e)
            err_text = str(e)
            if "<" in err_text or ">" in err_text or len(err_text) > 200:
                msg = get_text("system_error_generic", get_lang(user_id))
            else:
                msg = f"System Error: {err_text}"
            try:
                smart_update_status(bot, user_id, msg, ctx)
            except Exception:
                bot.send_message(user_id, msg, parse_mode=None)
        finally:
            if media_files:
                for mf in media_files:
                    if mf.path and os.path.exists(mf.path):
                        try:
                            os.remove(mf.path)
                        except Exception:
                            pass
            if not is_chat and not keep_context_for_image_loop:
                clear_context(user_id)

    return run_generation
