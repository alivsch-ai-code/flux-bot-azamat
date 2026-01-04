# src/utils/strings.py

STRINGS = {
    # --- NAVIGATION ---
    "welcome": {
        "en": "👋 Welcome to the AI Hub!\nWhat would you like to create?",
        "de": "👋 Willkommen im AI Hub!\nWas möchtest du erstellen?"
    },
    "transparency_msg": {
        "en": (
            "<b>🛡️ We believe in transparency</b>\n\n"
            "There are many scams in the online world today. We want to be open with you: "
            "We use established networks like Replicate to provide you with top-tier AI technology simply and for 'pocket change'.\n\n"
            "💡 <b>An honest note:</b> If you are tech-savvy, you might save money by using providers like Replicate directly.\n\n"
            "For everyone else, we offer the most convenient access right here.\n\n"
            "<b>Have fun with AZAMAT AI!</b> 🚀"
        ),
        "de": (
            "<b>🛡️ Wir setzen auf Transparenz</b>\n\n"
            "In der aktuellen Online-Welt gibt es leider viel Scam. Wir spielen mit offenen Karten: "
            "Wir nutzen etablierte Netzwerke wie Replicate, um euch KI-Technologie einfach und gegen 'Kleingeld' zur Verfügung zu stellen.\n\n"
            "💡 <b>Ein ehrlicher Hinweis:</b> Falls du technisch sehr versiert bist, "
            "kannst du Geld sparen, indem du Anbieter wie Replicate direkt nutzt.\n\n"
            "Für alle anderen bieten wir hier den bequemsten Zugang.\n\n"
            "<b>Viel Spaß mit AZAMAT AI!</b> 🚀"
        )
    },
    "btn_back": {
        "en": "🔙 Back",
        "de": "🔙 Zurück"
    },
    
    # --- MAIN MENU ---
    "menu_image_studio": {
        "en": "🎨 Image Studio",
        "de": "🎨 Bild Studio"
    },
    "menu_video_studio": {
        "en": "🎬 Video Studio",
        "de": "🎬 Video Studio"
    },
    "menu_audio_studio": {
        "en": "🎵 Audio Studio",
        "de": "🎵 Audio Studio"
    },
    "menu_wallet": {
        "en": "💰 Wallet / Profile",
        "de": "💰 Guthaben / Profil"
    },

    # --- SUB MENUS (Image) ---
    "menu_text2image": {
        "en": "📝 Text to Image",
        "de": "📝 Text zu Bild"
    },
    "menu_editimage": {
        "en": "✏️ Edit Image",
        "de": "✏️ Bild bearbeiten"
    },

    # --- PROMPTS & MESSAGES ---
    "prompt_choose_mode": {
        "en": "Choose your mode:",
        "de": "Wähle deinen Modus:"
    },
    "prompt_choose_model": {
        "en": "Choose your model:",
        "de": "Wähle dein Modell:"
    },
    "msg_selected": {
        "en": "✅ Selected: <b>{model}</b>\n💰 Cost: {price}€ / run\n\n✍️ <b>Please write your prompt now:</b>",
        "de": "✅ Auswahl: <b>{model}</b>\n💰 Kosten: {price}€ / Start\n\n✍️ <b>Bitte schreibe jetzt deinen Prompt:</b>"
    },
    "msg_generating": {
        "en": "⏳ Generating with {model}...",
        "de": "⏳ Generiere mit {model}..."
    },
    "err_no_text": {
        "en": "⚠️ Please send text.",
        "de": "⚠️ Bitte sende text."
    },
    "err_aborted": {
        "en": "🛑 Aborted.",
        "de": "🛑 Abgebrochen."
    }
}

def get_text(key, lang="en"):
    """Holt den Text basierend auf Key und Sprache."""
    # Fallback auf Englisch, wenn Key in 'de' fehlt
    return STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("en", key))