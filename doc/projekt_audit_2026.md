# Projekt-Audit AZAMAT AI Hub (flux-bot-azamat) – März 2026

Vollständiger Durchgang: Einstieg, Bot, Replicate, Mini-App-UI, Infrastruktur, Tools.  
**Behoben in diesem Lauf** siehe Abschnitt 8; **offen / mittelfristig** Abschnitt 9.

---

## 1. Repository-Struktur (Überblick)

| Bereich | Pfade |
|--------|--------|
| Einstieg | `main.py` – Flask + Waitress, Telegram-Polling, Health, Web-API |
| Konfiguration | `src/config/settings.py` |
| Domain | `src/domain/entities.py`, `interfaces.py` |
| Application | `src/application/services.py`, `daily_services.py` |
| Infrastruktur | `src/infrastructure/database.py`, `metrics.py`, `ai/*`, `security/` |
| Telegram | `src/presentation/telegram/bot.py`, `keyboards.py`, `handlers/*` |
| Gen-Flow | `handlers/gen_handler.py` → `handlers/gen/*` |
| Mini App | `webapp/index.html` |
| Tools (lokal/Admin) | `src/tools/*` |
| Doku | `doc/*` |

---

## 2. Laufzeit & Bot (`main.py`, `bot.py`)

**Funktionsweise:** Ein Prozess: Hauptthread `infinity_polling`, Daemon-Thread Waitress (8 Threads), optional Status-Log-Thread.

**Stärken:** Health-Check `/`, WebApp-Route, `validate_init_data` für API-Aktionen, Retry bei Polling-Timeout.

**Risiken (bekannt, siehe `skalierbarkeit_render.md`):**
- Nur **eine** Bot-Instanz pro Token (409 bei Duplikat).
- DB: globaler Lock serialisiert alle Zugriffe (Engpass bei Last).

**Änderungen Audit:** `jsonify` für API-Antworten; `/api/models` liefert jetzt **`folders`** (Unterordner wie im Inline-Menü); Root-Pfad-Logik für `startswith(path + "/")` nur wenn `path != "root"` (korrekte Unterordner-Zuordnung).

---

## 3. Replicate & KI

| Komponente | Rolle |
|------------|--------|
| `unified_client.py` | Hauptpfad: Schema-Adapter, `replicate.run`, OpenAI/Grok |
| `replicate_concurrency.py` | Semaphor, `REPLICATE_MAX_CONCURRENT` (Warteschlange / Parallelität) |
| `services.py` | `GenerationService`, Pipelines (Headshot) mit direktem `replicate.run` |
| `dynamic_adapter.py` | Payload aus `input_schema` |
| `replicate/clients.py` | Alternative Implementierung (aktuell nicht in `main.py` angebunden) |

**Änderungen Audit:** Keine inhaltliche Logikänderung am Adapter; `result_delivery` nutzt `InputMediaPhoto(media=url, …)` explizit (API-Klarheit).

---

## 4. Telegram-UI (Commands, Keyboard, WebApp)

- **`keyboards.py`:** Inline-Menü, Reply-Keyboard, WebApp-Buttons für Image-Loop, Chat-Menüs.
- **`menu_handler.py`:** Start, Admin (`set_menu_mode`, `reload_models`), WebApp-Daten, Navigation (ohne `nav_path_*` – die übernimmt `gen`).
- **`gen/nav_handlers.py`:** `nav_path_*`, `sel_*`, Chat Start/Stop.
- **`runner.py`:** Generierung, Retry 429, Fallback-Modell, Image-Loop-Kontext.

**Änderungen Audit:** `ADMIN_ID` robust per `_parse_admin_id()` (leere/ungültige `.env` crashen nicht).

---

## 5. Mini App (`webapp/index.html`)

**Zuvor:**
- API lieferte nur Modelle auf exaktem `menu_path`; **Unterordner** (`sub_cats`) wurden im Backend berechnet, aber **nicht** zurückgegeben → leere Ansicht, Fallback nur auf Telegram.
- Modellnamen ungeescaped in `innerHTML` → theoretisches **XSS** bei bösartigen DB-Einträgen.

**Jetzt:**
- API: `folders[]` mit `path` und `slug`.
- UI: Ordner-Karten + Modell-Karten; `escapeHtml()` für Namen und Keys.
- Deep-Link `?path=` und Zurück-Navigation nutzen `folders` mit.

---

## 6. Datenbank (`database.py`)

- PostgreSQL/Neon, Migrationen in `_migrate_db`, Modell-Cache ~60s.
- **Globaler `threading.Lock`** um praktisch alle Methoden → sicher, aber bei vielen Usern Warteschlange.
- Keine Connection-Pool (pro Aufruf connect/close).

**Empfehlung (nicht umgesetzt):** `ThreadedConnectionPool`, Lock nur pro Transaktion oder feiner granular.

---

## 7. Tools (`src/tools/`)

- `replicate_fetcher`, `reclassify_models`, `fetch_advanced`, `import_staging`, GUIs – für Betrieb separat vom Bot.
- Nicht Teil des Runtime-Pfads von `main.py` (außer bei manuellem Aufruf).

---

## 8. In diesem Audit behoben

1. **`requirements.txt`:** doppeltes `python-dotenv` entfernt.
2. **`common.py`:** Thread-sicherer Zugriff auf `user_context` (Lock, `get_context` liefert Kopie).
3. **`menu_handler.py`:** sichere `ADMIN_ID`-Interpretation.
4. **`main.py`:** `jsonify` für `/api/webapp_action` und `/api/models`; `/api/models` mit **`folders`** und korrigierter Pfadlogik; redundanter `import os` in `webapp()` entfernt.
5. **`webapp/index.html`:** Unterordner-Navigation, `escapeHtml`, robustere `showModels`-Signatur.
6. **`result_delivery.py`:** `InputMediaPhoto(media=url, …)`.

---

## 9. Offen / Verbesserungen (Backlog)

| Thema | Vorschlag |
|-------|-----------|
| DB-Skalierung | Connection-Pool, weniger globaler Lock |
| Replicate | Retry in `UnifiedAIClient` analog `replicate/clients.py` (optional) |
| Monitoring | Strukturierte Logs / Metriken für Queue-Wartezeit |
| Tests | pytest für `api_models`-Payload, `escapeHtml`-äquivalent serverseitig |
| 409 Konflikt | Nur eine Deploy-Instanz; kein lokales Polling parallel zu Render |
| `nav_main` vs `nav_path_root` | Semantik dokumentiert: beide führen zur Root-Navigation (unterschiedliche Handler) |

---

## 10. Verweise

- `doc/render_deploy.md` – Deploy, Env inkl. `REPLICATE_MAX_CONCURRENT`
- `doc/skalierbarkeit_render.md` – Last & Render
- `doc/menu_modes.md` – commands / keyboard / webapp
- `doc/code_review_ui_replicate_outputs.md` – Medien-Auslieferung

---

*Erstellt im Rahmen des vollständigen Projekt-Reviews; bei Änderungen am Menü-Schema API und Webapp gemeinsam anpassen.*
