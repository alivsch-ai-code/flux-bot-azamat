# Archiv (nicht Teil der Bot-App)

Hier liegen Module, die **nicht** von `main.py` oder den Telegram-Handlern geladen werden, aber als Referenz oder für spätere Reaktivierung erhalten bleiben.

## `python_unused_providers/`

Früher unter `src/infrastructure/ai/` bzw. `replicate/clients.py`:

- **`kling_client.py`** – eigenständiger `AIProvider` für Kling; die laufende App nutzt stattdessen `UnifiedAIClient._run_kling` (Platzhalter) bzw. Replicate-Modelle.
- **`sonauto_client.py`** – Sonauto-Integration, nirgends importiert.
- **`openai_compatible_client.py`** – generischer OpenAI-kompatibler Client; Grok/OpenAI-Pfade laufen über Methoden in `UnifiedAIClient`.
- **`replicate_client_legacy.py`** – ältere `ReplicateClient`-Klasse; aktiv ist die Replicate-Logik in `unified_client.py`.

**Wieder aktivieren:** Dateien an die passenden Pfade unter `src/infrastructure/ai/` zurückkopieren und in `UnifiedAIClient` oder `GenerationService` verdrahten.

## `legacy_tools/`

Admin-/Staging-Skripte (DB-Init, Replicate-Import, Streamlit-GUIs). Aufruf aus dem Repo-Root:

```bash
python -m archive.legacy_tools.init
python -m archive.legacy_tools.fetch_advanced
```

Voraussetzungen: `DATABASE_URL`, ggf. `replicate`, `streamlit`, `psycopg2` (wie früher bei `src.tools`).

**Wieder als `src.tools`:** Ordnerinhalt nach `src/tools/` kopieren und Imports von `archive.legacy_tools` zurück auf `src.tools` stellen.
