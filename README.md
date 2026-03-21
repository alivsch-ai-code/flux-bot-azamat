# 🤖 AZAMAT AI Hub

Telegram-Bot für KI-Generierung (Bilder, Video, Audio, Text) via Replicate, OpenAI u.a.

## Schnellstart

```bash
pip install -r requirements.txt
# .env mit TELEGRAM_TOKEN, REPLICATE_API_TOKEN, DATABASE_URL anlegen
python main.py
```

## Deployment

- **Railway:** siehe [doc/railway_deploy.md](doc/railway_deploy.md)
- **Render:** siehe [doc/render_deploy.md](doc/render_deploy.md)

## Struktur

| Pfad | Beschreibung |
|------|--------------|
| `main.py` | Einstieg, Flask + Waitress, Telegram-Polling |
| `src/application/` | GenerationService, Logik |
| `src/presentation/telegram/` | Bot, Handler, Keyboards |
| `webapp/` | Telegram Mini App (HTML) |
| `doc/` | Deployment, Architektur, Audit |

## Env-Variablen

| Variable | Pflicht | Beschreibung |
|----------|---------|--------------|
| `TELEGRAM_TOKEN` | ✓ | Bot-Token von @BotFather |
| `REPLICATE_API_TOKEN` | ✓ | Replicate API Key |
| `DATABASE_URL` | ✓ | Neon PostgreSQL URL |
| `APP_URL` | (für WebApp) | z.B. `https://xxx.up.railway.app` |
| `REPLICATE_MAX_CONCURRENT` | | Max. parallele Replicate-Requests (Standard: 1) |
