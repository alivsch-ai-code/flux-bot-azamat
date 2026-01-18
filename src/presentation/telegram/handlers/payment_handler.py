from telebot import TeleBot, types
from src.presentation.telegram.handlers.common import clear_context 
from src.utils.strings import get_text

# Pakete: Label, Titel, Preis in XTR (Stars), Credits
CREDIT_PACKAGES = [
    ("S", "100 Credits", 50, 100),   # 50 Stars ~= 1.00 USD
    ("M", "500 Credits", 200, 500),  # Mengenrabatt
    ("L", "1500 Credits", 500, 1500)
]

def get_user_lang(message):
    try:
        return message.from_user.language_code[:2]
    except: return "de"

def register(bot: TeleBot, db):
    
    # 1. SHOP ÖFFNEN
    @bot.callback_query_handler(func=lambda call: call.data == "cmd_shop")
    def shop_callback(call):
        try:
            show_shop_logic(bot, call.message, db, get_user_lang(call.message))
            bot.answer_callback_query(call.id)
        except Exception:
            pass

    @bot.message_handler(commands=['buy', 'shop'])
    def shop_command(message):
        show_shop_logic(bot, message, db, get_user_lang(message))

    def show_shop_logic(bot, message, db, lang="de"):
        clear_context(message.chat.id)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for label, desc, price, credits in CREDIT_PACKAGES:
            btn_text = f"💎 {desc} ({price} ⭐️)"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{credits}_{price}"))
        
        # Zurück Button
        back_text = get_text("btn_back", lang)
        markup.add(types.InlineKeyboardButton(back_text, callback_data="nav_main"))
        
        current_credits = db.get_user_credits(message.chat.id)
        
        text = (
            f"<b>💳 Guthaben aufladen</b>\n"
            f"Dein aktuelles Guthaben: <b>{current_credits} Credits</b>\n\n"
            f"Wähle ein Paket, um sicher via <b>Telegram Stars</b> aufzuladen:"
        )
        
        try:
            bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup, parse_mode="HTML")
        except:
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    # 2. RECHNUNG SENDEN (Mit Fix für Pay-Button)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def send_invoice(call):
        try:
            _, credits, price = call.data.split('_')
            lang = get_user_lang(call.from_user)
            
            # --- FIX: Custom Markup muss Pay-Button UND Cancel-Button enthalten ---
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            # 1. Der Pay-Button (MUSS zwingend der erste Button sein!)
            # 'pay=True' sagt Telegram, dass dies der Kauf-Knopf ist.
            pay_text = f"⭐️ {price} XTR bezahlen" if lang == "de" else f"Pay ⭐️ {price} XTR"
            pay_btn = types.InlineKeyboardButton(text=pay_text, pay=True)
            
            # 2. Der Abbrechen-Button
            cancel_text = "❌ Abbrechen" if lang == "de" else "❌ Cancel"
            cancel_btn = types.InlineKeyboardButton(text=cancel_text, callback_data="cancel_invoice")
            
            markup.add(pay_btn)
            markup.add(cancel_btn)
            
            bot.send_invoice(
                call.message.chat.id,
                title=f"{credits} AI Credits",
                description=f"Aufladung für Bild- und Videogenerierung",
                invoice_payload=f"credits_{credits}",
                provider_token="", # Leer für Telegram Stars
                currency="XTR",    
                prices=[types.LabeledPrice(label="Credits", amount=int(price))], 
                start_parameter="buy_credits",
                reply_markup=markup # Hier übergeben wir jetzt das korrekte Menü
            )
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
        except Exception as e:
            print(f"Error sending invoice: {e}")

    # 3. RECHNUNG ABBRECHEN
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_invoice")
    def handle_cancel_invoice(call):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            # Optional: User zurück zum Shop leiten?
            # show_shop_logic(bot, call.message, db, get_user_lang(call.message))
        except:
            pass 

    # 4. ZAHLUNG ERHALTEN
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        payload = message.successful_payment.invoice_payload
        credits_amount = int(payload.split('_')[1])
        user_id = message.chat.id
        
        db.update_credits(user_id, credits_amount, "purchase")
        new_balance = db.get_user_credits(user_id)
        
        # Erfolgsnachricht
        bot.send_message(
            user_id, 
            f"✅ <b>Zahlung erfolgreich!</b>\n\n+{credits_amount} Credits gutgeschrieben.\nNeuer Stand: <b>{new_balance} Credits</b>", 
            parse_mode="HTML"
        )