import os
from telebot import TeleBot
from src.presentation.telegram import keyboards
from src.utils.strings import get_text
from src.presentation.telegram.handlers.common import get_context, clear_context, set_context

# --- HILFSFUNKTIONEN ---

def get_user_lang(message):
    """Ermittelt die Sprache: de, en, ru, kk."""
    try:
        raw_lang = message.from_user.language_code
        if raw_lang:
            short_lang = raw_lang[:2].lower()
            if short_lang in ["de", "ru", "kk"]: return short_lang
    except Exception: 
        pass
    return "en"

def matches_any_lang(text, key):
    """Prüft, ob der Text einem Button in irgendeiner Sprache entspricht."""
    for lang in ["de", "en", "ru", "kk"]:
        if text == get_text(key, lang):
            return True
    return False

# --- CORE LOGIK: SAUBERES MENÜ ---

def cleanup_context_messages(bot, user_id, ctx):
    """
    Löscht ALLE Nachrichten, die im Context gespeichert sind.
    Das entfernt 'Geister-Nachrichten' wie Beschreibungen oder Bilder.
    """
    if not ctx: return

    # 1. Die Liste der Zusatz-Nachrichten löschen (Bilder, Beschreibungen)
    if "cleanup_ids" in ctx:
        for msg_id in ctx["cleanup_ids"]:
            try:
                bot.delete_message(user_id, msg_id)
            except Exception:
                pass # Nachricht evtl. schon weg, ignorieren

    # 2. Die letzte Haupt-Nachricht löschen (das alte Menü/Prompt-Frage)
    if "last_bot_msg_id" in ctx:
        try:
            bot.delete_message(user_id, ctx["last_bot_msg_id"])
        except Exception:
            pass

def send_menu_and_cleanup(bot, message, text_key, markup_func, model_registry, lang):
    """
    Navigiert zu einem neuen Menü und räumt ALLES Alte auf.
    Versucht erst zu editieren (für Ruhe im Chat), falls das nicht geht -> Löschen & Neu.
    """
    user_id = message.chat.id
    ctx = get_context(user_id)
    
    # 1. User-Input (Klick) löschen -> Hält den Chat sauber
    try:
        bot.delete_message(user_id, message.message_id)
    except Exception:
        pass

    # Vorbereitung: Neues Menü erstellen
    msg_text = get_text(text_key, lang)
    try:
        markup = markup_func(model_registry, lang)
    except TypeError:
        markup = markup_func(lang)

    # 2. SPEZIALFALL: Wenn wir Zusatz-Nachrichten (cleanup_ids) haben (z.B. Beschreibungen),
    # können wir nicht einfach 'editieren', weil die Beschreibungen sonst stehen bleiben.
    # Wir müssen also erst aufräumen und dann das Menü neu senden oder editieren.
    
    # Wir löschen erst die "Bubbles" (Beschreibungen, Bilder)
    if ctx and "cleanup_ids" in ctx:
        for msg_id in ctx["cleanup_ids"]:
            try: bot.delete_message(user_id, msg_id)
            except: pass
        # Liste aus Context entfernen, da erledigt
        del ctx["cleanup_ids"]
        set_context(user_id, ctx)

    # 3. Jetzt versuchen wir, das Hauptmenü zu aktualisieren
    if ctx and "last_bot_msg_id" in ctx:
        try:
            # Versuch: Editieren (Sanft)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=ctx["last_bot_msg_id"],
                text=msg_text,
                reply_markup=markup,
                parse_mode='HTML'
            )
            return # Erfolg!
        except Exception:
            # Fallback: Wenn Editieren fehlschlägt (z.B. Nachricht zu alt), alte löschen
            try: bot.delete_message(user_id, ctx["last_bot_msg_id"])
            except: pass

    # 4. Fallback: Neu senden (wenn kein alter Context da war oder Editieren schiefging)
    new_msg = bot.send_message(user_id, msg_text, reply_markup=markup, parse_mode='HTML')

    # Neuen State speichern
    if not ctx: ctx = {}
    ctx["last_bot_msg_id"] = new_msg.message_id
    set_context(user_id, ctx)


def register(bot: TeleBot, generation_service, model_registry, db): 
    
    # --- START & RESET ---
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        lang = get_user_lang(message)
        db.add_user_if_not_exists(message.chat.id, message.from_user.username)
        
        # WICHTIG: Erst aufräumen, DANN Context löschen!
        # Sonst weiß der Bot nicht mehr, welche Nachrichten er löschen muss.
        old_ctx = get_context(message.chat.id)
        if old_ctx:
            cleanup_context_messages(bot, message.chat.id, old_ctx)
        
        # Jetzt Kontext resetten
        clear_context(message.chat.id)
        
        # Info-Nachricht (Transparenz)
        bot.send_message(message.chat.id, get_text("transparency_msg", lang), parse_mode='HTML')
        
        # Hauptmenü senden
        msg = bot.send_message(
            message.chat.id, 
            get_text("welcome", lang), 
            reply_markup=keyboards.get_persistent_main_menu(model_registry, lang)
        )
        
        # ID merken für späteres Aufräumen
        set_context(message.chat.id, {"last_bot_msg_id": msg.message_id})


    # --- ADMIN CHEAT ---
    @bot.message_handler(commands=['cheat_mode'])
    def admin_give_credits(message):
        lang = get_user_lang(message)
        try:
            ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  
        except ValueError:
            ADMIN_ID = 0
            
        if message.from_user.id != ADMIN_ID: return 
        
        db.update_credits(message.chat.id, 10000, "admin_gift")
        try: bot.delete_message(message.chat.id, message.message_id)
        except: pass
        
        # Bestätigung kurz zeigen (oder direkt löschen?)
        bot.send_message(message.chat.id, get_text("admin_cheat_success", lang))

    # --- ZURÜCK BUTTON ---
    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "btn_back"))
    def handle_back(message):
        lang = get_user_lang(message)
        user_id = message.chat.id
        ctx = get_context(user_id)

        # 1. User Klick löschen
        try: bot.delete_message(user_id, message.message_id)
        except: pass

        # 2. Alles Alte aufräumen (Beschreibungen, Bilder, altes Menü)
        cleanup_context_messages(bot, user_id, ctx)
        
        # 3. Context leeren (da wir im Hauptmenü neu starten)
        clear_context(user_id)

        # 4. Hauptmenü senden
        msg = bot.send_message(
            user_id, 
            get_text("msg_main_menu", lang), 
            reply_markup=keyboards.get_persistent_main_menu(model_registry, lang)
        )
        
        set_context(user_id, {"last_bot_msg_id": msg.message_id})

    # --- SUBMENÜ NAVIGATION ---
    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "menu_image_studio"))
    def nav_image(message):
        send_menu_and_cleanup(bot, message, "msg_select_model", keyboards.get_image_studio_menu, model_registry, get_user_lang(message))

    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "menu_video_studio"))
    def nav_video(message):
        send_menu_and_cleanup(bot, message, "msg_select_model", keyboards.get_video_studio_menu, model_registry, get_user_lang(message))

    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "menu_tools_edit"))
    def nav_edit(message):
        send_menu_and_cleanup(bot, message, "msg_select_tool", keyboards.get_edit_menu, model_registry, get_user_lang(message))