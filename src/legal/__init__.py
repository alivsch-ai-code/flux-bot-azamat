"""
Rechtstexte (Impressum, Datenschutz) — getrennt von strings.py.

Export für Bot, Flask-API und Tests.
"""

from __future__ import annotations

from src.legal.imprint_fields import build_imprint_placeholders, build_privacy_context
from src.legal.render import render_impressum, render_privacy, split_telegram_chunks
from src.legal.ui_labels import webapp_legal_labels

__all__ = [
    "build_imprint_placeholders",
    "build_privacy_context",
    "render_impressum",
    "render_privacy",
    "split_telegram_chunks",
    "webapp_legal_labels",
]
