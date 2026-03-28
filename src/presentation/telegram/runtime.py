"""Laufzeit-Referenz: Event-Loop des Telegram-Pollers (für Thread → asyncio-Brücken)."""

from __future__ import annotations

import asyncio
from typing import Optional

_main_loop: Optional[asyncio.AbstractEventLoop] = None


def set_telegram_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


def get_telegram_loop() -> asyncio.AbstractEventLoop:
    if _main_loop is None:
        raise RuntimeError("Telegram event loop not set")
    return _main_loop


def run_coroutine_sync(coro, *, timeout: float = 600):
    """Führt eine Coroutine auf dem Telegram-Loop aus (z. B. Flask- oder Worker-Thread — nicht vom Event-Loop-Thread)."""
    loop = get_telegram_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result(timeout=timeout)
