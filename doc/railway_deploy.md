# Deployment auf Railway

Railway ist die aktuelle Haupt-Deployment-Plattform (schneller Start, kein Cold-Sleep).

---

## Voraussetzungen

- GitHub-Repository verbunden
- `runtime.txt` mit `3.12` (im Projekt – für Python-Version)

---

## Schritte

### 1. Neues Projekt auf Railway

1. [railway.app](https://railway.app) → **New Project**
2. **Deploy from GitHub repo** → Repository auswählen
3. Branch: `main`

### 2. Service konfigurieren

| Einstellung | Wert |
|-------------|------|
| **Build Command** | `npm ci --prefix webapp-react && npm run build --prefix webapp-react && pip install -r requirements.txt` |
| **Start Command** | `python main.py` |
| **Root Directory** | (leer, wenn Repo-Root) |

Alternative (empfohlen, im Repo versioniert): Über `nixpacks.toml` im Repo-Root ist der Build- und Startprozess bereits fest definiert. Dann muss in Railway kein manueller Build Command gepflegt werden.

### 3. Umgebungsvariablen

| Variable | Beschreibung |
|----------|--------------|
| `TELEGRAM_TOKEN` | Bot-Token von BotFather |
| `REPLICATE_API_TOKEN` | Replicate API Key |
| `DATABASE_URL` | Neon-PostgreSQL-URL |
| `ADMIN_ID` | Deine Telegram-Chat-ID |
| `APP_URL` | **Wichtig für Web-App:** `https://<dein-service>.up.railway.app` (nach Generate Domain setzen) |
| `REPLICATE_MAX_CONCURRENT` | (optional) Max. parallele Replicate-Requests; Standard `1` |
| `LOG_BOT_ALOSCHA` | (optional) Separater Bot für Status-Logs |
| `LOG_ADMIN_ID` | (optional) Empfänger der Status-Logs |

**APP_URL:** Nach dem ersten Deploy unter **Settings → Networking → Generate Domain** eine URL erzeugen, dann in den Variables `APP_URL=https://xxx.up.railway.app` setzen (ohne `/webapp` am Ende).

**Aktuelle Production-URL:** `https://flux-bot-azamat-production.up.railway.app`

### 4. Web-App mit BotFather

1. [@BotFather](https://t.me/BotFather) → `/setmenubutton`
2. URL: `https://flux-bot-azamat-production.up.railway.app/webapp-react` (React Dual-Variante)
   (alternativ für die alte HTML-UI: `/webapp`)

### 5. Port

Railway setzt `PORT` automatisch (z.B. 8080). Der Bot nutzt `os.getenv("PORT", 5000)`.

---

## Wichtige Punkte

- **409 Conflict:** Läuft der Bot noch auf Render oder lokal, kommt es zu Konflikten. Nur **eine** Instanz pro Token.
- **Retry bei 409:** Der Bot wartet 30s und versucht erneut – hilft bei Deploy-Overlap.
- **Health Check:** `GET /` liefert „🤖 System Status: ONLINE“.

---

## Migration von Render

1. Render-Service stoppen oder löschen
2. Railway deployen
3. `APP_URL` auf die Railway-URL setzen
4. BotFather: Menü-Button-URL auf Railway ändern
