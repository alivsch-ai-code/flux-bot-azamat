"""
Bündelt eingehende Chat-Texte mit adaptivem Debounce.

Nach der 1. Nachricht: 20 s warten, nach der 2.: 10 s, nach der 3.: 5 s, nach der 4.: 10 s.
Ab der 5. Nachricht im gleichen Burst wird sofort eine Antwort erzeugt, die alle
gesammelten Nachrichten berücksichtigt.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Index 0 = erste Nachricht im Burst, …, Index 3 = vierte (fünfte löst sofort-Flush aus)
DEBOUNCE_SECONDS: Tuple[int, ...] = (20, 10, 5, 10)

# Ein Eintrag: (Telegram-User-ID, Anzeigename, Text)
BatchItem = Tuple[int, str, str]
OnFlush = Callable[[int, List[BatchItem]], None]

_states: Dict[int, "_BurstState"] = {}
_states_lock = threading.Lock()


class _BurstState:
    __slots__ = ("lock", "pending", "timer")

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.pending: List[BatchItem] = []
        self.timer: Optional[threading.Timer] = None


def _get_state(chat_id: int) -> _BurstState:
    with _states_lock:
        st = _states.get(chat_id)
        if st is None:
            st = _BurstState()
            _states[chat_id] = st
        return st


def _cancel_timer(st: _BurstState) -> None:
    if st.timer is not None:
        st.timer.cancel()
        st.timer = None


def debounce_delay_seconds_for_count(count_after_append: int) -> Optional[int]:
    """
    Liefert die Wartezeit in Sekunden nach count_after_append Nachrichten im Puffer.
    None = sofort flushen (≥ 5 Nachrichten).
    """
    if count_after_append >= 5:
        return None
    if count_after_append < 1:
        return DEBOUNCE_SECONDS[0]
    idx = min(count_after_append, len(DEBOUNCE_SECONDS)) - 1
    return DEBOUNCE_SECONDS[idx]


def cancel_pending_batch(chat_id: int) -> None:
    """Bricht Timer und verwirft noch nicht verarbeitete Nachrichten (z. B. Chat beenden)."""
    st = _states.get(chat_id)
    if st is None:
        return
    with st.lock:
        _cancel_timer(st)
        st.pending.clear()


def schedule_batched_text_message(chat_id: int, item: BatchItem, on_flush: OnFlush) -> None:
    """
    Hängt eine Nachricht an den Burst an und startet/stellt den Timer um.
    Bei ≥ 5 Nachrichten wird on_flush synchron aufgerufen.
    """
    st = _get_state(chat_id)
    batch_to_flush: Optional[List[BatchItem]] = None

    with st.lock:
        _cancel_timer(st)
        st.pending.append(item)
        n = len(st.pending)
        delay = debounce_delay_seconds_for_count(n)

        if delay is None:
            batch_to_flush = st.pending[:]
            st.pending.clear()
        else:

            def fire() -> None:
                inner = _get_state(chat_id)
                try:
                    with inner.lock:
                        if not inner.pending:
                            return
                        b = inner.pending[:]
                        inner.pending.clear()
                        _cancel_timer(inner)
                    on_flush(chat_id, b)
                except Exception:
                    logger.exception("chat_debounce flush failed chat_id=%s", chat_id)

            t = threading.Timer(delay, fire)
            t.daemon = True
            st.timer = t
            t.start()

    if batch_to_flush is not None:
        try:
            on_flush(chat_id, batch_to_flush)
        except Exception:
            logger.exception("chat_debounce immediate flush failed chat_id=%s", chat_id)
