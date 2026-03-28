"""
payment_handler.py – Telegram Stars (aiogram 3).
"""

from __future__ import annotations

import logging
from typing import Optional

from aiogram import F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Message, PreCheckoutQuery, WebAppInfo

from src.presentation.telegram.handlers.common import clear_context
from src.config.settings import config
from src.utils.strings import get_text

logger = logging.getLogger(__name__)

CREDIT_PACKAGES = config.CREDIT_PACKAGES


def get_user_lang(msg) -> str:
    try:
        user = msg.from_user if hasattr(msg, "from_user") else msg
        return (user.language_code or "de")[:2]
    except (AttributeError, TypeError):
        return "de"


async def send_invoice_to_user(facade, user_id: int, credits: int, price: int, lang: str = "de", payload_suffix: str = "") -> None:
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⭐️ {price} XTR bezahlen" if lang == "de" else f"Pay ⭐️ {price} XTR", pay=True)],
            [InlineKeyboardButton(text="❌ Abbrechen" if lang == "de" else "❌ Cancel", callback_data="cancel_invoice")],
        ]
    )
    payload = f"credits_{credits}{payload_suffix}"
    await facade.send_invoice(
        chat_id=user_id,
        title=f"{credits} AI Credits",
        description="Aufladung für Bild- und Videogenerierung",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Credits", amount=int(price))],
        reply_markup=markup,
    )


async def show_shop_logic(
    facade,
    message,
    db,
    lang: str = "de",
    force_inline: bool = False,
    group_chat_id: Optional[int] = None,
) -> None:
    clear_context(message.chat.id)
    user_id = message.chat.id
    menu_mode = db.get_bot_setting("menu_mode", "commands")

    if not force_inline and menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
        app_url = config.APP_URL.rstrip("/")
        shop_url = app_url + "/webapp?view=shop"
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=get_text("menu_mode_webapp", lang), web_app=WebAppInfo(url=shop_url))]
            ]
        )
        text = get_text("webapp_open_shop", lang)
        try:
            await facade.edit_message_text(text, user_id, message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await facade.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        return

    rows = []
    for label, desc, price, credits in CREDIT_PACKAGES:
        cb = f"buy_{credits}_{price}"
        if group_chat_id is not None:
            cb = f"{cb}_g{group_chat_id}"
        rows.append([InlineKeyboardButton(text=f"💎 {desc} ({price} ⭐️)", callback_data=cb)])
    rows.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="nav_main")])

    markup = InlineKeyboardMarkup(inline_keyboard=rows)

    current_credits = (
        db.get_group_user_credits(user_id, group_chat_id) + db.get_user_credits(user_id)
        if group_chat_id is not None
        else db.get_user_credits(user_id)
    )

    grp_note = "\n<i>👉 Diese Credits werden für die Gruppe gutgeschrieben.</i>\n" if group_chat_id is not None else ""
    text = (
        f"<b>💳 Guthaben aufladen</b>\n\n"
        f"<b>Dein Stand:</b> <code>{current_credits} Credits</code>\n\n"
        f"<i>Wähle ein Paket – sicher via Telegram Stars</i>\n"
        f"{grp_note}\n"
        f"<b>Pakete:</b>"
    )

    try:
        await facade.edit_message_text(
            text,
            user_id,
            message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
    except Exception:
        await facade.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")


def register(router, facade, db) -> None:
    @router.callback_query(F.data == "cmd_shop")
    async def shop_callback(call: CallbackQuery):
        try:
            chat = call.message.chat if call.message else None
            grp_id = chat.id if chat and getattr(chat, "type", "") in ("group", "supergroup") else None
            await show_shop_logic(facade, call.message, db, get_user_lang(call.from_user), group_chat_id=grp_id)
            await call.answer()
        except Exception as e:
            logger.warning("Shop callback failed: %s", e)

    @router.message(Command("buy", "shop"))
    async def shop_command(message: Message):
        await show_shop_logic(facade, message, db, get_user_lang(message))

    @router.callback_query(F.data.startswith("buy_"))
    async def send_invoice_cb(call: CallbackQuery):
        try:
            parts = call.data.split("_")
            credits, price = int(parts[1]), int(parts[2])
            group_chat_id = None
            if len(parts) >= 4 and parts[3].startswith("g"):
                try:
                    group_chat_id = int(parts[3][1:])
                except (ValueError, IndexError):
                    pass
            lang = get_user_lang(call.from_user)
            payload_suffix = f"_grp_{group_chat_id}" if group_chat_id is not None else ""
            user_id = call.from_user.id
            await send_invoice_to_user(facade, user_id, credits, price, lang, payload_suffix=payload_suffix)
            try:
                await call.answer()
            except Exception:
                pass
        except Exception as e:
            logger.error("Error sending invoice: %s", e)

    @router.callback_query(F.data == "cancel_invoice")
    async def handle_cancel_invoice(call: CallbackQuery):
        try:
            await facade.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    @router.pre_checkout_query()
    async def checkout(q: PreCheckoutQuery):
        await q.answer(ok=True)

    @router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
    async def got_payment(message: Message):
        sp = message.successful_payment
        if not sp:
            return
        payload = sp.invoice_payload
        try:
            parts = payload.split("_")
            credits_amount = int(parts[1])
        except (IndexError, ValueError) as e:
            logger.error("Invalid payment payload %r: %s", payload, e)
            return
        user_id = message.chat.id
        group_chat_id = None
        if "_grp_" in payload:
            try:
                idx = payload.index("_grp_") + 5
                group_chat_id = int(payload[idx:])
            except (ValueError, IndexError):
                pass

        if group_chat_id is not None:
            db.update_group_user_credits(user_id, group_chat_id, credits_amount, "purchase")
            new_balance = db.get_group_user_credits(user_id, group_chat_id) + db.get_user_credits(user_id)
            msg = (
                f"✅ <b>Zahlung erfolgreich!</b>\n\n"
                f"+{credits_amount} Credits für die Gruppe gutgeschrieben.\n"
                f"Neuer Stand (Gruppe): <b>{new_balance} Credits</b>"
            )
        else:
            db.update_credits(user_id, credits_amount, "purchase")
            new_balance = db.get_user_credits(user_id)
            msg = (
                f"✅ <b>Zahlung erfolgreich!</b>\n\n"
                f"+{credits_amount} Credits gutgeschrieben.\n"
                f"Neuer Stand: <b>{new_balance} Credits</b>"
            )
        await facade.send_message(user_id, msg, parse_mode="HTML")
