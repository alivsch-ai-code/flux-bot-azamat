import logging

from telebot import TeleBot, types

from src.presentation.telegram.handlers.common import clear_context
from src.utils.strings import get_text

logger = logging.getLogger(__name__)

CREDIT_PACKAGES = [
    ("S", "100 Credits", 50, 100),   
    ("M", "500 Credits", 200, 500),  
    ("L", "1500 Credits", 500, 1500)
]

def get_user_lang(msg) -> str:
    """Holt die Sprachcode aus Message oder User (z. B. call.message oder call.from_user)."""
    try:
        user = msg.from_user if hasattr(msg, "from_user") else msg
        return (user.language_code or "de")[:2]
    except (AttributeError, TypeError):
        return "de"


def show_shop_logic(bot: TeleBot, message, db, lang: str = "de", force_inline: bool = False) -> None:
    """Zeigt den Shop (Credits kaufen). Bei menu_mode=webapp: WebApp-Button – außer force_inline=True (z.B. Gruppen)."""
    from src.config.settings import config

    clear_context(message.chat.id)
    user_id = message.chat.id
    menu_mode = db.get_bot_setting("menu_mode", "commands")

    if not force_inline and menu_mode == "webapp" and config.APP_URL and config.APP_URL.startswith("https://"):
        app_url = config.APP_URL.rstrip("/")
        shop_url = app_url + "/webapp?view=shop"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            get_text("menu_mode_webapp", lang),
            web_app=types.WebAppInfo(url=shop_url)
        ))
        text = get_text("webapp_open_shop", lang)
        try:
            bot.edit_message_text(text, user_id, message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for label, desc, price, credits in CREDIT_PACKAGES:
        btn_text = f"💎 {desc} ({price} ⭐️)"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{credits}_{price}"))

    back_text = get_text("btn_back", lang)
    markup.add(types.InlineKeyboardButton(back_text, callback_data="nav_main"))

    current_credits = db.get_user_credits(user_id)

    text = (
        f"<b>💳 Guthaben aufladen</b>\n\n"
        f"<b>Dein Stand:</b> <code>{current_credits} Credits</code>\n\n"
        f"<i>Wähle ein Paket – sicher via Telegram Stars</i>\n\n"
        f"<b>Pakete:</b>"
    )

    try:
        bot.edit_message_text(
            text, user_id, message.message_id,
            reply_markup=markup, parse_mode="HTML",
        )
    except Exception:
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")


def register(bot: TeleBot, db) -> None:

    @bot.callback_query_handler(func=lambda call: call.data == "cmd_shop")
    def shop_callback(call):
        try:
            show_shop_logic(bot, call.message, db, get_user_lang(call.message))
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.warning("Shop callback failed: %s", e)

    @bot.message_handler(commands=['buy', 'shop'])
    def shop_command(message):
        show_shop_logic(bot, message, db, get_user_lang(message))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def send_invoice(call):
        try:
            _, credits, price = call.data.split('_')
            lang = get_user_lang(call.from_user)
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            pay_text = f"⭐️ {price} XTR bezahlen" if lang == "de" else f"Pay ⭐️ {price} XTR"
            pay_btn = types.InlineKeyboardButton(text=pay_text, pay=True)
            cancel_text = "❌ Abbrechen" if lang == "de" else "❌ Cancel"
            cancel_btn = types.InlineKeyboardButton(text=cancel_text, callback_data="cancel_invoice")
            
            markup.add(pay_btn)
            markup.add(cancel_btn)
            
            bot.send_invoice(
                call.message.chat.id,
                title=f"{credits} AI Credits",
                description=f"Aufladung für Bild- und Videogenerierung",
                invoice_payload=f"credits_{credits}",
                provider_token="", 
                currency="XTR",    
                prices=[types.LabeledPrice(label="Credits", amount=int(price))], 
                start_parameter="buy_credits",
                reply_markup=markup
            )
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
        except Exception as e:
            logger.error("Error sending invoice: %s", e)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_invoice")
    def handle_cancel_invoice(call):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @bot.message_handler(content_types=["successful_payment"])
    def got_payment(message):
        payload = message.successful_payment.invoice_payload
        try:
            credits_amount = int(payload.split("_")[1])
        except (IndexError, ValueError) as e:
            logger.error("Invalid payment payload %r: %s", payload, e)
            return
        user_id = message.chat.id
        
        db.update_credits(user_id, credits_amount, "purchase")
        new_balance = db.get_user_credits(user_id)
        
        bot.send_message(
            user_id,
            f"✅ <b>Zahlung erfolgreich!</b>\n\n+{credits_amount} Credits gutgeschrieben.\nNeuer Stand: <b>{new_balance} Credits</b>",
            parse_mode="HTML",
        )