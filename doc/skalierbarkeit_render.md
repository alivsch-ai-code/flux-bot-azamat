# Skalierbarkeits-Untersuchung: ~40 gleichzeitige User auf Render

## Zusammenfassung

| Frage | Antwort |
|-------|---------|
| **Kann der Bot 40 gleichzeitige User bedienen?** | Teilweise – mit Einschränkungen und Empfehlungen |
| **Auf dem Render Free Tier?** | Eher nein – Cold Starts, RAM, evtl. Traffic-Sperre |
| **Mit Render Starter ($7/mo)?** | Eher ja – wenn Optimierungen umgesetzt werden |

---

## 1. Architektur-Überblick

### Ablauf pro User-Request

```
Telegram → infinity_polling → Handler-Thread → process_request()
                                    ↓
                    DB (Neon) ←→ Replicate API
                                    ↓
                         Antwort an User
```

### Wichtige Komponenten

| Komponente | Technik | Parallelität |
|------------|---------|--------------|
| Bot-Polling | pyTelegramBotAPI `infinity_polling()` | Ein Polling-Thread; Updates werden in **separaten Threads** verarbeitet |
| Flask | `app.run()` (Standard-Server) | **Ein Request gleichzeitig** (single-threaded) |
| Datenbank | psycopg2, `threading.Lock` | **Alle DB-Zugriffe serialisiert** |
| Replicate | `replicate.run()` (synchron) | Pro Generierung ein blockierender Aufruf (10–60+ Sekunden) |
| `user_context` | In-Memory-Dict | Kein Lock – theoretisch race conditions möglich |

---

## 2. Engpässe im Detail

### 2.1 Flask-Webserver (Kritisch)

```python
# main.py Zeile 107
app.run(host='0.0.0.0', port=config.PORT, use_reloader=False)
```

- Der eingebaute Flask-Server ist **single-threaded**
- Endpunkte: `/api/webapp_action`, `/api/models`, `/webapp`
- **40 User** rufen gleichzeitig z.B. `/api/models` auf → maximal **ein Request zur Zeit**
- Folge: Lange Wartezeiten, Timeouts, schlechte UX

**Empfehlung:** Produktions-WSGI-Server (z.B. Gunicorn) mit mehreren Workers/Threads.

---

### 2.2 Datenbank-Zugriff (Hoch)

```python
# database.py
self.lock = threading.Lock()

def get_user_credits(self, user_id):
    with self.lock:  # <-- Alle 40 User warten auf diesen Lock
        conn = self._get_connection()
        ...
```

- **Jeder** DB-Zugriff nutzt den gleichen `Lock`
- Pro Generierung: `get_user_credits`, `update_credits`, `get_model_by_key`, ggf. `get_all_models`, etc.
- Folge: Viele Threads blockieren sich gegenseitig

Zusätzlich: Neue Verbindung pro Request (`_get_connection()`), kein Connection-Pooling. Bei Neon kann das funktionieren, erhöht aber Latenz.

---

### 2.3 Replicate API (Mittel)

- Limit: **600 Predictions pro Minute** (create prediction)
- 40 User × 1 Generierung/Minute = 40 Requests → weit unter dem Limit
- Wenn viele User gleichzeitig generieren: kurze Bursts möglich, danach evtl. 429
- Der Bot hat **Retry-Logik** bei 429 (20 s Pause, bis zu 4 Versuche)

**Hinweis:** Ohne Zahlungsmethode bei Replicate: nur **1 Request/Sekunde, max. 6/Minute** – dann reicht es nicht für 40 User.

---

### 2.4 Render-Ressourcen

| Aspekt | Free Tier | Starter ($7) |
|--------|-----------|--------------|
| RAM | 512 MB | 512 MB |
| CPU | Shared | Shared |
| Cold Start | Nach ~15 Min Inaktivität, ~50–60 s | Kein Sleep |
| Traffic | Risiko: Sperre bei „service-initiated“ Traffic | Stabiler |
| Laufzeit | 750 h/Monat | Unbegrenzt |

- 40 gleichzeitige Threads + Flask + DB-Verbindungen + Replicate-Requests → **512 MB können knapp werden**
- Free Tier: Cold Starts stören bei häufigem Gebrauch stark

---

### 2.5 `user_context` (behoben)

- `common.py` nutzt jetzt ein **`threading.Lock`** und `get_context` liefert eine **Kopie** des Kontexts, damit parallele Handler-Threads sicher sind.

---

## 3. Szenario: 40 User gleichzeitig aktiv

### Typischer Lastfall

- Einige User: Modell auswählen, Prompt eingeben, Generierung starten
- Andere: Menü/WebApp aufrufen, Credits prüfen, Bilder ansehen
- Generierungen: 10–60 s pro Request

### Erwartetes Verhalten

| Komponente | Verhalten |
|------------|-----------|
| Telegram-Handler | 40 Threads parallel – prinzipiell kein Problem |
| Flask `/api/*` | Starke Verzögerung, da single-threaded |
| Datenbank | Deutliche Verzögerung durch Lock-Serialisierung |
| Replicate | OK, solange Zahlungsmethode hinterlegt ist |
| RAM | Möglich knapp bei vielen gleichzeitigen Threads |

---

## 4. Empfehlungen

### Kurzfristig (für ~40 User)

1. **Starter statt Free**  
   - Kein Sleep, stabilere Laufzeit

2. **Flask mit Gunicorn betreiben**  
   ```bash
   # Start Command auf Render
   gunicorn -w 2 -b 0.0.0.0:$PORT main:app
   ```
   - `main.py` muss `app` exportieren (ist der Fall)
   - Gunicorn zu `requirements.txt` hinzufügen

3. **Replicate: Zahlungsmethode hinterlegen**  
   - Sonst nur 6 Requests/Minute → für 40 User nicht ausreichend

### Mittelfristig (bei weiterem Wachstum)

4. **Connection-Pooling für Neon**  
   - z.B. `psycopg2.pool.ThreadedConnectionPool`

5. **DB-Lock granulieren**  
   - Lock pro Operation oder pro Connection statt global

6. **Generierungen asynchron**  
   - z.B. Celery oder Background-Threads, damit Handler-Threads nicht minutenlang blockieren (größerer Refactor)

7. ~~**`user_context` thread-sicher machen**~~ – umgesetzt (siehe `common.py`).

---

## 5. Fazit

| Bedingung | Eignung für 40 User |
|-----------|----------------------|
| Render Free | Eher nein (Cold Start, Ressourcen, evtl. Traffic-Limit) |
| Render Starter + Gunicorn + Zahlungsmethode Replicate | Eher ja |
| Ohne Anpassungen (nur Starter) | Möglicherweise – aber Flask bleibt Engpass |

Der Bot ist prinzipiell darauf ausgelegt, mehrere User parallel zu bedienen (thread-basiert). Die Limitierungen liegen vor allem bei:

- Flask (single-threaded)
- globalem DB-Lock
- Render Free Tier

Mit **Starter + Gunicorn + Replicate-Zahlungsmethode** ist der Betrieb mit ~40 gleichzeitigen Usern realistisch.
