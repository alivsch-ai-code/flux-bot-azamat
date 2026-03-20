# Code-Review: UI, Replicate-Requests & Modell-Outputs

Stand: März 2025

## 1. Architektur-Überblick

```
User → Telegram → gen_handler/runner → GenerationService → UnifiedAIClient → Replicate API
                                                                              ↓
User ← parse_and_deliver ← result ← process_request ← GenerationResult ← output
```

- **main.py**: Verwendet `UnifiedAIClient` (nicht den separaten `ReplicateClient` aus `replicate/clients.py`)
- **UnifiedAIClient** (`unified_client.py`): Routing nach Provider (replicate, openai, grok, kling)
- **DynamicSchemaAdapter** (`dynamic_adapter.py`): Input-Payload aus DB-Schema, Output-Parsing (wird von ReplicateClient genutzt, UnifiedAIClient hat eigene Logik)

---

## 2. UI (Telegram)

### 2.1 Menü-Modi
- **commands**: Inline-Buttons (Kategorien, Modelle)
- **keyboard**: Reply Keyboard (Kategorien/Modelle als Tasten)
- **webapp**: Nur Web-App-Button + optional Menü-Button neben dem Eingabefeld

### 2.2 Wichtige UI-Flows
| Aktion | Handler | Menü nach Erfolg |
|--------|---------|------------------|
| /start | menu_handler.send_welcome | Nur eine Variante je Modus |
| nav_main (Zurück) | menu_handler.handle_navigation | Nur eine Variante je Modus |
| nav_path_* | nav_handlers.handle_path_nav | Keyboard: nur Reply, sonst Inline |
| Generierung erfolgreich | runner.run_generation | Jetzt menü-modusabhängig |
| Image-Loop (weiteres Bild) | runner | Keyboard: keine Inline-Buttons |

### 2.3 Behobene Punkte
- Nach Generierung wird das Menü je nach `menu_mode` korrekt gesetzt (keyboard/webapp/commands)
- Im Image-Loop bei Keyboard-Modus werden keine zusätzlichen Inline-Buttons mehr gesendet

---

## 3. Replicate-Request-Verarbeitung

### 3.1 Flow (UnifiedAIClient._run_replicate)
1. **Dateien**: Lokale Pfade → Data-URI (klein) oder Replicate Files API (groß)
2. **Input-Payload**: `DynamicSchemaAdapter.build_input_payload` wenn `input_schema` in DB
3. **Sonderfälle**:
   - `flux` in model.key → `aspect_ratio: "16:9"`, `safety_tolerance: 5`
   - `minimax` → `prompt_optimizer: True`
4. **API-Call**: `replicate.run(model.replicate_id, input=input_data)`

### 3.2 Kein Retry im UnifiedAIClient
- Der `ReplicateClient` in `replicate/clients.py` hat Retry bei Rate Limit
- Der **UnifiedAIClient** ruft `replicate.run` direkt auf – Retries erfolgen im **runner** (bei 429, bis zu 4 Versuche mit Wartezeit)

### 3.3 Behobene Punkte
- **Premium Pipeline** / **Ultimate Pipeline**: `image_url=None` → `media_files=None` (korrekter Parameter)

---

## 4. Modell-Outputs

### 4.1 Output-Formate (Replicate)
- **FileOutput** mit `.url` (Bilder, Video, Audio)
- **Liste** von FileOutputs oder Strings
- **Generator** (Streaming-Text)
- **String** (reiner Text)

### 4.2 UnifiedAIClient Output-Handling
- FileOutput → `data=output` (Objekt mit .url)
- Liste: erstes Element (Media) oder alle Strings zusammengefügt (Text)
- Generator → in Liste sammeln, dann wie Liste

### 4.3 parse_and_deliver (result_delivery.py)
- **Einzelbild**: `send_photo` (URL oder Bytes nach Download)
- **Mehrere Bilder** (z.B. Premium Pipeline): `send_media_group` mit bis zu 10 Fotos
- **Video/Audio**: `send_video` / `send_audio`
- **Chat-Modus**: Text als Nachricht + Chat-Menü
- **Fallback**: URL als Text, bei Fehlern `send_document`

### 4.4 Behobene Punkte
- **Listen-Output**: Premium Pipeline liefert 4 URLs – bisher nur erstes Bild angezeigt. Jetzt `send_media_group` für 2–10 Bilder.

---

## 5. Potenzielle Verbesserungen (offen)

1. **UnifiedAIClient**: Kein Retry bei Rate Limit – Retries nur im runner. Evtl. Retry-Logik wie im ReplicateClient übernehmen.
2. **ReplicateClient** (`replicate/clients.py`): Wird nicht genutzt – entweder entfernen oder als Alternative zu UnifiedAIClient anbieten.
3. **output_schema**: Wird im UnifiedAIClient nicht genutzt; `DynamicSchemaAdapter.parse_output` nur im ReplicateClient. Bei komplexen API-Responses könnte eine einheitliche Nutzung helfen.
4. **Face Swap**: Replicate erwartet `swap_image` als File-Objekt. Aktuell `open(..., "rb")` – prüfen, ob Replicate damit umgehen kann (evtl. Upload zu Replicate nötig).

---

## 6. Geänderte Dateien (Review-Fixes)

| Datei | Änderung |
|-------|----------|
| `src/application/services.py` | `image_url=None` → `media_files=None` (2 Stellen) |
| `src/presentation/telegram/handlers/gen/result_delivery.py` | `_extract_urls_from_result`, `send_media_group` für Listen |
| `src/presentation/telegram/handlers/gen/runner.py` | Menü-Modus nach Generierung; Image-Loop ohne Inline bei keyboard |
