# handlers/gen/ – Modul für den Generierungs-Flow
# Exportiert die zentralen Funktionen für gen_handler.py (Orchestrator).

from src.presentation.telegram.handlers.gen.ux import smart_update_status
from src.presentation.telegram.handlers.gen.media_helpers import (
    path_to_mediafile,
    ctx_media_to_list,
    schema_requires_media,
    schema_allows_multiple_media,
)
from src.presentation.telegram.handlers.gen.error_checks import (
    is_uri_too_large,
    is_rate_limit,
    is_technical_error,
)
from src.presentation.telegram.handlers.gen.download import download_url_to_bytes
from src.presentation.telegram.handlers.gen.result_delivery import parse_and_deliver
from src.presentation.telegram.handlers.gen.pending import (
    pending_prompts,
    cleanup_pending_prompts,
)

__all__ = [
    "smart_update_status",
    "path_to_mediafile",
    "ctx_media_to_list",
    "schema_requires_media",
    "schema_allows_multiple_media",
    "is_uri_too_large",
    "is_rate_limit",
    "is_technical_error",
    "download_url_to_bytes",
    "parse_and_deliver",
    "pending_prompts",
    "cleanup_pending_prompts",
]
