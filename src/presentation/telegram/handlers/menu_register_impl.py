"""
Private-Chat-Menü und Admin — aiogram-Router (aus menu_handler ausgelagert).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from aiogram import F
from aiogram.enums import ChatType, ContentType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from src.config.settings import config
from src.legal import (
    build_imprint_placeholders,
    build_privacy_context,
    render_impressum,
    render_privacy,
    split_telegram_chunks,
)
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.chat_debounce import cancel_pending_batch
from src.presentation.telegram.handlers.common import clear_context, get_context, set_context
from src.presentation.telegram.handlers.gen.chat_sessions import append_global_chat_event
from src.presentation.telegram.handlers.group_handler import get_group_menu_markup
from src.presentation.telegram.handlers.gen.nav_handlers import send_model_detail_view
from src.presentation.telegram.handlers.menu_handler import (
    ADMIN_ID,
    REFERRAL_REWARD,
    _is_keyboard_mode,
    _is_webapp_mode,
    _remove_reply_keyboard_silently,
    process_webapp_action,
)
from src.presentation.telegram.handlers.payment_handler import show_shop_logic
from src.presentation.telegram.welcome_utils import send_welcome_with_video
from src.utils.strings import get_text, get_welcome

logger = logging.getLogger(__name__)


def register_menu_handlers(router, facade, generation_service, db, daily_service=None) -> None:
    def get_lang(user_id):
        return db.get_user_settings(user_id)["lang"]

    @router.message(Command("set_menu_mode"), F.chat.type == ChatType.PRIVATE)
    async def admin_set_menu_mode(message: Message):
        user_id = message.chat.id
        if ADMIN_ID and user_id != ADMIN_ID:
            await message.answer(f"⛔ Nur für Admins. Deine ID: {user_id} – prüfe ADMIN_ID in .env")
            return
        lang = get_lang(user_id)
        parts = (message.text or "").strip().split()
        if len(parts) < 2:
            current = db.get_bot_setting("menu_mode", "commands")
            await message.answer(
                f"📋 Aktueller Modus: <b>{current}</b>\n\n"
                "Zum Ändern: /set_menu_mode <code>commands</code> | <code>keyboard</code> | <code>webapp</code>",
                parse_mode="HTML",
            )
            return
        mode = parts[1].lower()
        if mode not in ("commands", "keyboard", "webapp"):
            await message.answer(get_text("admin_menu_mode_invalid", lang))
            return
        db.set_bot_setting("menu_mode", mode)
        hint = ""
        if mode == "keyboard":
            hint = "\n\n👇 Sende /start um die Tastatur zu sehen."
        elif mode == "webapp":
            if config.APP_URL:
                hint = "\n\n✅ Bot neu starten – dann öffnet das 🌐 neben dem Eingabefeld die App."
            else:
                hint = "\n\n⚠️ Keine HTTPS-URL. Lokal: ngrok http 5000, dann APP_URL=https://xxx.ngrok-free.app"
        await message.answer(get_text("admin_menu_mode_set", lang).format(mode=mode) + hint)

    def _should_handle_keyboard_nav(m: Message) -> bool:
        if not _is_keyboard_mode(db) or not m.text:
            return False
        if keyboards.get_keyboard_action_for_text(m.text) is not None:
            return True
        ctx = get_context(m.chat.id)
        path = ctx.get("keyboard_path")
        if path is not None:
            models = db.get_all_models()
            return keyboards.get_path_keyboard_action(m.text, path, models, get_lang(m.chat.id)) is not None
        return False

    @router.message(lambda m: _should_handle_keyboard_nav(m))
    async def handle_keyboard_nav(message: Message):
        user_id = message.chat.id
        lang = get_lang(user_id)
        all_models = db.get_all_models()
        try:
            await facade.delete_message(user_id, message.message_id)
        except Exception:
            pass

        action = keyboards.get_keyboard_action_for_text(message.text)
        if action is None:
            ctx = get_context(user_id)
            path = ctx.get("keyboard_path", "root")
            path_result = keyboards.get_path_keyboard_action(message.text, path, all_models, lang)
            if path_result:
                act_type, target = path_result
                if act_type == "nav_main":
                    clear_context(user_id)
                    db.set_user_chat_mode(user_id, None, active=False)
                    cancel_pending_batch(user_id)
                    un = (message.from_user and message.from_user.first_name) or ""
                    welcome_text = get_welcome(lang, un)
                    markup = keyboards.get_main_reply_keyboard(lang)
                    await send_welcome_with_video(facade, user_id, welcome_text, markup)
                elif act_type == "nav_path":
                    clear_context(user_id)
                    db.set_user_chat_mode(user_id, None, active=False)
                    set_context(user_id, {"keyboard_path": target})
                    path_markup = keyboards.get_path_reply_keyboard(all_models, lang, target)
                    title_key = f"title_{target.replace('/', '_')}"
                    title_text = get_text(title_key, lang)
                    if title_text == title_key:
                        cat_name = target.split("/")[-1].capitalize()
                        display_name = get_text(f"menu_{cat_name.lower()}", lang)
                        title_text = f"📂 <b>{display_name if not display_name.startswith('menu_') else cat_name}</b>"
                    await facade.send_message(user_id, title_text, reply_markup=path_markup, parse_mode="HTML")
                elif act_type == "sel":
                    prev = get_context(user_id) or {}
                    clear_context(user_id)
                    db.set_user_chat_mode(user_id, None, active=False)
                    cancel_pending_batch(user_id)
                    await send_model_detail_view(facade, user_id, target, db, get_lang)
                    set_context(
                        user_id,
                        {
                            "model_key": target,
                            "step": "viewing_model",
                            "keyboard_path": path,
                            "menu_path": path,
                            "media_paths": prev.get("media_paths") or [],
                        },
                    )
            return

        clear_context(user_id)
        db.set_user_chat_mode(user_id, None, active=False)
        cancel_pending_batch(user_id)
        if action == "nav_main":
            un = (message.from_user and message.from_user.first_name) or ""
            welcome_text = get_welcome(lang, un)
            markup = keyboards.get_main_reply_keyboard(lang)
            await send_welcome_with_video(facade, user_id, welcome_text, markup)
        elif action.startswith("nav_path_"):
            target_path = action.replace("nav_path_", "")
            set_context(user_id, {"keyboard_path": target_path})
            path_markup = keyboards.get_path_reply_keyboard(all_models, lang, target_path)
            title_key = f"title_{target_path.replace('/', '_')}"
            title_text = get_text(title_key, lang)
            if title_text == title_key:
                cat_name = target_path.split("/")[-1].capitalize()
                display_name = get_text(f"menu_{cat_name.lower()}", lang)
                title_text = f"📂 <b>{display_name if not display_name.startswith('menu_') else cat_name}</b>"
            await facade.send_message(user_id, title_text, reply_markup=path_markup, parse_mode="HTML")
        elif action == "nav_profile":
            creds = db.get_user_credits(user_id)
            text = get_text("profile_text", lang).format(
                name=message.from_user.first_name,
                creds=creds,
                user_id=user_id,
            )
            markup = keyboards.get_back_menu(lang, target="nav_main")
            await facade.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")
        elif action == "cmd_shop":
            await show_shop_logic(facade, message, db, lang)

    @router.message(Command("reload_models"), F.chat.type == ChatType.PRIVATE)
    async def admin_reload_models(message: Message):
        user_id = message.chat.id
        if ADMIN_ID and user_id != ADMIN_ID:
            return
        try:
            if hasattr(db, "_models_cache"):
                delattr(db, "_models_cache")
            if hasattr(db, "_models_cache_ts"):
                delattr(db, "_models_cache_ts")
            models = db.get_all_models()
            await facade.send_message(
                user_id,
                f"✅ Modelle neu aus Neon geladen. Anzahl: {len(models)}",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.exception("Admin reload_models failed: %s", e)
            await facade.send_message(user_id, f"❌ Fehler beim Neuladen der Modelle: {e}", parse_mode="HTML")

    @router.message(Command("trigger_daily_news"), F.chat.type == ChatType.PRIVATE)
    async def admin_trigger_daily_news(message: Message):
        user_id = message.chat.id
        if ADMIN_ID and user_id != ADMIN_ID:
            return
        if not daily_service:
            await message.answer("❌ DailyService ist nicht verfügbar.")
            return
        try:
            # Dispatch kann Minuten dauern (Replicate + viele Chats); nicht den aiogram-Loop blockieren.
            result = await asyncio.to_thread(daily_service.trigger_ai_news_post)
            if result.get("ok"):
                sent_count = int(result.get("sent_count") or 0)
                total = int(result.get("total_recipients") or 0)
                await message.answer(
                    f"✅ Daily News manuell ausgelöst.\nGesendet an: {sent_count}/{total} Empfänger",
                    parse_mode="HTML",
                )
            else:
                await message.answer(
                    f"⚠️ Trigger ausgeführt, aber nichts gesendet.\nGrund: <code>{result.get('reason','unknown')}</code>",
                    parse_mode="HTML",
                )
        except Exception as e:
            logger.exception("Admin trigger_daily_news failed: %s", e)
            await message.answer(f"❌ Fehler beim Triggern der Daily News: {e}")

    @router.message(Command("track_channel"), F.chat.type == ChatType.PRIVATE)
    async def admin_track_channel(message: Message):
        """
        Registriert einen Telegram-Channel für Daily-News-Broadcast.
        Nutzung: /track_channel -1001234567890 [de|en|ru|kk]
        """
        user_id = message.chat.id
        if ADMIN_ID and user_id != ADMIN_ID:
            return
        parts = (message.text or "").strip().split()
        if len(parts) < 2:
            await message.answer(
                "ℹ️ Nutzung:\n"
                "<code>/track_channel -1001234567890 de</code>\n\n"
                "• chat_id muss negativ sein (Channel/Group-ID)\n"
                "• Sprache optional: de | en | ru | kk",
                parse_mode="HTML",
            )
            return
        try:
            chat_id = int(parts[1].strip())
        except (TypeError, ValueError):
            await message.answer("❌ Ungültige chat_id. Erwartet wird eine numerische ID wie -1001234567890.")
            return
        if chat_id >= 0:
            await message.answer("❌ chat_id muss negativ sein (Telegram Channel/Group-ID).")
            return
        lang = (parts[2].strip().lower() if len(parts) >= 3 else "de")
        if lang not in ("de", "en", "ru", "kk"):
            await message.answer("❌ Ungültige Sprache. Erlaubt: de, en, ru, kk.")
            return
        db.set_group_language(chat_id, lang)
        await message.answer(
            "✅ Channel/Chat für Daily News registriert.\n"
            f"chat_id: <code>{chat_id}</code>\n"
            f"Sprache: <b>{lang}</b>\n\n"
            "Hinweis: Der Bot muss im Channel Admin-Rechte zum Posten haben.",
            parse_mode="HTML",
        )

    @router.message(Command("tracked_channels"), F.chat.type == ChatType.PRIVATE)
    async def admin_tracked_channels(message: Message):
        """Zeigt alle aktuell für Daily News erfassten negativen Chat-IDs."""
        user_id = message.chat.id
        if ADMIN_ID and user_id != ADMIN_ID:
            return
        ids = []
        for cid in db.get_all_tracked_groups():
            try:
                i = int(cid)
            except Exception:
                continue
            if i < 0:
                ids.append(i)
        if not ids:
            await message.answer("ℹ️ Keine negativen Chat-IDs registriert.")
            return
        ids_sorted = sorted(set(ids))
        lines = ["📣 Registrierte Channel/Group IDs für Daily News:"]
        for cid in ids_sorted:
            lines.append(f"• <code>{cid}</code> ({db.get_group_language(cid)})")
        await message.answer("\n".join(lines), parse_mode="HTML")

    def _lang_from_message(message: Message) -> str:
        if message.chat.type == ChatType.PRIVATE:
            return get_lang(message.chat.id)
        db.add_group_if_not_exists(message.chat.id, "en")
        return db.get_group_language(message.chat.id)

    @router.message(
        Command("info", "privacy", "datenschutz"),
        F.chat.type.in_({ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP}),
    )
    async def cmd_privacy_info(message: Message):
        lang_key = _lang_from_message(message)
        text = render_privacy(lang_key, build_privacy_context(config))
        for chunk in split_telegram_chunks(text):
            await message.answer(chunk)

    @router.message(Command("impressum"), F.chat.type.in_({ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP}))
    async def cmd_impressum(message: Message):
        lang_key = _lang_from_message(message)
        im_ctx = build_imprint_placeholders(config, lang_key)
        text = render_impressum(lang_key, im_ctx)
        for chunk in split_telegram_chunks(text):
            await message.answer(chunk)

    @router.message(F.content_type == ContentType.WEB_APP_DATA, F.chat.type == ChatType.PRIVATE)
    async def handle_web_app_data(message: Message):
        if not _is_webapp_mode(db):
            return
        try:
            data = json.loads(message.web_app_data.data)
            action = data.get("action", "")
        except (json.JSONDecodeError, TypeError, AttributeError):
            return
        user_id = message.chat.id
        is_group = str(message.chat.type) in ("group", "supergroup")
        try:
            await facade.delete_message(user_id, message.message_id)
        except Exception:
            pass
        await asyncio.to_thread(
            process_webapp_action,
            facade,
            user_id,
            action,
            db,
            is_group=is_group,
            payload=data,
        )

    @router.message(Command("start"), F.chat.type == ChatType.PRIVATE)
    async def send_welcome(message: Message):
        user_id = message.chat.id
        db.add_user_if_not_exists(user_id, message.from_user.username)
        lang = get_lang(user_id)

        old_ctx = get_context(user_id)
        if old_ctx and "last_bot_msg_id" in old_ctx:
            try:
                await facade.delete_message(user_id, old_ctx["last_bot_msg_id"])
            except Exception:
                pass
        clear_context(user_id)

        args = message.text.split()
        if len(args) > 1 and not db.user_exists(user_id):
            try:
                ref_id = int(args[1])
                if ref_id != user_id:
                    db.update_credits(ref_id, REFERRAL_REWARD, "referral")
                    await facade.send_message(
                        ref_id,
                        get_text("ref_success_referrer", get_lang(ref_id)).format(amount=REFERRAL_REWARD),
                    )
            except (ValueError, IndexError):
                pass
        else:
            no_referral_text = get_text("no_referral", lang)
            await facade.send_message(user_id, no_referral_text, parse_mode="HTML")

        transparency_text = get_text("transparency_msg", lang)
        await facade.send_message(user_id, transparency_text, parse_mode="HTML")

        user_name = (message.from_user and message.from_user.first_name) or ""
        welcome_text = get_welcome(lang, user_name)
        all_models = db.get_all_models()

        if _is_keyboard_mode(db):
            reply_kbd = keyboards.get_main_reply_keyboard(lang)
            await send_welcome_with_video(facade, user_id, welcome_text, reply_kbd)
        elif _is_webapp_mode(db) and config.APP_URL:
            webapp_url = (config.APP_URL or "").rstrip("/")
            if webapp_url.startswith("https://"):
                webapp_url = webapp_url + "/webapp"
                try:
                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=get_text("menu_mode_webapp", lang),
                                    web_app=WebAppInfo(url=webapp_url),
                                )
                            ]
                        ]
                    )
                    await send_welcome_with_video(facade, user_id, welcome_text, markup)
                    await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)
                except Exception as e:
                    logger.warning("WebApp-Button fehlgeschlagen, Fallback zu Inline-Menü: %s", e)
                    markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                    await send_welcome_with_video(facade, user_id, welcome_text, markup)
                    await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)
            else:
                markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                await send_welcome_with_video(facade, user_id, welcome_text, markup)
                await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)
        else:
            markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
            await send_welcome_with_video(facade, user_id, welcome_text, markup)
            await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)

    @router.callback_query(
        lambda c: bool(c.data and c.data.startswith("nav_") and not c.data.startswith("nav_path_"))
    )
    async def handle_navigation(call: CallbackQuery):
        chat_id = call.message.chat.id
        chat_type = str(call.message.chat.type)
        if chat_type in ("group", "supergroup"):
            text, markup = get_group_menu_markup(
                db, chat_id, (call.from_user.first_name or call.from_user.username or "") if call.from_user else ""
            )
            try:
                await facade.edit_message_text(
                    text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                await facade.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            try:
                await call.answer()
            except Exception:
                pass
            return

        user_id = chat_id
        lang = get_lang(user_id)
        try:
            target = call.data.split("_")[1]
        except IndexError:
            return

        new_text = ""
        new_markup = None

        if target == "main":
            user_name = db.get_user_username_or_name(user_id) or ""
            new_text = get_welcome(lang, user_name)
            all_models = db.get_all_models()
            clear_context(user_id)
            if _is_keyboard_mode(db):
                main_kbd = keyboards.get_main_reply_keyboard(lang)
                try:
                    await facade.delete_message(user_id, call.message.message_id)
                except Exception:
                    pass
                await send_welcome_with_video(facade, user_id, new_text, main_kbd)
            elif _is_webapp_mode(db) and config.APP_URL:
                webapp_url = (config.APP_URL or "").rstrip("/")
                if webapp_url.startswith("https://"):
                    webapp_url = webapp_url + "/webapp"
                    try:
                        new_markup = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text=get_text("menu_mode_webapp", lang),
                                        web_app=WebAppInfo(url=webapp_url),
                                    )
                                ]
                            ]
                        )
                        try:
                            await facade.delete_message(user_id, call.message.message_id)
                        except Exception:
                            pass
                        await send_welcome_with_video(facade, user_id, new_text, new_markup)
                        await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)
                    except Exception as e:
                        logger.warning("WebApp-Button (nav_main) fehlgeschlagen, Fallback: %s", e)
                        new_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                        try:
                            await facade.delete_message(user_id, call.message.message_id)
                        except Exception:
                            pass
                        await send_welcome_with_video(facade, user_id, new_text, new_markup)
                        await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)
                else:
                    new_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                    try:
                        await facade.delete_message(user_id, call.message.message_id)
                    except Exception:
                        pass
                    await send_welcome_with_video(facade, user_id, new_text, new_markup)
                    await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)
            else:
                new_markup = keyboards.get_dynamic_model_menu(all_models, lang, current_path="root")
                try:
                    await facade.delete_message(user_id, call.message.message_id)
                except Exception:
                    pass
                await send_welcome_with_video(facade, user_id, new_text, new_markup)
                await asyncio.to_thread(_remove_reply_keyboard_silently, facade, user_id)
            try:
                await call.answer()
            except Exception:
                pass
            return

        elif target == "settings":
            if _is_webapp_mode(db) and config.APP_URL and config.APP_URL.startswith("https://"):
                webapp_url = (config.APP_URL or "").rstrip("/") + "/webapp?view=settings"
                new_text = get_text("webapp_open_settings", lang)
                new_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=get_text("menu_mode_webapp", lang),
                                web_app=WebAppInfo(url=webapp_url),
                            )
                        ]
                    ]
                )
            else:
                settings = db.get_user_settings(user_id)
                new_text = get_text("settings_title", lang)
                new_markup = keyboards.get_settings_menu(settings, lang)

        elif target == "lang":
            new_text = "🌐 <b>Select Language / Sprache wählen:</b>"
            new_markup = keyboards.get_language_menu(lang)

        elif target == "profile":
            if _is_webapp_mode(db) and config.APP_URL and config.APP_URL.startswith("https://"):
                webapp_url = (config.APP_URL or "").rstrip("/") + "/webapp?view=profile"
                new_text = get_text("webapp_open_profile", lang)
                new_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=get_text("menu_mode_webapp", lang),
                                web_app=WebAppInfo(url=webapp_url),
                            )
                        ]
                    ]
                )
            else:
                creds = db.get_user_credits(user_id)
                new_text = get_text("profile_text", lang).format(
                    name=call.from_user.first_name,
                    creds=creds,
                    user_id=user_id,
                )
                new_markup = keyboards.get_back_menu(lang, target="nav_main")

        elif target == "referral":
            if _is_webapp_mode(db) and config.APP_URL and config.APP_URL.startswith("https://"):
                webapp_url = (config.APP_URL or "").rstrip("/") + "/webapp?view=profile"
                new_text = get_text("webapp_open_profile", lang)
                new_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=get_text("menu_mode_webapp", lang),
                                web_app=WebAppInfo(url=webapp_url),
                            )
                        ]
                    ]
                )
            else:
                me = await facade.get_me()
                bot_name = me.username or ""
                link = f"https://t.me/{bot_name}?start={user_id}"
                new_text = get_text("share_menu_title", lang).format(ref_link=link)
                share_text = get_text("share_text_template", lang).format(ref_link=link)
                new_markup = keyboards.get_share_menu(link, share_text, lang)

        elif target == "support":
            new_text = get_text("support_text", lang)
            new_markup = keyboards.get_back_menu(lang, target="nav_main")

        if new_text and new_markup:
            try:
                await facade.edit_message_text(
                    new_text,
                    user_id,
                    call.message.message_id,
                    reply_markup=new_markup,
                    parse_mode="HTML",
                )
            except Exception:
                await facade.send_message(user_id, new_text, reply_markup=new_markup, parse_mode="HTML")

        try:
            await call.answer()
        except Exception:
            pass

    @router.callback_query(F.data == "toggle_opt")
    async def handle_toggle_opt(call: CallbackQuery):
        user_id = call.message.chat.id
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings["auto_opt"] else 1
        db.update_setting(user_id, "auto_opt", new_val)
        new_settings = db.get_user_settings(user_id)
        lang = new_settings["lang"]
        await facade.edit_message_reply_markup(
            user_id,
            call.message.message_id,
            reply_markup=keyboards.get_settings_menu(new_settings, lang),
        )
        try:
            await call.answer()
        except Exception:
            pass

    @router.callback_query(F.data == "toggle_daily")
    async def handle_toggle_daily(call: CallbackQuery):
        user_id = call.message.chat.id
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings["daily_msg"] else 1
        db.update_setting(user_id, "daily_msg", new_val)
        new_settings = db.get_user_settings(user_id)
        lang = new_settings["lang"]
        await facade.edit_message_reply_markup(
            user_id,
            call.message.message_id,
            reply_markup=keyboards.get_settings_menu(new_settings, lang),
        )
        status_key = "daily_news_on" if new_val else "daily_news_off"
        try:
            await call.answer(get_text(status_key, lang))
        except Exception:
            pass

    @router.callback_query(F.data == "toggle_neg")
    async def handle_toggle_neg(call: CallbackQuery):
        user_id = call.message.chat.id
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings.get("auto_negative_prompt", True) else 1
        db.update_setting(user_id, "auto_negative_prompt", new_val)
        new_settings = db.get_user_settings(user_id)
        lang = new_settings["lang"]
        await facade.edit_message_reply_markup(
            user_id,
            call.message.message_id,
            reply_markup=keyboards.get_settings_menu(new_settings, lang),
        )
        try:
            await call.answer()
        except Exception:
            pass

    @router.callback_query(F.data == "clear_history")
    async def handle_clear_history(call: CallbackQuery):
        user_id = call.message.chat.id
        settings = db.get_user_settings(user_id)
        lang = settings["lang"]
        try:
            db.clear_chat_session(user_id)
            append_global_chat_event(db, user_id, "system", "User cleared chat history.")
            await call.answer(get_text("history_cleared", lang))
        except Exception:
            await call.answer()

    @router.callback_query(F.data.startswith("set_lang_"))
    async def handle_set_lang(call: CallbackQuery):
        user_id = call.message.chat.id
        new_lang = call.data.split("_")[2]
        db.update_setting(user_id, "language", new_lang)
        settings = db.get_user_settings(user_id)
        try:
            await call.answer(get_text("lang_selected", new_lang))
        except Exception:
            pass
        await facade.edit_message_text(
            get_text("settings_title", new_lang),
            user_id,
            call.message.message_id,
            reply_markup=keyboards.get_settings_menu(settings, new_lang),
            parse_mode="HTML",
        )

    @router.message(Command("cheat_mode"), F.chat.type == ChatType.PRIVATE)
    async def cheat(m: Message):
        try:
            admin_id = int(os.getenv("ADMIN_ID", "0"))
        except (ValueError, TypeError):
            admin_id = 0
        if m.from_user.id == admin_id:
            db.update_credits(m.chat.id, 10000)
            lang = get_lang(m.chat.id)
            await m.answer(get_text("admin_cheat_success", lang))
