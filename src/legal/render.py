from __future__ import annotations

from src.legal.datenschutz import privacy_body
from src.legal.impressum import impressum_body


def render_impressum(lang: str, imprint_ctx: dict[str, str]) -> str:
    """Plaintext Impressum; Platzhalter aus imprint_ctx (bereits sicher formatiert)."""
    lg = (lang or "de").strip() or "de"
    if lg not in ("de", "en", "ru", "kk"):
        lg = "de"
    tpl = impressum_body(lg)
    return tpl.format(**imprint_ctx)


def render_privacy(lang: str, privacy_ctx: dict[str, str] | None = None) -> str:
    """Plaintext Datenschutzerklärung."""
    lg = (lang or "de").strip() or "de"
    if lg not in ("de", "en", "ru", "kk"):
        lg = "de"
    ctx = privacy_ctx or {"service_name": "AZAMAT AI"}
    tpl = privacy_body(lg)
    return tpl.format(**ctx)


def split_telegram_chunks(text: str, max_len: int = 3900) -> list[str]:
    """
    Telegram-Nachrichtenlimit ca. 4096 Zeichen; Puffer für Sonderzeichen.
    Teilt an Absatzgrenzen, sonst hart.
    """
    t = (text or "").strip()
    if not t:
        return []
    if len(t) <= max_len:
        return [t]
    out: list[str] = []
    rest = t
    while rest:
        if len(rest) <= max_len:
            out.append(rest)
            break
        cut = rest.rfind("\n\n", 0, max_len)
        if cut < max_len // 3:
            cut = rest.rfind("\n", 0, max_len)
        if cut < max_len // 3:
            cut = max_len
        chunk = rest[:cut].strip()
        if chunk:
            out.append(chunk)
        rest = rest[cut:].strip()
    return out
