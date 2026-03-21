# Deployment auf Render

> **Hinweis:** Aktuell läuft der Bot auf **Railway** – siehe `doc/railway_deploy.md`.

## Web-Adresse bekommen

Bei einem **Web Service** auf Render bekommst du automatisch eine HTTPS-URL:

`https://<dein-service-name>.onrender.com`

Diese URL wird von Render gesetzt und in `RENDER_EXTERNAL_URL` bereitgestellt. Der Bot nutzt sie automatisch für die Web-App.

---

## Schritte

### 1. Render-Dashboard

1. Gehe zu [render.com](https://render.com) und melde dich an.
2. **New** → **Web Service**
3. Repository verbinden (z.B. GitHub)

### 2. Service konfigurieren

| Einstellung | Wert |
|-------------|------|
| **Name** | z.B. `flux-bot-azamat` (wird Teil der URL) |
| **Region** | Frankfurt (oder nahe zu dir) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python main.py` |
| **Instance Type** | Free (oder Starter) |

### 3. Umgebungsvariablen (Environment)

Unter **Environment** diese Variablen setzen:

| Variable | Beschreibung |
|----------|--------------|
| `TELEGRAM_TOKEN` | Bot-Token von BotFather |
| `REPLICATE_API_TOKEN` | Replicate API Key |
| `DATABASE_URL` | Neon-PostgreSQL-URL |
| `ADMIN_ID` | Deine Telegram-Chat-ID |
| `SONAUTO_API_KEY` | (optional) |
| `REPLICATE_MAX_CONCURRENT` | (optional) Max. parallele Replicate-Generierungen; Standard `1` (nacheinander). Z. B. `2` für zwei gleichzeitige Predictions. |
| … | Weitere Keys wie in `.env` |

**Hinweis:** `APP_URL` und `RENDER_EXTERNAL_URL` musst du **nicht** setzen – Render füllt `RENDER_EXTERNAL_URL` automatisch.

### 4. Deploy

- Auf **Create Web Service** klicken.
- Render startet den Build und den Service.
- Nach dem Start siehst du die URL z.B. unter: `https://flux-bot-azamat.onrender.com`

### 5. Web-App mit BotFather verknüpfen

1. [@BotFather](https://t.me/BotFather) öffnen
2. `/setmenubutton` → deinen Bot wählen
3. URL angeben: `https://flux-bot-azamat.onrender.com/webapp`  
   (Name durch deinen Service-Namen ersetzen)

---

## Wichtige Punkte

- **Port:** Render setzt `PORT` automatisch (meist 10000). Der Code verwendet bereits `os.getenv("PORT", 5000)`.
- **Cold Start:** Beim Free Tier kann der Service nach Inaktivität einschlafen; der erste Aufruf dauert dann länger.
- **Health Check:** `GET /` liefert „🤖 System Status: ONLINE“ – Render nutzt das für Health Checks.
