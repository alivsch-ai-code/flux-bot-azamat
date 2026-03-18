"""
gen_handler.py – ORCHESTRATOR für den Generierungs-Flow

ORCHESTRIERT den gesamten Ablauf der KI-Generierung im Telegram-Bot. Bindet die
Sub-Module (handlers/gen/) und externe Dienste (GenerationService, DB) zusammen.
Enthält NUR die register()-Funktion und die Aufrufe der einzelnen Registrierungen –
keine Handler-Implementierungen.

ABLAUF (Orchestrierung):
1. register_nav_handlers: Path-Navigation, Modell-Klick, Chat-Entscheidung, Stop-Chat
2. register_start_gen_handler: Start-Generierung → Context (waiting_for_prompt/media)
3. register_prompt_handlers: Text empfangen → Optimierung (optional) → run_generation
4. register_media_handlers: Foto/Video/Dokument hochgeladen → run_generation oder Prompt-Aufforderung
5. run_generation (aus runner): Credits prüfen, Service aufrufen, parse_and_deliver, Context bereinigen

GENUTZTE MODULE (handlers/gen/):
- nav_handlers: register_nav_handlers
- start_handler: register_start_gen_handler
- runner: create_run_generation
- prompt_handlers: register_prompt_handlers
- media_handlers: register_media_handlers
"""

from telebot import TeleBot

from src.presentation.telegram.handlers.gen.nav_handlers import register_nav_handlers
from src.presentation.telegram.handlers.gen.start_handler import register_start_gen_handler
from src.presentation.telegram.handlers.gen.runner import create_run_generation
from src.presentation.telegram.handlers.gen.prompt_handlers import register_prompt_handlers
from src.presentation.telegram.handlers.gen.media_handlers import register_media_handlers


def register(bot: TeleBot, generation_service, db) -> None:
    """Registriert alle Generierungs- und Navigations-Handler beim Bot-Start."""

    def get_lang(uid):
        return db.get_user_settings(uid)["lang"]

    run_generation = create_run_generation(bot, db, generation_service, get_lang)

    register_nav_handlers(bot, db, get_lang)
    register_start_gen_handler(bot, db, get_lang)
    register_prompt_handlers(bot, db, get_lang, run_generation)
    register_media_handlers(bot, db, get_lang, run_generation)
