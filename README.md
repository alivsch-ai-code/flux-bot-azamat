# 🤖 AZAMAT AI Hub

> **All-in-One Telegram Bot** für KI-Generierung: Bilder, Videos, Audio, Text & Chat – powered by Replicate, OpenAI, Gemini und mehr.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0?logo=telegram)](https://core.telegram.org/bots)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql)](https://neon.tech)

---

## ✨ Highlights

| Feature | Beschreibung |
|---------|--------------|
| 🎨 **Multi-Modal AI** | Flux, DALL·E, Kling, Hunyuan, Gemini u.v.m. – Bilder, Video, Audio, Text |
| 🌐 **Telegram Mini App** | Moderne Web-App im Telegram-Client – Kategorien, Modelle, Shop, Einstellungen |
| 👥 **Gruppen-Modus** | AZAMAT in Gruppen: Chat mit Gemini, Credits kaufen, Sprachwahl – einmalige Willkommens-DM |
| 🌍 **Mehrsprachig** | Deutsch, English, Русский, Қазақша |
| 💳 **Credits & Stars** | Bezahlung via Telegram Stars (XTR), transparente Preise pro Generierung |
| 📱 **3 Menü-Modi** | Commands, Keyboard oder WebApp – flexibel konfigurierbar |

---

## 🛠 Tech Stack

- **Bot:** [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- **AI:** [Replicate](https://replicate.com), OpenAI, Gemini (via Replicate)
- **DB:** PostgreSQL (Neon)
- **Web:** Flask, Waitress
- **Deploy:** Render, Railway

---

## 🚀 Schnellstart

```bash
# Repository klonen
git clone https://github.com/alivsch-ai-code/flux-bot-azamat.git
cd flux-bot-azamat

# Abhängigkeiten
pip install -r requirements.txt

# Konfiguration (.env anlegen)
cp .env.example .env   # Falls vorhanden
# TELEGRAM_TOKEN, REPLICATE_API_TOKEN, DATABASE_URL eintragen

# Starten
python main.py
```

---

## ⚙️ Konfiguration

| Variable | Pflicht | Beschreibung |
|----------|---------|--------------|
| `TELEGRAM_TOKEN` | ✓ | Bot-Token von [@BotFather](https://t.me/BotFather) |
| `REPLICATE_API_TOKEN` | ✓ | API-Key von [replicate.com](https://replicate.com) |
| `DATABASE_URL` | ✓ | PostgreSQL-URL (z.B. [Neon](https://neon.tech)) |
| `APP_URL` | (WebApp) | HTTPS-Basis-URL, z.B. `https://xxx.onrender.com` |
| `OPENAI_API_KEY` | (Optional) | Für DALL·E / GPT-Modelle |
| `ADMIN_ID` | (Optional) | Telegram-User-ID für Admin-Befehle |
| `REPLICATE_MAX_CONCURRENT` | | Max. parallele Replicate-Requests (Default: 1) |

---

## 📁 Projektstruktur

```
flux-bot-azamat/
├── main.py                 # Einstieg: Flask + Telegram-Polling
├── webapp/
│   └── index.html          # Telegram Mini App (Shop, Settings, Modelle)
├── src/
│   ├── application/        # GenerationService, Business-Logik
│   ├── domain/             # Entities, Interfaces
│   ├── infrastructure/     # DB, Replicate, OpenAI-Adapter
│   ├── presentation/       # Telegram Bot, Handler, Keyboards
│   │   └── telegram/
│   │       ├── handlers/
│   │       │   ├── group_handler.py   # Gruppen: Gemini, Credits, Sprache
│   │       │   ├── menu_handler.py    # Menü, Einstellungen
│   │       │   ├── payment_handler.py # Shop, Invoice (Stars)
│   │       │   └── gen/               # Generation, Navigation, Media
│   │       └── keyboards.py
│   ├── config/
│   └── utils/              # Strings (i18n), Validierung
└── doc/                    # Deployment, Architektur, Audit
```

---

## 🌐 Menü-Modi

| Modus | Beschreibung |
|-------|--------------|
| `commands` | Standard: `/start`, `/shop` + Inline-Buttons |
| `keyboard` | Reply-Keyboard am Eingabefeld mit Kategorien |
| `webapp` | Telegram Mini App – alles in einer Oberfläche |

**Admin:** `/set_menu_mode commands|keyboard|webapp`

Für die WebApp wird eine HTTPS-URL (`APP_URL`) und die Freigabe der Domain bei [@BotFather](https://t.me/BotFather) benötigt.

---

## 👥 Gruppen-Modus

Wenn AZAMAT zu einer **Gruppe** hinzugefügt wird:

- **Chat:** Ausschließlich mit **Gemini** – lustig, freundlich, frech (AZAMAT-Persönlichkeit)
- **Credits:** Kauf über Inline-Buttons → DM mit Shop
- **Sprache:** DE, EN, RU, KK pro Gruppe einstellbar
- **Willkommen:** Einmalige persönliche Begrüßung per DM (Gemini-generiert) – jeder User nur einmal

---

## 📦 Deployment

- **[Render](doc/render_deploy.md)** – Empfohlen, Web Service + Healthchecks
- **[Railway](doc/railway_deploy.md)** – Alternative mit einfachem Setup

---

## 📄 Lizenz

MIT
