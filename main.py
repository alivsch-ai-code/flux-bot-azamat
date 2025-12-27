import os
import telebot
import replicate
import threading
from flask import Flask

# --- KONFIGURATION ---
# Wir holen die Schlüssel sicher aus den Umgebungsvariablen des Servers
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

# Bot und Flask initialisieren
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- DER BOT (LOGIK) ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    prompt = message.text
    chat_id = message.chat.id
    
    print(f"📩 Neuer Auftrag: {prompt}")
    status_msg = bot.reply_to(message, "🎨 Auftrag an Server B (Replicate) gesendet... (ca. 2-5s)")
    bot.send_chat_action(chat_id, 'upload_photo')

    try:
        # 1. API Aufruf an Replicate (FLUX-Schnell)
        # Wir nutzen die offizielle Replicate Python Library
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={"prompt": prompt}
        )
        
        # Output ist eine Liste mit URLs, z.B. ["https://replicate.delivery/..."]
        image_url = output[0]
        
        # 2. Bild an User senden
        bot.send_photo(chat_id, image_url, caption=f"✨ {prompt}")
        bot.delete_message(chat_id, status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Fehler: {str(e)}")
        print(f"Error: {e}")

# --- DER SERVER (DAMIT RENDER ZUFRIEDEN IST) ---
@app.route('/')
def home():
    return "🤖 Bot ist ONLINE und läuft!"

def run_bot():
    bot.infinity_polling()

# --- HAUPTPROGRAMM ---
if __name__ == "__main__":
    # Starte den Bot in einem eigenen Hintergrund-Thread
    t = threading.Thread(target=run_bot)
    t.start()
    
    # Starte den Webserver (wichtig für Render!)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)