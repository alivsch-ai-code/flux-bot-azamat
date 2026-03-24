# Anwendungsfälle und Schnittstellen

Dieses Dokument beschreibt typische **Use Cases**, die **äußeren und inneren Schnittstellen** des AZAMAT-Bots und ergänzt [architecture.md](architecture.md) sowie das [README](../README.md).

---

## 1. Anwendungsfälle (Überblick)

| Use Case | Kurzbeschreibung | Haupt-Einstieg |
|----------|------------------|----------------|
| **Privat: Erste Nachricht → Chat** | Nutzer schreibt ohne Menü-Kontext Text → Bot aktiviert Default-Textmodell (z. B. Gemini Flash) und antwortet. | `prompt_handlers` → `chat_debounce` → `run_generation` |
| **Privat: Modell-Chat** | Nutzer startet Chat zu einem gewählten Textmodell; Nachrichten werden gebündelt beantwortet (siehe Abschnitt 4). | `nav_handlers` (Chat ja) + `prompt_handlers` |
| **Privat: Bild/Video/Audio** | Modell wählen → Prompt (optional Optimierung) → `GenerationService` → Medienversand. | `start_handler`, `prompt_handlers`, `media_handlers`, `runner` |
| **Privat: Mini App** | Shop, Einstellungen, Modell-Details, Referenz-Upload über eingebettete Web-UI. | `webapp/index.html` → Flask-APIs unter `/api/*` |
| **Privat: Credits** | Pakete kaufen per Telegram Stars (`/shop`, Inline-Buttons). | `payment_handler` |
| **Gruppe: AZAMAT-Chat** | Text in Gruppe → gebündelte Gemini-Antwort; Credits pro schreibendem Nutzer (Gruppen-Logik in DB). | `group_handler` + `chat_debounce` |
| **Gruppe: Shop & Sprache** | `/shop`, Inline „Credits“ / „Sprache“; Shop per DM; Sprache pro `chat_id`. | `group_handler` |
| **Admin** | Menümodus, Modell-Reload, ggf. `cheat_mode` / WebApp-Aktionen. | `menu_handler`, `main.py` |

---

## 2. Schnittstelle: Telegram Bot

### 2.1 Registrierungsreihenfolge

In [`src/presentation/telegram/bot.py`](../src/presentation/telegram/bot.py) (`setup_bot`):

1. `group_handler.register` — Gruppen-Text und Gruppen-Commands zuerst.
2. `menu_handler.register` — `/start` (privat), Tastatur-Navigation, WebApp-Daten.
3. `payment_handler.register`
4. `gen_handler.register` — u. a. `prompt_handlers` mit breitem `message_handler`.

**Wichtig:** Gruppennachrichten werden in `prompt_handlers.on_prompt` sofort ignoriert (`group` / `supergroup`), damit keine doppelte Verarbeitung neben `group_handler` entsteht.

### 2.2 Zentrale Handler-Module

| Modul | Rolle |
|-------|--------|
| `group_handler.py` | Gruppen: Text (Gemini), `/start`, Shop, Sprache |
| `menu_handler.py` | Willkommen, Pfad-Tastatur, WebApp-Aktionen, `/start` privat |
| `payment_handler.py` | Rechnungen, Stars, erfolgreiche Zahlung |
| `gen/nav_handlers.py` | `nav_*`, `sel_*`, Chat starten/beenden |
| `gen/prompt_handlers.py` | Freitext (privat): Chat-Modus, Default-Chat, `waiting_for_prompt` |
| `gen/runner.py` | `create_run_generation` → `GenerationService`, `parse_and_deliver` |
| `gen/chat_sessions.py` | Persistente Chat-History (`append_with_summary_if_needed`, `build_chat_prompt_from_messages`) |
| `chat_debounce.py` | Bündeln kurzer Nachrichtenfolgen (siehe Abschnitt 4) |

---

## 3. Schnittstelle: HTTP / Flask (`main.py`)

Alle Routen laufen im selben Prozess wie der Telegram-Polling-Thread (siehe Deploy-Doku).

| Route | Methode | Zweck |
|-------|---------|--------|
| `/` | GET | Health / einfache Antwort |
| `/webapp` | GET | Auslieferung der Mini-App (`webapp/index.html`) |
| `/api/webapp_action` | POST | Aktionen aus der WebApp (`action`, `init_data`); ruft `process_webapp_action` auf |
| `/api/user_info` | POST | Nutzer, Credits, Sprache, Bot-Username anhand `init_data` |
| `/api/strings` | GET | `?lang=de|en|ru|kk` — UI-Strings für die WebApp |
| `/api/model` | GET | `?key=<model_key>` — Modell-Metadaten, Schema, `generation_options_schema`, Veo-Hinweise |
| `/api/models` | GET | Liste aktiver Modelle (WebApp) |
| `/api/shop_packages` | GET | Pakete für Shop-UI |
| `/api/webapp_upload_reference` | POST | Multipart: Referenzbilder → Replicate Files → URLs |

**Authentifizierung WebApp:** Telegram `init_data` wird mit Bot-Token validiert (`validate_init_data`); bei Fehler meist HTTP 403.

---

## 4. Chat-Batching (Debounce)

**Modul:** [`src/presentation/telegram/handlers/chat_debounce.py`](../src/presentation/telegram/handlers/chat_debounce.py)

### 4.1 Verhalten

- Pro **Chat-ID** (privat: gleich User-ID; Gruppe: Gruppen-`chat_id`) werden eingehende **Textnachrichten** in einem Burst gesammelt.
- Nach der **1.** Nachricht: Wartezeit **20 s**; **2.** → **10 s**; **3.** → **5 s**; **4.** → **10 s** (Timer wird bei jeder neuen Nachricht neu gestartet).
- Ab der **5.** Nachricht im gleichen Burst: **sofort** Flush — **eine** LLM-Anfrage, die **alle** gesammelten Inhalte berücksichtigt.
- **Abbruch:** `cancel_pending_batch(chat_id)` verwirft den Puffer und den Timer — u. a. bei Chat beenden oder wenn der Nutzer ins Hauptmenü wechselt (`nav_handlers`, `menu_handler`).

### 4.2 Öffentliche API (Python)

```text
schedule_batched_text_message(chat_id: int, item: tuple[int, str, str], on_flush: Callable) -> None
  item = (telegram_user_id, display_name, text)
  on_flush(chat_id, batch: list[tuple[int, str, str]])  # bei Ablauf oder sofort ab 5 Nachrichten

cancel_pending_batch(chat_id: int) -> None

debounce_delay_seconds_for_count(n: int) -> int | None  # None = sofort flush; vor allem für Tests
```

**Hinweis:** `waiting_for_prompt` (Medien-Generierung mit optionaler Prompt-Optimierung) läuft **ohne** dieses Batching.

---

## 5. Schnittstelle: Anwendungsschicht

### 5.1 `GenerationService.process_request`

Definiert in [`src/application/services.py`](../src/application/services.py). Kernparameter:

| Parameter | Bedeutung |
|-----------|-----------|
| `user_id` | Telegram-User (Credits-Inhaber) |
| `model` | `AIModel` aus der DB |
| `prompt` | Bereinigter/finaler Prompt |
| `media_files` | Optional `List[MediaFile]` |
| `no_charge` | z. B. Willkommens-DM in Gruppen |
| `group_chat_id` | Wenn gesetzt: effektive Credits / Abbuchung im Gruppenkontext |
| `generation_params` | z. B. Dauer, Auflösung, `aspect_ratio`, Referenz-URLs |
| `charge_cost` | Optionaler Override der Kosten |

**Rückgabe:** `(success: bool, result | fehlermeldung)`.

Validierung: `InputValidator` (Sicherheit, Sanitizing); bei Bildmodellen ggf. Mindestauflösung.

### 5.2 Domain-Verträge (Referenz)

In [`src/domain/interfaces.py`](../src/domain/interfaces.py):

- `UserRepository` — Nutzer & Credits (konzeptionell; konkrete Implementierung ist `DatabaseManager`).
- `AIProvider.generate` — konzeptioneller AI-Vertrag; Laufzeit nutzt `UnifiedAIClient` über die gleiche Schicht.

---

## 6. Datenhaltung (Kurz)

- **PostgreSQL** über `DatabaseManager` (`DATABASE_URL`): Nutzer, Credits, Modelle, Chat-Sessions, Gruppeneinstellungen, Transaktionen.
- **Chat-Session-Keys:** privat `user_id` + `model_key`; Gruppe `session_id = -abs(chat_id)` mit Modell-Key-Suffix `_group` (siehe `group_handler`).
- **`daily_posts`:** Pro Kalendertag höchstens ein Eintrag (`date_to_send` unique). `message_text` kann **einfacher HTML-Text** sein oder **JSON** mit Schlüsseln `de`, `en`, `ru`, `kk` — der `DailyService` wählt pro Abonnent die passende Sprache (`daily_services._resolve_daily_message_text`). Beispiel-Skript: `tools/seed_daily_alexa_plus_tomorrow.py`.

---

## 7. Weiterführende Dokumentation

- [architecture.md](architecture.md) — Schichtenmodell (Mermaid)
- [menu_modes.md](menu_modes.md) — Commands / Keyboard / WebApp
- [render_deploy.md](render_deploy.md), [railway_deploy.md](railway_deploy.md) — Betrieb
- [tests_dokumentation.md](tests_dokumentation.md) — Testüberblick
