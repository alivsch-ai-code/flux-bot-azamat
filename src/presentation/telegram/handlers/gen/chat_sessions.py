"""
chat_sessions.py – Persistente Chat-History für Text-LLMs (eine Zeile pro User+Modell).

Speichert History als JSON-Liste von Nachrichten:
    [{"role": "user"|"assistant"|"system", "content": "..."}]

Erzeugt außerdem nach jeder 5. Nachricht eine Zusammenfassung der letzten 5
Nachrichten und ersetzt diese durch einen kompakten System-Eintrag.
"""

from typing import List, Dict

from src.infrastructure.ai.replicate.prompt_engineer import optimize_prompt_via_llm


def build_chat_prompt_from_messages(messages: List[Dict], new_user_message: str, system_prompt: str = None) -> str:
    """Baut einen Prompt mit [SYSTEM]/[HISTORY]-Block aus der History. Optional: system_prompt für Gruppen (AZAMAT)."""
    default_system = "Du bist ein hilfreicher Chatbot. Unten steht der bisherige Dialog (History). Beantworte nur die letzte Nachricht des Users."
    sys_block = (system_prompt or default_system).strip()
    lines = [
        "[SYSTEM]",
        sys_block,
        "\n[HISTORY]",
    ]
    for m in messages:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            prefix = "User"
        elif role == "assistant":
            prefix = "Assistant"
        else:
            prefix = "System"
        lines.append(f"{prefix}: {content}")
    lines.append(f"User: {new_user_message}")
    lines.append("Assistant:")
    return "\n".join(lines)


def append_with_summary_if_needed(db, user_id: int, model_key: str, new_message: Dict) -> List[Dict]:
    """
    Hängt eine neue Message an die Session an.
    Nach jeder 5. Nachricht wird versucht, die letzten 5 zusammenzufassen und
    durch einen System-Summary-Eintrag zu ersetzen.
    """
    messages = db.get_chat_session(user_id, model_key)
    messages.append(new_message)

    if len(messages) >= 5 and len(messages) % 5 == 0:
        last_five = messages[-5:]
        text_block = "\n".join(
            f"{m.get('role','')}: {m.get('content','')}" for m in last_five
        )
        try:
            summary = optimize_prompt_via_llm(
                "Fasse die folgende Unterhaltung knapp zusammen:\n" + text_block
            )
            messages = messages[:-5]
            messages.append({"role": "system", "content": summary})
        except Exception:
            # Im Fehlerfall keine Zusammenfassung – History bleibt unverändert.
            pass

    db.save_chat_session(user_id, model_key, messages)
    return messages

