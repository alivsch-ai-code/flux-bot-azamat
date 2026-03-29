"""Befüllt Impressum-Platzhalter aus Konfiguration (Umgebungsvariablen)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings


_LABELS = {
    "de": {
        "phone": "Telefon",
        "reg": "Registereintrag",
        "vat": "USt-IdNr.",
        "resp": "Verantwortlich für den Inhalt (V.i.S.d.P.)",
    },
    "en": {
        "phone": "Phone",
        "reg": "Register entry",
        "vat": "VAT ID",
        "resp": "Responsible for content (editorial)",
    },
    "ru": {
        "phone": "Телефон",
        "reg": "Регистрационная запись",
        "vat": "Идентификатор НДС",
        "resp": "Ответственный за содержание",
    },
    "kk": {
        "phone": "Телефон",
        "reg": "Тіркеу жазбасы",
        "vat": "ҚҚС идентификаторы",
        "resp": "Мазмұны үшін жауапты",
    },
}


def build_imprint_placeholders(config: "Settings", lang: str) -> dict[str, str]:
    lg = (lang or "de").strip() or "de"
    if lg not in _LABELS:
        lg = "de"
    lb = _LABELS[lg]

    legal_name = (getattr(config, "IMPRINT_LEGAL_NAME", None) or "").strip() or "AZAMAT AI"
    address = (getattr(config, "IMPRINT_ADDRESS", None) or "").strip()
    if not address:
        address = {
            "de": "(Angabe der postalischen Anschrift in der Konfiguration: IMPRINT_ADDRESS)",
            "en": "(Postal address to be set in configuration: IMPRINT_ADDRESS)",
            "ru": "(Почтовый адрес указывается в конфигурации: IMPRINT_ADDRESS)",
            "kk": "(Пошталық мекенжай конфигурацияда орнатылады: IMPRINT_ADDRESS)",
        }.get(lg, "(IMPRINT_ADDRESS)")

    email = (getattr(config, "IMPRINT_EMAIL", None) or "").strip()
    if not email:
        email = {
            "de": "(E-Mail in der Konfiguration: IMPRINT_EMAIL)",
            "en": "(Email in configuration: IMPRINT_EMAIL)",
            "ru": "(Электронная почта в конфигурации: IMPRINT_EMAIL)",
            "kk": "(Электрондық пошта конфигурацияда: IMPRINT_EMAIL)",
        }.get(lg, "(IMPRINT_EMAIL)")

    phone = (getattr(config, "IMPRINT_PHONE", None) or "").strip()
    phone_block = f"{lb['phone']}: {phone}\n" if phone else ""

    resp = (getattr(config, "IMPRINT_RESPONSIBLE", None) or "").strip()
    responsible_block = f"{lb['resp']}: {resp}\n" if resp else ""

    reg = (getattr(config, "IMPRINT_REG", None) or "").strip()
    reg_block = f"{lb['reg']}: {reg}\n" if reg else ""

    vat = (getattr(config, "IMPRINT_VAT", None) or "").strip()
    vat_block = f"{lb['vat']}: {vat}\n" if vat else ""

    return {
        "legal_name": legal_name,
        "address": address,
        "email": email,
        "phone_block": phone_block,
        "responsible_block": responsible_block,
        "reg_block": reg_block,
        "vat_block": vat_block,
    }


def build_privacy_context(config: "Settings") -> dict[str, str]:
    name = (getattr(config, "LEGAL_SERVICE_NAME", None) or "").strip() or "AZAMAT AI"
    return {"service_name": name}
