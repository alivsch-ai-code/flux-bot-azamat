"""
chat_history.py – Einfacher In-Memory-Chatverlauf für LLM-Chat

Speichert pro Benutzer die letzten Turns (User/Assistant) und baut daraus
einen Prompt für das LLM. Kein Persistenzlayer – nur für die laufende
Bot-Session.
"""

from typing import Dict, List

_HISTORY: Dict[int, List[Dict[str, str]]] = {}
MAX_TURNS = 5


def build_chat_prompt(user_id: int, new_user_message: str) -> str:
    """
    Baut einen kombinierten Prompt aus den letzten MAX_TURNS Dialog-Turns
    plus der neuen User-Nachricht.
    Format:
        User: ...
        Assistant: ...
        ...
        User: <neue Nachricht>
        Assistant:
    """
    history = _HISTORY.get(user_id, [])
    turns = history[-MAX_TURNS:]
    lines: List[str] = []
    for turn in turns:
        u = (turn.get("user") or "").strip()
        a = (turn.get("assistant") or "").strip()
        if u:
            lines.append(f"User: {u}")
        if a:
            lines.append(f"Assistant: {a}")
    lines.append(f"User: {new_user_message}")
    lines.append("Assistant:")
    return "\n".join(lines)


def append_chat_turn(user_id: int, user_message: str, assistant_message: str) -> None:
    """Fügt einen neuen Dialog-Turn an und begrenzt die Länge."""
    if user_id not in _HISTORY:
        _HISTORY[user_id] = []
    _HISTORY[user_id].append(
        {"user": (user_message or "").strip(), "assistant": (assistant_message or "").strip()}
    )
    if len(_HISTORY[user_id]) > MAX_TURNS:
        _HISTORY[user_id] = _HISTORY[user_id][-MAX_TURNS:]


def clear_history(user_id: int) -> None:
    """Löscht den Verlauf für einen Benutzer (z.B. bei stop_chat)."""
    _HISTORY.pop(user_id, None)

