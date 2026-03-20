"""
media_handlers.py – Media-Upload (Foto, Video, Dokument)

Registriert:
- process_media_upload: Lädt Datei herunter, speichert in temp/, fügt zu ctx.media_paths hinzu.
  Bei upscale-Modellen: sofort run_generation. Sonst: Aufforderung für Prompt.
- on_photo, on_video, on_document: Message-Handler, die process_media_upload aufrufen.
"""

import logging
import os
import time
import uuid

from src.infrastructure.metrics import record_timing
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import get_context, set_context
from src.presentation.telegram.handlers.gen import ctx_media_to_list
from src.utils.strings import get_text

logger = logging.getLogger(__name__)


def register_media_handlers(bot, db, get_lang, run_generation) -> None:
    """Registriert process_media_upload und die Message-Handler für photo, video, document."""
 
    MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB Limit

    def _save_incoming_file(user_id: int, file_id: str, default_ext: str) -> str:
        t0 = time.perf_counter()
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)

        if len(downloaded) > MAX_FILE_BYTES:
            raise ValueError("file_too_large")

        os.makedirs("temp", exist_ok=True)
        ext = default_ext
        if getattr(file_info, "file_path", None):
            ext = os.path.splitext(file_info.file_path)[1] or default_ext
        path = os.path.join("temp", f"user_{user_id}_{uuid.uuid4().hex[:8]}{ext}")
        with open(path, "wb") as f:
            f.write(downloaded)
        record_timing("gen.media.save_incoming_file", time.perf_counter() - t0)
        return path

    def _handle_unsolicited_media(msg, file_id: str, media_type: str, default_ext: str):
        """
        Fallback: User lädt ein Medium hoch, ohne dass ein Modell-Flow aktiv ist.
        Wir speichern das Medium und bieten direkt die passende Modell-Kategorie zur Auswahl an.
        """
        user_id = msg.chat.id
        lang = get_lang(user_id)
        try:
            path = _save_incoming_file(user_id, file_id, default_ext)
        except ValueError as e:
            if str(e) == "file_too_large":
                bot.send_message(user_id, "❌ Datei ist zu groß (max. 20 MB).")
            else:
                bot.send_message(user_id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
            return
        except Exception as e:
            logger.exception("Unsolicited media save failed: %s", e)
            bot.send_message(user_id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
            return

        category = "image" if media_type == "image" else "video" if media_type == "video" else "audio" if media_type == "audio" else "tools"
        ctx = {
            "step": "waiting_for_model_for_media",
            "media_paths": [{"path": path, "type": media_type}],
            "menu_path": category,
        }
        set_context(user_id, ctx)

        all_models = db.get_all_models()
        markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path=category)
        bot.send_message(
            user_id,
            "✅ Medium erhalten.\n\nMöchtest du dafür ein KI-Modell auswählen? Wähle unten ein Modell aus:",
            reply_markup=markup,
            parse_mode="HTML",
        )

    def process_media_upload(msg, file_id: str, media_type: str, default_ext: str):
        user_id = msg.chat.id
        ctx = get_context(user_id)
        t0 = time.perf_counter()
        in_model_flow = (
            ctx
            and ctx.get("model_key")
            and ctx.get("step") in ("waiting_for_media", "waiting_for_image", "viewing_model")
        )
        if not in_model_flow:
            _handle_unsolicited_media(msg, file_id, media_type, default_ext)
            return
        try:
            path = _save_incoming_file(user_id, file_id, default_ext)
            if "media_paths" not in ctx:
                ctx["media_paths"] = []
            ctx["media_paths"].append({"path": path, "type": media_type})
            ctx["step"] = "waiting_for_prompt"
            model = db.get_model_by_key(ctx["model_key"])
            media_list = ctx_media_to_list(ctx)
            if model and model.type and "upscale" in model.type and media_list:
                run_generation(user_id, ctx["model_key"], "", media_list)
            else:
                count = len(ctx["media_paths"])
                bot.send_message(
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
                bot.send_message(user_id, "❌ Datei ist zu groß (max. 20 MB).")
            else:
                bot.send_message(user_id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
        except Exception as e:
            logger.exception("Media upload failed: %s", e)
            bot.send_message(msg.chat.id, "❌ Upload-Fehler. Bitte versuchen Sie es erneut.")
        finally:
            record_timing("gen.media.process_media_upload", time.perf_counter() - t0)

    @bot.message_handler(content_types=["photo"])
    def on_photo(msg):
        process_media_upload(msg, msg.photo[-1].file_id, "image", ".jpg")

    @bot.message_handler(content_types=["video"])
    def on_video(msg):
        process_media_upload(msg, msg.video.file_id, "video", ".mp4")

    @bot.message_handler(content_types=["document"])
    def on_document(msg):
        if not msg.document:
            return
        ext = os.path.splitext(msg.document.file_name or "")[1] or ".bin"
        process_media_upload(msg, msg.document.file_id, "document", ext)
