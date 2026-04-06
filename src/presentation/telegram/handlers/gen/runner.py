"""
runner.py – Generierungs-Ausführung (async, aiogram / TelegramBotFacade).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import clear_context, get_context, set_context
from src.presentation.telegram.handlers.gen import (
    is_rate_limit,
    is_technical_error,
    parse_and_deliver,
    smart_update_status,
)
from src.presentation.telegram.handlers.gen.chat_sessions import (
    append_global_chat_event,
    append_with_summary_if_needed,
    build_chat_prompt_from_messages,
)
from src.infrastructure.ai.unified_client import is_replicate_webhook_pending_result
from src.utils.gimmicks import get_random_tip
from src.utils.strings import get_text

logger = logging.getLogger(__name__)
REUSABLE_MEDIA_TTL_SECONDS = 240


def _to_webapp_result_payload(result) -> dict:
    """Builds a lightweight, UI-friendly result payload for the WebApp."""
    raw_items = result if isinstance(result, list) else [result]
    urls: list[str] = []
    texts: list[str] = []

    for item in raw_items:
        val = None
        if isinstance(item, str):
            val = item
        elif hasattr(item, "url"):
            maybe_url = getattr(item, "url", None)
            val = maybe_url() if callable(maybe_url) else maybe_url
        elif item is not None:
            val = str(item)

        if not isinstance(val, str):
            continue
        s = val.strip()
        if not s:
            continue
        if s.startswith(("http://", "https://")):
            urls.append(s)
        else:
            texts.append(s)

    return {
        "result_urls": urls[:10],
        "result_text": (texts[0][:4000] if texts else ""),
    }


async def post_generation_followup_after_success(
    facade,
    db,
    user_id: int,
    model,
    result,
    cost: int,
    lang: str,
    ctx,
    is_chat: bool,
    prompt: str,
    model_key: str,
    chat_history_mode: str | None,
):
    """Nach erfolgreicher Auslieferung: Chat-Historie, Bild-Loop-Kontext, nächstes Menü."""
    if model.type and "text" in model.type and chat_history_mode in ("once_off", "persistent"):
        try:
            raw = result[0] if isinstance(result, list) and result else result
            assistant_text = raw if isinstance(raw, str) else str(raw)
            if assistant_text.strip():
                append_global_chat_event(db, user_id, "assistant", assistant_text)
                append_with_summary_if_needed(
                    db,
                    user_id,
                    model_key,
                    {"role": "assistant", "content": assistant_text},
                )
        except Exception:
            pass

    if not is_chat:
        if model.type and "image" in model.type:
            menu_path = (ctx or {}).get("menu_path", model.menu_path or "image")
            prev_media = list((ctx or {}).get("media_paths") or [])
            reusable_media = []
            for item in prev_media:
                if isinstance(item, dict):
                    p = str(item.get("path") or "")
                    t = str(item.get("type") or "image")
                    if p.startswith("http://") or p.startswith("https://"):
                        reusable_media.append({"path": p, "type": t})
                elif isinstance(item, str) and (item.startswith("http://") or item.startswith("https://")):
                    reusable_media.append({"path": item, "type": "image"})
            expires_at = int(time.time()) + REUSABLE_MEDIA_TTL_SECONDS if reusable_media else 0
            new_ctx = {
                "model_key": model.key,
                "step": "waiting_for_prompt",
                "media_paths": [],
                "recent_media_paths": reusable_media,
                "recent_media_expires_at": expires_at,
                "last_prompt": (prompt or "").strip(),
                "generation_options": {},
                "menu_path": menu_path,
            }
            set_context(user_id, new_ctx)
            prompt_msg = get_text("model_req_prompt_with_model", lang).format(model=model.name)
            if reusable_media:
                ttl_minutes = max(1, int(REUSABLE_MEDIA_TTL_SECONDS / 60))
                prompt_msg += "\n\n" + get_text("reuse_media_offer", lang).format(
                    count=len(reusable_media), minutes=ttl_minutes
                )
            menu_mode = db.get_bot_setting("menu_mode", "commands")
            back_markup = None
            if menu_mode != "keyboard":
                from src.config.settings import config

                webapp_url = (config.APP_URL or "").rstrip("/")
                back_markup = keyboards.get_image_loop_buttons(
                    lang, menu_mode, webapp_url, model.key, menu_path or "image"
                )
                if reusable_media:
                    rows = list(back_markup.inline_keyboard)
                    rows.append(
                        [
                            InlineKeyboardButton(
                                text=get_text("btn_reuse_media_yes", lang),
                                callback_data="reuse_media_yes",
                            ),
                            InlineKeyboardButton(
                                text=get_text("btn_reuse_media_no", lang),
                                callback_data="reuse_media_no",
                            ),
                        ]
                    )
                    rows.append(
                        [
                            InlineKeyboardButton(
                                text=get_text("btn_reuse_media_text", lang),
                                callback_data="reuse_media_text",
                            )
                        ]
                    )
                    back_markup = InlineKeyboardMarkup(inline_keyboard=rows)
            if menu_mode == "keyboard":
                await facade.send_message(user_id, prompt_msg, parse_mode="HTML")
            else:
                await facade.send_message(
                    user_id, prompt_msg, reply_markup=back_markup, parse_mode="HTML"
                )
        else:
            await asyncio.sleep(1)
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
                    webapp_url = base + (
                        "?path=" + quote(menu_path, safe="") if menu_path and menu_path != "root" else ""
                    )
                    next_markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=get_text("menu_mode_webapp", lang),
                                    web_app=WebAppInfo(url=webapp_url),
                                )
                            ]
                        ]
                    )
                else:
                    next_markup = keyboards.get_dynamic_model_menu(all_models, lang, menu_path)
            else:
                next_markup = keyboards.get_dynamic_model_menu(all_models, lang, menu_path)
            await facade.send_message(
                user_id,
                get_text("msg_next_step", lang),
                reply_markup=next_markup,
                parse_mode="HTML",
            )


def create_run_generation(facade, db, generation_service, get_lang):
    """Liefert eine async run_generation(user_id, model_key, prompt, media_files, ...)."""

    async def run_generation(
        user_id,
        model_key,
        prompt,
        media_files,
        is_chat=False,
        chat_history_mode: str | None = None,
        chat_user_name: str | None = None,
    ):
        ctx = get_context(user_id)
        lang = get_lang(user_id)
        model = db.get_model_by_key(model_key)
        if not model:
            return {"status": "error", "error": "model_not_found"}
        keep_context_for_image_loop = False
        webhook_pending = False
        try:
            base_cost = int(model.custom_price if model.custom_price is not None else model.internal_cost)
            generation_options = (ctx or {}).get("generation_options") or {}
            cost = base_cost
            is_text_model = bool(model.type and "text" in model.type)
            prompt_for_generation = prompt

            if chat_history_mode == "once_off" and is_text_model:
                try:
                    user_name = (
                        chat_user_name
                        or getattr(db, "get_user_username_or_name", lambda _u: None)(user_id)
                        or "User"
                    )
                    messages = append_with_summary_if_needed(
                        db,
                        user_id,
                        model_key,
                        {"role": "user", "content": prompt or "", "user_name": user_name},
                    )
                    sys_prompt = get_text("azamat_private_chat_prompt", lang)
                    sys_prompt = f"{sys_prompt}\n\n{get_text('azamat_user_name_hint', lang).format(name=user_name)}"
                    prompt_for_generation = build_chat_prompt_from_messages(
                        messages,
                        prompt or "",
                        system_prompt=sys_prompt,
                        current_user_name=user_name,
                    )
                except Exception:
                    prompt_for_generation = prompt
            rid = (model.replicate_id or "").lower()
            if "google/veo-3.1" in rid:
                try:
                    duration = int(generation_options.get("duration", 5) or 5)
                except (TypeError, ValueError):
                    duration = 5
                duration = max(5, duration)
                cost = int(round(base_cost * (duration / 5.0)))
            if int(db.get_user_credits(user_id)) < cost:
                await smart_update_status(facade, user_id, get_text("err_no_credits", lang), ctx)
                return {"status": "error", "error": get_text("err_no_credits", lang), "credits": int(db.get_user_credits(user_id))}
            wait_msg_id = await smart_update_status(
                facade,
                user_id,
                get_text("status_generating", lang).format(tip=get_random_tip(lang)),
                ctx,
            )
            await facade.send_chat_action(
                user_id, "typing" if (is_chat or is_text_model) else "upload_photo"
            )

            def _call_gen():
                return generation_service.process_request(
                    user_id,
                    model,
                    prompt_for_generation,
                    media_files,
                    generation_params=generation_options,
                    charge_cost=cost,
                    lang=lang,
                    is_chat=is_chat,
                    chat_history_mode=chat_history_mode,
                )

            success, result = await asyncio.to_thread(_call_gen)
            # Replicate: bei Limit-Überschreitung oft HTTP 429 / „throttled“
            # (https://replicate.com/docs/topics/predictions/rate-limits) — kurz warten und wiederholen.
            for _ in range(4):
                if success or not is_rate_limit(result):
                    break
                await smart_update_status(facade, user_id, get_text("please_wait_longer", lang), ctx)
                await asyncio.sleep(20)
                success, result = await asyncio.to_thread(_call_gen)

            if not success and is_technical_error(result):
                fallback_model = db.get_fallback_model(model)
                if fallback_model:
                    logger.info("Fallback zu %s...", fallback_model.name)
                    await smart_update_status(
                        facade,
                        user_id,
                        get_text("fallback_attempt", lang).format(model=model.name, fallback=fallback_model.name),
                        ctx,
                    )

                    def _call_fb():
                        return generation_service.process_request(
                            user_id,
                            fallback_model,
                            prompt_for_generation,
                            media_files,
                            generation_params=generation_options,
                            charge_cost=cost,
                            lang=lang,
                            is_chat=is_chat,
                            chat_history_mode=chat_history_mode,
                        )

                    success, result = await asyncio.to_thread(_call_fb)
                    if success:
                        model = fallback_model

            try:
                await facade.delete_message(user_id, wait_msg_id)
            except Exception:
                pass

            if success and is_replicate_webhook_pending_result(result):
                webhook_pending = True
                await facade.send_message(
                    user_id,
                    get_text("gen_webhook_pending", lang),
                    parse_mode="HTML",
                )
                return {
                    "status": "pending",
                    "message": get_text("gen_webhook_pending", lang),
                    "credits": int(db.get_user_credits(user_id)),
                }
            elif success:
                await parse_and_deliver(
                    facade, user_id, result, model, cost, lang, ctx, is_chat, prompt, keyboards
                )
                if not is_chat and model.type and "image" in model.type:
                    keep_context_for_image_loop = True
                await post_generation_followup_after_success(
                    facade,
                    db,
                    user_id,
                    model,
                    result,
                    cost,
                    lang,
                    ctx,
                    is_chat,
                    prompt,
                    model_key,
                    chat_history_mode,
                )
                out = _to_webapp_result_payload(result)
                return {
                    "status": "success",
                    "credits": int(db.get_user_credits(user_id)),
                    **out,
                }
            else:
                logger.error("Generation failed: %s", result)
                try:
                    db.insert_generation_error(user_id, model_key, str(result))
                except Exception:
                    pass
                await smart_update_status(
                    facade, user_id, get_text("err_gen_failed", lang).format(result=result), ctx
                )
                return {
                    "status": "error",
                    "error": str(result),
                    "credits": int(db.get_user_credits(user_id)),
                }

        except Exception as e:
            logger.exception("System Error: %s", e)
            err_text = str(e)
            if "<" in err_text or ">" in err_text or len(err_text) > 200:
                msg = get_text("system_error_generic", get_lang(user_id))
            else:
                msg = f"System Error: {err_text}"
            try:
                await smart_update_status(facade, user_id, msg, ctx)
            except Exception:
                await facade.send_message(user_id, msg, parse_mode=None)
            return {"status": "error", "error": msg, "credits": int(db.get_user_credits(user_id))}
        finally:
            if media_files:
                for mf in media_files:
                    if mf.path and os.path.exists(mf.path):
                        try:
                            os.remove(mf.path)
                        except Exception:
                            pass
            if not is_chat and not keep_context_for_image_loop and not webhook_pending:
                clear_context(user_id)

    return run_generation
