"""
gen_handler.py – ORCHESTRATOR für den Generierungs-Flow (aiogram).
"""

from aiogram import Router

from src.presentation.telegram.handlers.gen.media_handlers import register_media_handlers
from src.presentation.telegram.handlers.gen.nav_handlers import register_nav_handlers
from src.presentation.telegram.handlers.gen.prompt_handlers import register_prompt_handlers
from src.presentation.telegram.handlers.gen.runner import create_run_generation
from src.presentation.telegram.handlers.gen.start_handler import register_start_gen_handler
from src.presentation.telegram.handlers.menu_handler import set_webapp_run_generation


def register(router: Router, facade, generation_service, db) -> None:
    def get_lang(uid):
        return db.get_user_settings(uid)["lang"]

    run_generation = create_run_generation(facade, db, generation_service, get_lang)
    set_webapp_run_generation(run_generation)

    register_nav_handlers(router, facade, db, get_lang)
    register_start_gen_handler(router, facade, db, get_lang)
    register_prompt_handlers(router, facade, db, get_lang, run_generation)
    register_media_handlers(router, facade, db, get_lang, run_generation)
