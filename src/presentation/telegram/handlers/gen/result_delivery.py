"""
gen/result_delivery.py – Ergebnis-Auslieferung an den User

Verarbeitet die API-Antwort (URL, Bytes, FileOutput, repr(bytes)) und sendet das Ergebnis
an den User. Reihenfolge: 1) Parse raw result → res_bytes, res (URL). 2) Bei Medien:
Datei-Versand (Temp-Datei, send_photo/video/audio, bei Fehler send_document). 3) Bei Fehlern:
URL-Versand als Fallback. 4) Letzter Fallback: Fehlermeldung.
Nutzt detect_media_from_bytes für Typ-Erkennung, download_url_to_bytes für URLs.
"""

import logging
import os
import time
import uuid

from telebot import types

from src.infrastructure.metrics import record_timing
from src.presentation.telegram.handlers.common import set_context
from src.presentation.telegram.handlers.gen.download import download_url_to_bytes
from src.utils.media_utils import detect_media_from_bytes
from src.utils.strings import get_text

logger = logging.getLogger(__name__)
MAX_URL_LENGTH = 400


def _parse_raw_result(raw):
    """Wandelt API-Roh-Ergebnis in (res_bytes, res) um. res = URL oder None."""
    if isinstance(raw, bytes):
        return raw, None
    if hasattr(raw, "read") and callable(getattr(raw, "read", None)):
        try:
            res_bytes = raw.read()
            res_url = getattr(raw, "url", None)
            res_url = res_url() if callable(res_url) else res_url
            return res_bytes, res_url
        except Exception:
            return None, str(raw)
    if hasattr(raw, "url"):
        url_val = getattr(raw, "url", None)
        url = url_val() if callable(url_val) else url_val
        return None, url
    if isinstance(raw, str):
        return None, raw
    s = str(raw)
    if s.startswith("b'") or s.startswith('b"'):
        try:
            import ast
            return ast.literal_eval(s), None
        except Exception:
            return None, s
    return None, s


def _try_send_as_file(bot, user_id, res_bytes, res, caption, model):
    """Sendet Medien als Datei (Temp-File). Bei Fehler Fallback zu send_document."""
    data = res_bytes
    if not data and res and str(res).startswith(("http://", "https://")):
        data = download_url_to_bytes(res)
    if not data:
        logger.warning("_try_send_as_file: no data")
        return False
    media_type, ext = detect_media_from_bytes(data)
    temp_path = None
    try:
        temp_path = os.path.join("temp", f"tg_{user_id}_{uuid.uuid4().hex[:8]}{ext}")
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(data)
        try:
            with open(temp_path, "rb") as f:
                if media_type == "video":
                    bot.send_video(user_id, f, caption=caption)
                elif media_type == "audio":
                    bot.send_audio(user_id, f, caption=caption)
                else:
                    bot.send_photo(user_id, f, caption=caption)
            return True
        except Exception as ex:
            logger.warning("Media send failed, fallback to document: %s", ex)
            with open(temp_path, "rb") as f:
                bot.send_document(user_id, f, caption=caption)
            return True
    except Exception as ex2:
        logger.error("File send failed: %s", ex2)
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def parse_and_deliver(bot, user_id, result, model, cost, lang, ctx, is_chat, prompt, keyboards_fn):
    """
    Parst das API-Ergebnis und liefert es aus. Berücksichtigt Chat-Modus vs. Medien-Modus.
    """
    t0 = time.perf_counter()
    raw = result[0] if isinstance(result, list) and result else result
    res_bytes, res = _parse_raw_result(raw)

    if is_chat:
        txt = res if res else get_text("media_link_too_long", lang) if res_bytes else ""
        if txt:
            # Alten "Chat beenden"-Button entfernen, falls vorhanden
            try:
                last_id = (ctx or {}).get("last_chat_button_msg_id")
                if last_id:
                    try:
                        bot.edit_message_reply_markup(user_id, last_id, reply_markup=None)
                    except Exception:
                        pass
            except Exception:
                pass

            msg = bot.send_message(user_id, txt, reply_markup=keyboards_fn.get_chat_active_menu(lang))

            # Aktuelle Nachricht als neue Button-Message merken
            try:
                new_ctx = dict(ctx or {})
                new_ctx["last_chat_button_msg_id"] = msg.message_id
                set_context(user_id, new_ctx)
            except Exception:
                pass
        record_timing("gen.result_delivery.parse_and_deliver", time.perf_counter() - t0)
        return

    caption = get_text("success_caption", lang).format(prompt=(prompt or "")[:50], cost=cost)
    is_valid_url = res and isinstance(res, str) and res.strip().startswith(("http://", "https://")) and " " not in res.strip()[:50]
    url_too_long = is_valid_url and len(res) > MAX_URL_LENGTH

    def safe_msg(could_not_send=False):
        if could_not_send or not res or url_too_long or (res and (res.startswith("b'") or res.startswith('b"'))):
            return get_text("media_send_failed", lang)
        return f"{res[:400]}\n\n💰 {cost} Credits" if len(res) > 400 else f"{res}\n\n💰 {cost} Credits"

    is_media_model = model.type and ("video" in model.type or "audio" in model.type or "image" in model.type)
    sent = False

    if (res_bytes or (is_valid_url and is_media_model)) and is_media_model:
        sent = _try_send_as_file(bot, user_id, res_bytes, res, caption, model)
    if not sent and is_valid_url and is_media_model and not url_too_long:
        try:
            if model.type and "video" in model.type:
                bot.send_video(user_id, res, caption=caption)
            elif model.type and "audio" in model.type:
                bot.send_audio(user_id, res, caption=caption)
            else:
                bot.send_photo(user_id, res, caption=caption)
            sent = True
        except Exception as e:
            logger.error("Media Send Error: %s", e)
            from src.presentation.telegram.handlers.gen.error_checks import is_uri_too_large
            if is_uri_too_large(e):
                sent = _try_send_as_file(bot, user_id, res_bytes, res, caption, model)
    if not sent:
        if res and is_valid_url:
            try:
                bot.send_message(user_id, f"{res}\n\n💰 {cost} Credits", disable_web_page_preview=True)
            except Exception:
                bot.send_message(user_id, safe_msg(could_not_send=True))
        else:
            bot.send_message(user_id, safe_msg(could_not_send=True))

    record_timing("gen.result_delivery.parse_and_deliver", time.perf_counter() - t0)
