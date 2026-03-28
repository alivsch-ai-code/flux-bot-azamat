"""
Application layer: Use-Cases zwischen Präsentation (Telegram/Web) und Domain/Infrastruktur.

Die `GenerationService`-Implementierung liegt ausschließlich in `services.py`.
Hier nur Re-Export für `from src.application import GenerationService` falls gewünscht.
"""

from src.application.services import GenerationService

__all__ = ["GenerationService"]
