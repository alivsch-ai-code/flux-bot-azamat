# menu_handler.py
import os
from telebot import TeleBot
from src.presentation.telegram import keyboards
from src.utils.strings import get_text
from src.presentation.telegram.handlers.common import get_context, clear_context, set_context

# --- KONFIGURATION ---
REFERRAL_REWARD = 50 # Wie viele Credits bekommt der Werber?

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
    """
    if not ctx: return

    # 1. Die Liste der Zusatz-Nachrichten löschen (Bilder, Beschreibungen, Share-Menüs)
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
    """
    user_id = message.chat.id
    ctx = get_context(user_id)
    
    # 1. User-Input (Klick) löschen
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

    # 2. Zusatz-Nachrichten löschen (z.B. Share-Buttons vom vorherigen Screen)
    if ctx and "cleanup_ids" in ctx:
        for msg_id in ctx["cleanup_ids"]:
            try: bot.delete_message(user_id, msg_id)
            except: pass
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
            try: bot.delete_message(user_id, ctx["last_bot_msg_id"])
            except: pass

    # 4. Fallback: Neu senden
    new_msg = bot.send_message(user_id, msg_text, reply_markup=markup, parse_mode='HTML')

    # Neuen State speichern
    if not ctx: ctx = {}
    ctx["last_bot_msg_id"] = new_msg.message_id
    set_context(user_id, ctx)


def register(bot: TeleBot, generation_service, model_registry, db): 
    
    # --- START & RESET & REFERRAL CHECK ---
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        lang = get_user_lang(message)
        user_id = message.chat.id
        args = message.text.split()
        
        # 1. Ist der User wirklich neu?
        # WICHTIG: Deine DB-Klasse braucht 'user_exists(user_id)'
        # Wenn 'add_user_if_not_exists' true zurückgibt, wenn neu, kannst du auch das nutzen.
        is_new_user = not db.user_exists(user_id) if hasattr(db, 'user_exists') else True

        # User in DB anlegen
        db.add_user_if_not_exists(user_id, message.from_user.username)
        
        # 2. Referral Logik: Wenn neu UND Argument vorhanden (z.B. /start 12345)
        if is_new_user and len(args) > 1:
            try:
                referrer_id = int(args[1])
                # Check: Man kann sich nicht selbst werben
                if referrer_id != user_id:
                    # Prüfen ob Werber existiert
                    referrer_exists = db.user_exists(referrer_id) if hasattr(db, 'user_exists') else True
                    
                    if referrer_exists:
                        # A. Credits an den Werber
                        db.update_credits(referrer_id, REFERRAL_REWARD, "referral_bonus")
                        
                        # B. Benachrichtigung an den Werber
                        try:
                            # Wir senden auf Englisch oder Fallback DE, da wir Sprache des Werbers hier nicht wissen
                            msg_ref = get_text("ref_success_referrer", "de") 
                            msg_ref_fmt = msg_ref.format(amount=REFERRAL_REWARD)
                            bot.send_message(referrer_id, msg_ref_fmt, parse_mode="HTML")
                        except Exception as e:
                            print(f"Could not notify referrer: {e}")
            except ValueError:
                pass # Argument war keine ID
        
        # --- Standard Start Prozedur (Aufräumen & Hauptmenü) ---
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

        # 2. Alles Alte aufräumen
        cleanup_context_messages(bot, user_id, ctx)
        
        # 3. Context leeren
        clear_context(user_id)

        # 4. Hauptmenü senden
        msg = bot.send_message(
            user_id, 
            get_text("msg_main_menu", lang), 
            reply_markup=keyboards.get_persistent_main_menu(model_registry, lang)
        )
        
        set_context(user_id, {"last_bot_msg_id": msg.message_id})

    # --- NEW: REFERRAL MENU HANDLER ---
    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "btn_free_credits"))
    def show_referral_menu(message):
        lang = get_user_lang(message)
        user_id = message.chat.id
        
        # 1. Haupt-Nachricht auf "Wähle Optionen" oder ähnliches setzen (und alten Content cleanen)
        # Wir nutzen einfach "msg_next_step" oder einen ähnlichen Titel, damit das "Zurück" Menü erscheint
        send_menu_and_cleanup(bot, message, "msg_next_step", keyboards.get_back_menu, model_registry, lang)
        
        # 2. Link generieren
        try:
            bot_username = bot.get_me().username
        except:
            bot_username = "DeinBotName" # Fallback
            
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        
        # 3. Share Text und Buttons vorbereiten
        share_text_raw = get_text("share_text_template", lang).format(ref_link=ref_link)
        menu_text = get_text("share_menu_title", lang).format(amount=REFERRAL_REWARD, ref_link=ref_link)
        
        share_markup = keyboards.get_share_menu(ref_link, share_text_raw, lang)
        
        # 4. Buttons senden (Zusätzlich zum 'Zurück' Menü oben)
        sent_msg = bot.send_message(user_id, menu_text, reply_markup=share_markup, parse_mode="HTML")
        
        # 5. Damit der "Zurück" Button auch DIESE Nachricht löscht:
        ctx = get_context(user_id)
        if ctx:
            if "cleanup_ids" not in ctx: ctx["cleanup_ids"] = []
            ctx["cleanup_ids"].append(sent_msg.message_id)
            set_context(user_id, ctx)

    # --- SUBMENÜ NAVIGATION ---
    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "menu_image_studio"))
    def nav_image(message):
        send_menu_and_cleanup(bot, message, "msg_select_model", keyboards.get_image_studio_menu, model_registry, get_user_lang(message))

    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "menu_image_description"))
    def nav_desc(message):
        send_menu_and_cleanup(bot, message, "msg_select_model", keyboards.get_image_description_menu, model_registry, get_user_lang(message))

    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "menu_video_studio"))
    def nav_video(message):
        send_menu_and_cleanup(bot, message, "msg_select_model", keyboards.get_video_studio_menu, model_registry, get_user_lang(message))

    @bot.message_handler(func=lambda msg: matches_any_lang(msg.text, "menu_tools_edit"))
    def nav_edit(message):
        send_menu_and_cleanup(bot, message, "msg_select_tool", keyboards.get_edit_menu, model_registry, get_user_lang(message))