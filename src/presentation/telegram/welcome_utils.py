"""Hilfsfunktionen für die Willkommens-Nachricht (inkl. Welcome-Video)."""
import os

# Projekt-Root (von src/presentation/telegram/ 4 Ebenen hoch)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WELCOME_VIDEO_PATH = os.path.join(_ROOT, "video", "welcome_azamat.mp4")


def send_welcome_with_video(bot, chat_id: int, welcome_text: str, markup=None):
    """
    Sendet die Willkommens-Nachricht. Falls video/welcome_azamat.mp4 existiert,
    wird es als Video mit Caption gesendet, sonst als Text-Nachricht.
    """
    if os.path.isfile(WELCOME_VIDEO_PATH):
        try:
            with open(WELCOME_VIDEO_PATH, "rb") as f:
                bot.send_video(
                    chat_id, f, caption=welcome_text,
                    parse_mode="HTML", reply_markup=markup
                )
            return
        except Exception:
            pass
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)
