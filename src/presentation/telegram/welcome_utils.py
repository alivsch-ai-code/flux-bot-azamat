"""Hilfsfunktionen für die Willkommens-Nachricht (inkl. Welcome-Video)."""
import os

from aiogram.types import FSInputFile

# Projekt-Root (von src/presentation/telegram/ 4 Ebenen hoch)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WELCOME_VIDEO_PATH = os.path.join(_ROOT, "video", "welcome_azamat.mp4")


async def send_welcome_with_video(facade, chat_id: int, welcome_text: str, markup=None):
    """
    Sendet die Willkommens-Nachricht. Falls video/welcome_azamat.mp4 existiert,
    wird es als Video mit Caption gesendet, sonst als Text-Nachricht.
    """
    if os.path.isfile(WELCOME_VIDEO_PATH):
        try:
            await facade.send_video(
                chat_id,
                FSInputFile(WELCOME_VIDEO_PATH),
                caption=welcome_text,
                parse_mode="HTML",
                reply_markup=markup,
            )
            return
        except Exception:
            pass
    await facade.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)
