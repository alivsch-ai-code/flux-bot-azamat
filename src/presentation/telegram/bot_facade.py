"""
Einheitliche Telegram-Zugriffsschicht auf aiogram 3.x.

- Async-Methoden (`send_message`, …) für Handler: `await facade.send_message(...)`.
- Sync-Varianten (`*_sync`) für Flask, DailyService und threading.Timer über `run_coroutine_threadsafe`.
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Any, BinaryIO, List, Optional, Union

from aiogram import Bot
from aiogram.enums import ChatAction, ParseMode
from aiogram.types import (
    BufferedInputFile,
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    LabeledPrice,
    MenuButtonCommands,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

logger = logging.getLogger(__name__)


def _parse_mode(pm: Optional[str]) -> Optional[str]:
    if pm is None:
        return None
    if isinstance(pm, str) and pm.upper() == "HTML":
        return ParseMode.HTML
    return pm


def _to_input_file(photo: Any, filename: str = "file.bin") -> Union[str, BufferedInputFile, FSInputFile]:
    if isinstance(photo, (BufferedInputFile, FSInputFile)):
        return photo
    if isinstance(photo, str):
        return photo
    if hasattr(photo, "read"):
        data = photo.read()
        if hasattr(photo, "seek"):
            try:
                photo.seek(0)
            except Exception:
                pass
        return BufferedInputFile(data, filename=filename)
    raise TypeError(f"Unsupported photo/media type: {type(photo)}")


class TelegramBotFacade:
    __slots__ = ("_bot", "_loop")

    def __init__(self, bot: Bot, loop: asyncio.AbstractEventLoop) -> None:
        self._bot = bot
        self._loop = loop

    @property
    def raw(self) -> Bot:
        return self._bot

    def _sync(self, coro, *, timeout: float = 180):
        """
        Nur aus Nicht-Event-Loop-Threads aufrufen (Waitress, DailyService, asyncio.to_thread).
        Nie aus einem aiogram-``async def``-Handler direkt — sonst Deadlock (Loop blockiert auf result()).
        """
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=timeout)

    # --- Sync API (Flask / DailyService / Timer-Threads) ---

    def send_message_sync(self, chat_id: int, text: str, **kwargs) -> Message:
        return self._sync(self.send_message(chat_id, text, **kwargs))

    def send_photo_sync(self, chat_id: int, photo, **kwargs) -> Message:
        return self._sync(self.send_photo(chat_id, photo, **kwargs))

    def send_video_sync(self, chat_id: int, video, **kwargs) -> Message:
        return self._sync(self.send_video(chat_id, video, **kwargs))

    def send_audio_sync(self, chat_id: int, audio, **kwargs) -> Message:
        return self._sync(self.send_audio(chat_id, audio, **kwargs))

    def send_document_sync(self, chat_id: int, document, **kwargs) -> Message:
        return self._sync(self.send_document(chat_id, document, **kwargs))

    def send_media_group_sync(self, chat_id: int, media: list, **kwargs) -> list:
        return self._sync(self.send_media_group(chat_id, media, **kwargs))

    def edit_message_text_sync(self, text: str, chat_id: int, message_id: int, **kwargs) -> Union[Message, bool]:
        return self._sync(self.edit_message_text(text, chat_id, message_id, **kwargs))

    def edit_message_reply_markup_sync(self, chat_id: int, message_id: int, **kwargs) -> Union[Message, bool]:
        return self._sync(self.edit_message_reply_markup(chat_id, message_id, **kwargs))

    def delete_message_sync(self, chat_id: int, message_id: int) -> bool:
        return self._sync(self.delete_message(chat_id, message_id))

    def send_chat_action_sync(self, chat_id: int, action: str) -> bool:
        return self._sync(self.send_chat_action(chat_id, action))

    def get_me_sync(self):
        return self._sync(self.get_me())

    def send_invoice_sync(self, chat_id: int, **kwargs) -> Message:
        return self._sync(self.send_invoice(chat_id, **kwargs))

    def download_file_bytes_sync(self, file_id: str) -> bytes:
        return self._sync(self.download_file_bytes(file_id))

    # --- Async API (Polling-Handler) ---

    async def get_me(self):
        return await self._bot.get_me()

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup=None,
        parse_mode=None,
        disable_web_page_preview: Optional[bool] = None,
        **kwargs,
    ) -> Message:
        pm = _parse_mode(parse_mode)
        return await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=pm,
            disable_web_page_preview=disable_web_page_preview,
            **kwargs,
        )

    async def reply_to(self, message: Message, text: str, **kwargs) -> Message:
        pm = _parse_mode(kwargs.pop("parse_mode", None))
        return await message.answer(text, parse_mode=pm, **kwargs)

    async def edit_message_text(
        self,
        text: str,
        chat_id: int,
        message_id: int,
        reply_markup=None,
        parse_mode=None,
        disable_web_page_preview: Optional[bool] = None,
        **kwargs,
    ) -> Union[Message, bool]:
        pm = _parse_mode(parse_mode)
        return await self._bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=pm,
            disable_web_page_preview=disable_web_page_preview,
            **kwargs,
        )

    async def edit_message_reply_markup(
        self,
        chat_id: int,
        message_id: int,
        reply_markup=None,
        **kwargs,
    ) -> Union[Message, bool]:
        return await self._bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        return await self._bot.delete_message(chat_id=chat_id, message_id=message_id)

    async def send_chat_action(self, chat_id: int, action: str) -> bool:
        try:
            act = ChatAction(action) if isinstance(action, str) else action
        except ValueError:
            act = ChatAction.TYPING
        return await self._bot.send_chat_action(chat_id=chat_id, action=act)

    async def send_photo(
        self,
        chat_id: int,
        photo,
        caption: Optional[str] = None,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ) -> Message:
        pm = _parse_mode(parse_mode)
        media = _to_input_file(photo, "photo.jpg")
        return await self._bot.send_photo(
            chat_id=chat_id,
            photo=media,
            caption=caption,
            parse_mode=pm,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def send_video(
        self,
        chat_id: int,
        video,
        caption: Optional[str] = None,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ) -> Message:
        pm = _parse_mode(parse_mode)
        media = _to_input_file(video, "video.mp4")
        return await self._bot.send_video(
            chat_id=chat_id,
            video=media,
            caption=caption,
            parse_mode=pm,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def send_audio(
        self,
        chat_id: int,
        audio,
        caption: Optional[str] = None,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ) -> Message:
        pm = _parse_mode(parse_mode)
        media = _to_input_file(audio, "audio.mp3")
        return await self._bot.send_audio(
            chat_id=chat_id,
            audio=media,
            caption=caption,
            parse_mode=pm,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def send_document(
        self,
        chat_id: int,
        document,
        caption: Optional[str] = None,
        parse_mode=None,
        reply_markup=None,
        **kwargs,
    ) -> Message:
        pm = _parse_mode(parse_mode)
        media = _to_input_file(document, "file.bin")
        return await self._bot.send_document(
            chat_id=chat_id,
            document=media,
            caption=caption,
            parse_mode=pm,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def send_media_group(self, chat_id: int, media: List, **kwargs) -> list:
        return await self._bot.send_media_group(chat_id=chat_id, media=media, **kwargs)

    async def send_invoice(
        self,
        chat_id: int,
        *,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        currency: str,
        prices: list,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs,
    ) -> Message:
        # telebot: LabeledPrice(label, amount) — gleiche Struktur wie aiogram
        lp: List[LabeledPrice] = []
        for p in prices or []:
            if isinstance(p, LabeledPrice):
                lp.append(p)
            else:
                lp.append(LabeledPrice(label=getattr(p, "label", ""), amount=int(getattr(p, "amount", 0))))
        return await self._bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=lp,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def set_my_commands(self, commands) -> bool:
        return await self._bot.set_my_commands(commands)

    async def set_chat_menu_button(self, menu_button=None, chat_id: Optional[int] = None) -> bool:
        return await self._bot.set_chat_menu_button(chat_id=chat_id, menu_button=menu_button)

    async def delete_webhook(self, drop_pending_updates: bool = False) -> bool:
        return await self._bot.delete_webhook(drop_pending_updates=drop_pending_updates)

    async def download_file_bytes(self, file_id: str) -> bytes:
        buf = io.BytesIO()
        await self._bot.download(file=file_id, destination=buf)
        return buf.getvalue()

    @staticmethod
    def build_menu_button_webapp(text: str, url: str) -> MenuButtonWebApp:
        return MenuButtonWebApp(text=text, web_app=WebAppInfo(url=url))

    @staticmethod
    def build_menu_button_commands() -> MenuButtonCommands:
        return MenuButtonCommands()

    @staticmethod
    def input_media_photo(url: str, caption: Optional[str] = None) -> InputMediaPhoto:
        return InputMediaPhoto(media=url, caption=caption)


# --- Kompatibilität: LabeledPrice wie telebot.types ---
def labeled_price(label: str, amount: int) -> LabeledPrice:
    return LabeledPrice(label=label, amount=amount)
