"""
gen/result_delivery.py – Ergebnis-Auslieferung an den User (aiogram).
"""

import logging
import os
import time
import uuid
from urllib.parse import urlparse

from aiogram.types import FSInputFile, InputMediaPhoto

from src.infrastructure.metrics import record_timing
from src.presentation.telegram.handlers.common import set_context
from src.presentation.telegram.handlers.gen.download import download_url_to_bytes
from src.utils.media_utils import detect_media_from_bytes
from src.utils.strings import get_text

logger = logging.getLogger(__name__)
MAX_URL_LENGTH = 400


def _has_media_type(model, token: str) -> bool:
    types = getattr(model, "type", None) or []
    t = (token or "").strip().lower()
    if not t:
        return False
    for mt in types:
        cur = str(mt or "").strip().lower()
        if cur == t or t in cur:
            return True
    return False


def _infer_media_kind_from_url(url: str) -> str | None:
    if not isinstance(url, str):
        return None
    u = url.strip().lower()
    if not (u.startswith("http://") or u.startswith("https://")):
        return None
    path = (urlparse(u).path or "").lower()
    if path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff")):
        return "image"
    if path.endswith((".mp4", ".mov", ".webm", ".mkv", ".avi")):
        return "video"
    if path.endswith((".mp3", ".wav", ".ogg", ".m4a", ".flac")):
        return "audio"
    if "replicate.delivery" in u:
        return "image"
    return None


def _parse_raw_result(raw):
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


async def _try_send_as_file(facade, user_id, res_bytes, res, caption, model):
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
            fs = FSInputFile(temp_path)
            if media_type == "video":
                await facade.send_video(user_id, fs, caption=caption)
            elif media_type == "audio":
                await facade.send_audio(user_id, fs, caption=caption)
            else:
                await facade.send_photo(user_id, fs, caption=caption)
            return True
        except Exception as ex:
            logger.warning("Media send failed, fallback to document: %s", ex)
            fs = FSInputFile(temp_path)
            await facade.send_document(user_id, fs, caption=caption)
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


def _extract_urls_from_result(result):
    if isinstance(result, list) and result:
        urls = []
        for item in result:
            _, url = _parse_raw_result(item)
            if url and isinstance(url, str) and url.strip().startswith(("http://", "https://")):
                urls.append(url)
        return urls if urls else None
    _, res = _parse_raw_result(result[0] if isinstance(result, list) and result else result)
    if res and isinstance(res, str) and res.strip().startswith(("http://", "https://")):
        return [res]
    return None


async def parse_and_deliver(facade, user_id, result, model, cost, lang, ctx, is_chat, prompt, keyboards_fn):
    t0 = time.perf_counter()
    raw = result[0] if isinstance(result, list) and result else result
    res_bytes, res = _parse_raw_result(raw)

    if is_chat:
        txt = res if res else get_text("media_link_too_long", lang) if res_bytes else ""
        if txt:
            try:
                last_id = (ctx or {}).get("last_chat_button_msg_id")
                if last_id:
                    try:
                        await facade.edit_message_reply_markup(user_id, last_id, reply_markup=None)
                    except Exception:
                        pass
            except Exception:
                pass

            msg = await facade.send_message(user_id, txt, reply_markup=keyboards_fn.get_chat_active_menu(lang))

            try:
                new_ctx = dict(ctx or {})
                new_ctx["last_chat_button_msg_id"] = msg.message_id
                set_context(user_id, new_ctx)
            except Exception:
                pass
        record_timing("gen.result_delivery.parse_and_deliver", time.perf_counter() - t0)
        return

    caption = get_text("success_caption", lang).format(prompt=(prompt or "")[:50], cost=cost)
    is_valid_url = (
        res
        and isinstance(res, str)
        and res.strip().startswith(("http://", "https://"))
        and " " not in res.strip()[:50]
    )
    url_too_long = is_valid_url and len(res) > MAX_URL_LENGTH

    def safe_msg(could_not_send=False):
        if could_not_send or not res or url_too_long or (res and (res.startswith("b'") or res.startswith('b"'))):
            return get_text("media_send_failed", lang)
        return f"{res[:400]}\n\n💰 {cost} Credits" if len(res) > 400 else f"{res}\n\n💰 {cost} Credits"

    inferred_url_kind = _infer_media_kind_from_url(res) if is_valid_url else None
    is_media_model = (
        _has_media_type(model, "video")
        or _has_media_type(model, "audio")
        or _has_media_type(model, "image")
        or inferred_url_kind is not None
    )
    sent = False

    multi_urls = _extract_urls_from_result(result)
    if multi_urls and len(multi_urls) > 1 and is_media_model and model.type and "image" in model.type:
        try:
            media_group = [
                InputMediaPhoto(media=url, caption=caption if i == 0 else None)
                for i, url in enumerate(multi_urls[:10])
            ]
            await facade.send_media_group(user_id, media_group)
            sent = True
        except Exception as e:
            logger.warning("Media group failed, falling back to single: %s", e)
            multi_urls = None

    if not sent and (res_bytes or (is_valid_url and is_media_model)) and is_media_model:
        sent = await _try_send_as_file(facade, user_id, res_bytes, res, caption, model)
    if not sent and is_valid_url and is_media_model and not url_too_long:
        try:
            if inferred_url_kind == "video" or _has_media_type(model, "video"):
                await facade.send_video(user_id, res, caption=caption)
            elif inferred_url_kind == "audio" or _has_media_type(model, "audio"):
                await facade.send_audio(user_id, res, caption=caption)
            else:
                await facade.send_photo(user_id, res, caption=caption)
            sent = True
        except Exception as e:
            logger.error("Media Send Error: %s", e)
            from src.presentation.telegram.handlers.gen.error_checks import is_uri_too_large

            if is_uri_too_large(e):
                sent = await _try_send_as_file(facade, user_id, res_bytes, res, caption, model)
    if not sent:
        if res and is_valid_url:
            try:
                await facade.send_message(
                    user_id, f"{res}\n\n💰 {cost} Credits", disable_web_page_preview=True
                )
            except Exception:
                await facade.send_message(user_id, safe_msg(could_not_send=True))
        else:
            await facade.send_message(user_id, safe_msg(could_not_send=True))

    record_timing("gen.result_delivery.parse_and_deliver", time.perf_counter() - t0)
