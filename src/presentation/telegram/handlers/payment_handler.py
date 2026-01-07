from telebot import TeleBot, types
# Wir importieren clear_context, um laufende Vorgänge sauber zu beenden, wenn man den Shop öffnet
from src.presentation.telegram.handlers.common import clear_context 

# Pakete: Label, Titel, Preis in XTR (Stars), Credits
CREDIT_PACKAGES = [
    ("S", "100 Credits", 50, 100),   # 50 Stars ~= 1.00 USD
    ("M", "500 Credits", 200, 500),  # Mengenrabatt
    ("L", "1500 Credits", 500, 1500)
]

def register(bot: TeleBot, db):
    
    # 1. SHOP ÖFFNEN (Reagiert auf Button UND Befehle)
    @bot.message_handler(func=lambda msg: msg.text == "💳 Guthaben / Shop" or msg.text in ['/buy', '/shop'])
    def show_shop(message):
        # WICHTIG: Alten Status löschen, damit der Bot nicht "Abgebrochen" sagt
        clear_context(message.chat.id)
        
        markup = types.InlineKeyboardMarkup()
        for label, desc, price, credits in CREDIT_PACKAGES:
            # Button Text: 💎 100 Credits (50 ⭐️)
            btn_text = f"💎 {desc} ({price} ⭐️)"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{credits}_{price}"))
        
        current_credits = db.get_user_credits(message.chat.id)
        
        text = (
            f"<b>💳 Guthaben aufladen</b>\n"
            f"Dein aktuelles Guthaben: <b>{current_credits} Credits</b>\n\n"
            f"Wähle ein Paket, um sicher via <b>Telegram Stars</b> aufzuladen:"
        )
        
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    # 2. RECHNUNG SENDEN (Wenn User auf einen Preis klickt)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def send_invoice(call):
        try:
            _, credits, price = call.data.split('_')
            
            bot.send_invoice(
                call.message.chat.id,
                title=f"{credits} AI Credits",
                description=f"Aufladung für Bild- und Videogenerierung",
                invoice_payload=f"credits_{credits}",
                provider_token="", # WICHTIG: Leer lassen für Telegram Stars!
                currency="XTR",    # WICHTIG: XTR = Telegram Stars
                prices=[types.LabeledPrice(label="Credits", amount=int(price))], 
                start_parameter="buy_credits"
            )
            # Optional: Feedback, dass geklickt wurde
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Error sending invoice: {e}")

    # 3. PRE-CHECKOUT (Telegram fragt: Ist alles okay?)
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    # 4. ZAHLUNG ERHALTEN (Erfolg!)
    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        payload = message.successful_payment.invoice_payload
        credits_amount = int(payload.split('_')[1])
        user_id = message.chat.id
        
        # Datenbank Update
        db.update_credits(user_id, credits_amount, "purchase")
        new_balance = db.get_user_credits(user_id)
        
        # Erfolgsmeldung an User
        bot.send_message(
            user_id, 
            f"✅ <b>Zahlung erfolgreich!</b>\n\n+{credits_amount} Credits wurden deinem Konto gutgeschrieben.\n\nNeuer Kontostand: <b>{new_balance} Credits</b>", 
            parse_mode="HTML"
        )