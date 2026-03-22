"""
chat_sessions.py – Persistente Chat-History für Text-LLMs (eine Zeile pro User+Modell).

Speichert History als JSON-Liste von Nachrichten:
    [{"role": "user"|"assistant"|"system", "content": "...", "user_name": "Max"}]

Erzeugt bei Bedarf eine Zusammenfassung und ersetzt alte Nachrichten durch einen
kompakten System-Eintrag. Privat: alle 5 Nachrichten. Gruppen: Puffer bis 20, dann Summary.
"""

from typing import List, Dict

from src.infrastructure.ai.replicate.prompt_engineer import summarize_conversation_via_llm


def _format_msg_for_display(m: Dict) -> str:
    """Formatiert eine Nachricht für die History-Anzeige (mit Namen bei user)."""
    role = m.get("role")
    content = (m.get("content") or "").strip()
    if not content:
        return ""
    if role == "user":
        prefix = m.get("user_name") or "User"
    elif role == "assistant":
        prefix = "Assistant"
    else:
        prefix = "System"
    return f"{prefix}: {content}"


def build_chat_prompt_from_messages(
    messages: List[Dict], new_user_message: str, system_prompt: str = None, current_user_name: str = None
) -> str:
    """Baut einen Prompt mit [SYSTEM]/[HISTORY]-Block. current_user_name für die aktuelle Nachricht (Gruppen).
    Die letzte User-Nachricht wird explizit angehängt – wenn sie bereits in messages ist (nach append), nicht doppelt einbauen."""
    default_system = "Du bist ein hilfreicher Chatbot. Unten steht der bisherige Dialog (History). Beantworte nur die letzte Nachricht des Users."
    sys_block = (system_prompt or default_system).strip()
    lines = ["[SYSTEM]", sys_block, "\n[HISTORY]"]
    new_msg_stripped = (new_user_message or "").strip()
    msgs_to_show = messages
    if messages and messages[-1].get("role") == "user":
        last_content = (messages[-1].get("content") or "").strip()
        if last_content == new_msg_stripped:
            msgs_to_show = messages[:-1]
    for m in msgs_to_show:
        line = _format_msg_for_display(m)
        if line:
            lines.append(line)
    user_prefix = current_user_name or "User"
    lines.append(f"{user_prefix}: {new_user_message}")
    lines.append("Assistant:")
    return "\n".join(lines)


def append_with_summary_if_needed(
    db, user_id: int, model_key: str, new_message: Dict, max_messages: int = 5, summarize_at: int = None
) -> List[Dict]:
    """
    Hängt eine neue Message an die Session an.
    Wenn len >= summarize_at: fasst die ältesten summarize_at Nachrichten zusammen,
    ersetzt sie durch einen System-Summary-Eintrag.
    max_messages/summarize_at: Standard 5 (privat), für Gruppen 20.
    """
    if summarize_at is None:
        summarize_at = max_messages
    messages = db.get_chat_session(user_id, model_key)
    messages.append(new_message)

    if len(messages) >= summarize_at:
        to_summarize = messages[:summarize_at]
        text_block = "\n".join(_format_msg_for_display(m) for m in to_summarize if _format_msg_for_display(m))
        if text_block:
            try:
                summary = summarize_conversation_via_llm(text_block)
                messages = [{"role": "system", "content": summary}] + messages[summarize_at:]
            except Exception:
                pass

    db.save_chat_session(user_id, model_key, messages)
    return messages

