"""
log_bot_get_chat_id.py – Hilfstool: Chat-ID für LOG_BOT_ALOSCHA ermitteln

Starten:
    python -m archive.legacy_tools.log_bot_get_chat_id

Vorgehen:
1) In Telegram den Bot LOG_BOT_ALOSCHA öffnen und /start senden.
2) Danach irgendeine Nachricht senden.
3) Das Tool antwortet im Chat mit der chat.id (für Private Chat oder Gruppe).

Diese ID kannst du dann als LOG_ADMIN_ID in .env / Render-Env setzen.
"""

import os

import telebot
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    token = os.getenv("LOG_BOT_ALOSCHA")
    if not token:
        raise RuntimeError("LOG_BOT_ALOSCHA fehlt in .env")

    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start"])
    def on_start(msg):
        bot.send_message(
            msg.chat.id,
            "✅ Bereit. Sende mir eine Nachricht, dann antworte ich mit deiner chat_id.",
        )

    @bot.message_handler(func=lambda m: True, content_types=["text", "photo", "video", "document", "audio", "voice", "sticker"])
    def on_any(msg):
        chat_id = msg.chat.id
        chat_type = msg.chat.type
        title = getattr(msg.chat, "title", None)
        username = getattr(msg.chat, "username", None)

        details = []
        details.append(f"chat_id: {chat_id}")
        details.append(f"type: {chat_type}")
        if title:
            details.append(f"title: {title}")
        if username:
            details.append(f"username: @{username}")

        bot.send_message(chat_id, "🆔 " + "\n".join(details))

    bot.infinity_polling(timeout=60, long_polling_timeout=30)


if __name__ == "__main__":
    main()

