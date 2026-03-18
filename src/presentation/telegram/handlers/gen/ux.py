"""
gen/ux.py – User-Experience-Hilfsfunktionen

Stellt Hilfsfunktionen bereit, die die Interaktion im Chat verbessern:
- smart_update_status: Versucht eine bestehende Bot-Nachricht zu bearbeiten (Edit), statt
  eine neue zu senden. Verhindert Chat-Spam bei Status-Updates wie "Generiere...",
  "Bitte warte...", etc. Nutzt last_bot_msg_id aus dem User-Context. Falls Edit fehlschlägt
  (z.B. Nachricht zu alt, gleicher Text), wird eine neue Nachricht gesendet.
"""

import logging

logger = logging.getLogger(__name__)


def smart_update_status(bot, user_id, text, ctx, markup=None):
    """
    Aktualisiert die letzte Bot-Nachricht per Edit oder sendet neu.
    bot: TeleBot-Instanz
    user_id: Chat-ID
    text: Anzuzeigender Text
    ctx: User-Context mit 'last_bot_msg_id'
    markup: Optional InlineKeyboardMarkup
    Returns: message_id
    """
    msg_id = ctx.get("last_bot_msg_id")
    try:
        if msg_id:
            bot.edit_message_text(
                text, user_id, msg_id,
                reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False
            )
            return msg_id
        msg = bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
        return msg.message_id
    except Exception as e:
        logger.warning("Edit failed for user %s, sending new message: %s", user_id, e)
        msg = bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
        return msg.message_id
