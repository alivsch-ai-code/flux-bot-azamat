# Replicate Schema & UX Audit (2026-04)

Dieses Dokument fasst eine technische Prüfung von Replicate-Integration, Schema-Verarbeitung, Neon-Datenbestand, UI/UX-Flows und Testabdeckung zusammen.

---

## Scope

- Replicate-Integration: `src/infrastructure/ai/unified_client.py`
- Schema-Adapter: `src/infrastructure/ai/dynamic_adapter.py`
- Telegram Delivery: `src/presentation/telegram/handlers/gen/result_delivery.py`
- WebApp/API: `src/presentation/http/http_routes.py`, `webapp-react/src/views/*`
- Datenbank: `ai_models` in Neon (`DATABASE_URL`)

---

## Externe Referenzen (offiziell)

- Replicate: [Create a prediction](https://replicate.com/docs/topics/predictions/create-a-prediction)
- Replicate: [Input files](https://replicate.com/docs/topics/predictions/input-files)
- Replicate: [HTTP API reference](https://replicate.com/docs/reference/http)

UX-Research (NN/g):

- [Mobile Input Checklist](https://www.nngroup.com/articles/mobile-input-checklist/)
- [Web Form Design Top Recommendations](https://www.nngroup.com/articles/web-form-design/)

---

## Neon DB Audit (Snapshot)

Prüfung der aktiven Modelle (`ai_models WHERE is_active=1`):

- aktive Modelle: `55`
- ohne `input_schema`: `0`
- ohne `output_schema`: `0`
- `required`-Keys ohne passendes `properties`-Feld: `0`
- Modelle mit mindestens einem URI-Feld im Input: `30`

Ergebnis: Grundkonsistenz der Schemas in Neon ist gut.

---

## Umgesetzte Fixes in diesem Audit

### 1) Replicate Multi-Output wurde abgeschnitten (behoben)

In `UnifiedAIClient.normalize_replicate_output()` wurde bei Listen/Iteratoren bisher oft nur das erste FileOutput-Element zurückgegeben.

Neu:

- Wenn FileOutputs in einer Liste enthalten sind, bleibt die **komplette Liste** erhalten.
- Gleiches Verhalten für Iteratoren mit FileOutput-Elementen.

Impact:

- Multi-Image/Multi-Asset-Modelle verlieren keine Ergebnisse mehr vor der Delivery-Stufe.

### 2) Schema-Mapping für URLs ohne Dateiendung (behoben)

In `DynamicSchemaAdapter._map_files_to_schema()` wurden `unknown`-URLs zuvor nur für Bild-Slots als Fallback akzeptiert.

Neu:

- `unknown` wird nun auch für `video`- und `audio`-Slots akzeptiert, wenn passende Medienfelder erwartet werden.

Impact:

- Robustere Zuordnung bei CDN-/Replicate-URLs ohne Dateiendung.
- Weniger „fehlendes Input-File“, obwohl Upload vorhanden ist.

### 3) UX/A11y Keyboard-Nutzung in der WebApp verbessert

In `MainView` und `ModelsView` wurden klickbare Karten/Container um Keyboard-Aktivierung ergänzt (`Enter`/`Space`).

Impact:

- Bessere Accessibility und konsistentes Verhalten für Tastaturnutzer.

### 4) Striktes Schema-Merging für `generation_params` (zweite Audit-Welle)

In `UnifiedAIClient.build_replicate_input_dict()`:

- Es werden nur noch `generation_params`-Keys übernommen, die im `input_schema.properties` existieren.
- Werte werden gegen den erwarteten Typ coerced (`boolean`, `integer`, `number`, `string`, `array`).
- `enum` wird strikt geprüft (nicht erlaubte Werte werden verworfen).

Impact:

- Weniger 400er/Validation-Fehler bei Replicate.
- WebApp/Caller können keine schemafremden Parameter mehr unbemerkt injizieren.

### 5) Delivery-Heuristik für `replicate.delivery` entschärft

In `result_delivery._infer_media_kind_from_url()`:

- `replicate.delivery` ohne Dateiendung wird nicht mehr pauschal als Bild angenommen.
- Medientyp-Entscheid bleibt bei Modelltyp/Byte-Sniffing.

Impact:

- Weniger falsche `send_photo`-Versuche bei Video/Audio-Assets mit extensionlosen URLs.

---

## Ergänzte Tests

- `tests/test_unified_client_options.py`
  - neuer Test: Multi-FileOutputs bleiben als Liste erhalten.
- `tests/test_dynamic_adapter.py`
  - neuer Test: extensionlose URL wird korrekt auf `input_video` gemappt.
  - neuer Test: extensionlose URL wird korrekt auf `input_audio` gemappt.
- `tests/test_result_delivery_media_types.py`
  - neuer Test: extensionlose `replicate.delivery`-URL ohne Modelltyp fällt sauber auf Text-Link zurück.

---

## Offene Risiken / nächste Schritte

- Schema-validiertes Merging von `generation_params` gegen `input_schema` (Typ/Enum-Checks) ist noch ausbaufähig.
- Optional: `output_schema` stärker in die Normalisierung einbeziehen (schema-aware extraction).
- Optional: zentrales React-Notification-System mit `aria-live` statt ad-hoc Overlay.

---

## Fazit

Der Replicate-Flow ist deutlich robuster für reale Modelloutputs und dateiendungslose Upload-URLs.  
Die Neon-Schemas sind konsistent.  
Die UI ist im Bereich Tastatur-Bedienung verbessert, ohne bestehende Funktionen zu brechen.

