"""
gen/ux.py – User-Experience-Hilfsfunktionen (aiogram / TelegramBotFacade).
"""

import logging

logger = logging.getLogger(__name__)


async def smart_update_status(facade, user_id, text, ctx, markup=None):
    """
    Aktualisiert die letzte Bot-Nachricht per Edit oder sendet neu.
    Returns: message_id
    """
    msg_id = ctx.get("last_bot_msg_id")
    try:
        if msg_id:
            await facade.edit_message_text(
                text,
                user_id,
                msg_id,
                reply_markup=markup,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
            return msg_id
        msg = await facade.send_message(
            user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False
        )
        return msg.message_id
    except Exception as e:
        logger.warning("Edit failed for user %s, sending new message: %s", user_id, e)
        msg = await facade.send_message(
            user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False
        )
        return msg.message_id
