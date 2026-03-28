"""
media_handlers.py – Media-Upload (aiogram 3).
"""

from __future__ import annotations

import logging
import os
import time
import uuid

from aiogram import F
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from src.infrastructure.metrics import record_timing
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import get_context, set_context
from src.presentation.telegram.handlers.gen import ctx_media_to_list
from src.utils.strings import get_text

logger = logging.getLogger(__name__)


def register_media_handlers(router, facade, db, get_lang, run_generation) -> None:
    MAX_FILE_BYTES = 20 * 1024 * 1024

    async def _save_incoming_file(user_id: int, file_id: str, default_ext: str) -> str:
        t0 = time.perf_counter()
        downloaded = await facade.download_file_bytes(file_id)
        if len(downloaded) > MAX_FILE_BYTES:
            raise ValueError("file_too_large")
        os.makedirs("temp", exist_ok=True)
        ext = default_ext
        path = os.path.join("temp", f"user_{user_id}_{uuid.uuid4().hex[:8]}{ext}")
        with open(path, "wb") as f:
            f.write(downloaded)
        record_timing("gen.media.save_incoming_file", time.perf_counter() - t0)
        return path

    async def _handle_unsolicited_media(msg: Message, file_id: str, media_type: str, default_ext: str):
        user_id = msg.chat.id
        lang = get_lang(user_id)
        try:
            path = await _save_incoming_file(user_id, file_id, default_ext)
        except ValueError as e:
            if str(e) == "file_too_large":
                await facade.send_message(user_id, "❌ Datei ist zu groß (max. 20 MB).")
            else:
                await facade.send_message(user_id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
            return
        except Exception as e:
            logger.exception("Unsolicited media save failed: %s", e)
            await facade.send_message(user_id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
            return

        category = "image" if media_type == "image" else "video" if media_type == "video" else "audio" if media_type == "audio" else "tools"
        ctx = {
            "step": "waiting_for_model_for_media",
            "media_paths": [{"path": path, "type": media_type}],
            "menu_path": category,
        }
        set_context(user_id, ctx)

        menu_mode = db.get_bot_setting("menu_mode", "commands")
        if menu_mode == "webapp":
            from src.config.settings import config

            if config.APP_URL and config.APP_URL.startswith("https://"):
                from urllib.parse import quote

                app_url = config.APP_URL.rstrip("/")
                webapp_url = app_url + "/webapp?path=" + quote(category, safe="")
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=get_text("menu_mode_webapp", lang),
                                web_app=WebAppInfo(url=webapp_url),
                            )
                        ]
                    ]
                )
                await facade.send_message(
                    user_id,
                    get_text("webapp_media_choose", lang),
                    reply_markup=markup,
                    parse_mode="HTML",
                )
                return
        all_models = db.get_all_models()
        markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path=category)
        await facade.send_message(
            user_id,
            "✅ Medium erhalten.\n\nMöchtest du dafür ein KI-Modell auswählen? Wähle unten ein Modell aus:",
            reply_markup=markup,
            parse_mode="HTML",
        )

    async def process_media_upload(msg: Message, file_id: str, media_type: str, default_ext: str):
        user_id = msg.chat.id
        ctx = get_context(user_id)
        t0 = time.perf_counter()
        in_model_flow = (
            ctx
            and ctx.get("model_key")
            and ctx.get("step") in ("waiting_for_media", "waiting_for_image", "viewing_model")
        )
        if not in_model_flow:
            await _handle_unsolicited_media(msg, file_id, media_type, default_ext)
            return
        try:
            path = await _save_incoming_file(user_id, file_id, default_ext)
            if "media_paths" not in ctx:
                ctx["media_paths"] = []
            ctx["media_paths"].append({"path": path, "type": media_type})
            ctx["step"] = "waiting_for_prompt"
            model = db.get_model_by_key(ctx["model_key"])
            media_list = ctx_media_to_list(ctx)
            if model and model.type and "upscale" in model.type and media_list:
                await run_generation(user_id, ctx["model_key"], "", media_list)
            else:
                pending = (ctx.get("pending_webapp_prompt") or "").strip()
                if pending:
                    await run_generation(user_id, ctx["model_key"], pending, media_list)
                    return
                count = len(ctx["media_paths"])
                await facade.send_message(
                    user_id,
                    get_text("media_received", get_lang(user_id)).format(count=count)
                    + " "
                    + get_text("model_req_prompt", get_lang(user_id)),
                    reply_markup=keyboards.get_back_menu(get_lang(user_id), f"sel_{ctx['model_key']}"),
                    parse_mode="HTML",
                )
                set_context(user_id, ctx)
        except ValueError as e:
            if str(e) == "file_too_large":
                await facade.send_message(user_id, "❌ Datei ist zu groß (max. 20 MB).")
            else:
                await facade.send_message(user_id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
        except Exception as e:
            logger.exception("Media upload failed: %s", e)
            await facade.send_message(msg.chat.id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
        finally:
            record_timing("gen.media.process_media_upload", time.perf_counter() - t0)

    @router.message(F.photo, F.chat.type == ChatType.PRIVATE)
    async def on_photo(msg: Message):
        await process_media_upload(msg, msg.photo[-1].file_id, "image", ".jpg")

    @router.message(F.video, F.chat.type == ChatType.PRIVATE)
    async def on_video(msg: Message):
        await process_media_upload(msg, msg.video.file_id, "video", ".mp4")

    @router.message(F.document, F.chat.type == ChatType.PRIVATE)
    async def on_document(msg: Message):
        if not msg.document:
            return
        ext = os.path.splitext(msg.document.file_name or "")[1] or ".bin"
        await process_media_upload(msg, msg.document.file_id, "document", ext)
