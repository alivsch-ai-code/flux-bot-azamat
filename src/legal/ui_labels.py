"""Kurz-Labels für die WebApp (nicht der eigentliche Rechtstext)."""

from __future__ import annotations

WEBAPP_LEGAL_LABELS: dict[str, dict[str, str]] = {
    "de": {
        "section_title": "Rechtliches",
        "open_privacy": "Datenschutz",
        "open_impressum": "Impressum",
        "back": "Zurück zu Einstellungen",
        "doc_privacy_title": "Datenschutzerklärung",
        "doc_impressum_title": "Impressum",
    },
    "en": {
        "section_title": "Legal",
        "open_privacy": "Privacy policy",
        "open_impressum": "Legal notice (Impressum)",
        "back": "Back to settings",
        "doc_privacy_title": "Privacy policy",
        "doc_impressum_title": "Legal notice",
    },
    "ru": {
        "section_title": "Правовая информация",
        "open_privacy": "Политика конфиденциальности",
        "open_impressum": "Правовые сведения (Impressum)",
        "back": "Назад к настройкам",
        "doc_privacy_title": "Политика конфиденциальности",
        "doc_impressum_title": "Правовые сведения",
    },
    "kk": {
        "section_title": "Құқықтық ақпарат",
        "open_privacy": "Құпиялылық саясаты",
        "open_impressum": "Заңды мәліметтер (Impressum)",
        "back": "Баптауларға оралу",
        "doc_privacy_title": "Құпиялылық саясаты",
        "doc_impressum_title": "Заңды мәліметтер",
    },
}


def webapp_legal_labels(lang: str) -> dict[str, str]:
    lg = (lang or "de").strip() or "de"
    if lg not in WEBAPP_LEGAL_LABELS:
        lg = "de"
    return dict(WEBAPP_LEGAL_LABELS[lg])
