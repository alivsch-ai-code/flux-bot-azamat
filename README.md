# 🤖 AZAMAT AI Hub — All-in-One Telegram Bot for AI Image, Video & Audio Generation

> **The ultimate Telegram bot** for generating AI images, videos, music, and chat — powered by **Flux**, **DALL·E 3**, **Kling (via Replicate models)**, **HunyuanVideo**, **Gemini**, and more. One bot, dozens of models, Telegram Stars payments.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-2CA5E0?logo=telegram)](https://core.telegram.org/bots)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql)](https://neon.tech)

**Find this project when searching for:** *telegram ai image generation bot* · *flux telegram bot* · *dall-e telegram* · *ai art bot* · *text to image telegram* · *video generation bot* · *replicate telegram* · *telegram stars payment*

---

## 🎯 What is this?

**AZAMAT AI Hub** is an open-source **Telegram bot** that turns your chat into a full **AI creative studio**. Generate images from text (text-to-image), videos, music, voice clones, and chat with LLMs — all inside Telegram. No app switching, no complicated UIs. Just message the bot or open its Mini App.

Perfect for developers who want a **ready-made AI bot** for Telegram, or anyone building **image generation**, **video generation**, or **AI chatbot** projects with a modern stack.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎨 **AI Image Generation** | **Flux**, **Flux Pro**, **DALL·E 3**, **Stable Diffusion** — text-to-image, image-to-image, inpainting |
| 🎬 **AI Video Generation** | **Kling (via Replicate model integrations)**, **Wan**, **HunyuanVideo** — create videos from prompts or images |
| 🎙️ **AI Audio & Voice** | Music generation, voice cloning, text-to-speech |
| 💬 **AI Chat & LLMs** | **Gemini** for group chat, full LLM support for direct messages |
| 🌐 **Telegram Mini App** | Beautiful in-app web interface — browse models, buy credits, manage settings |
| 👥 **Group Chat Mode** | Add the bot to groups: chat with Gemini, buy credits, set language per group |
| 💳 **Telegram Stars (XTR)** | Native payments — no external payment providers needed |
| 🌍 **Multilingual** | German, English, Russian, Kazakh — full i18n |
| 🔌 **Replicate + OpenAI + Gemini** | Pluggable AI backends, easy to add new models |

---

## 🛠 Tech Stack

- **Bot:** [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- **AI:** [Replicate](https://replicate.com) (Flux, Kling, Hunyuan, etc.), OpenAI (DALL·E), Google Gemini
- **DB:** PostgreSQL ([Neon](https://neon.tech))
- **Web:** Flask, Waitress
- **Deploy:** Render, Railway

---

## 🚀 Quick Start

```bash
git clone https://github.com/alivsch-ai-code/flux-bot-azamat.git
cd flux-bot-azamat

pip install -r requirements.txt

# Create .env (see Configuration below)
cp .env.example .env

python main.py
```

---

## ⚙️ Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_TOKEN` | ✓ | From [@BotFather](https://t.me/BotFather) |
| `REPLICATE_API_TOKEN` | ✓ | From [replicate.com](https://replicate.com) |
| `DATABASE_URL` | ✓ | PostgreSQL connection string (e.g. [Neon](https://neon.tech)) |
| `APP_URL` | (WebApp) | HTTPS base URL for Mini App, e.g. `https://xxx.onrender.com` |
| `OPENAI_API_KEY` | (Optional) | For DALL·E / GPT models |
| `ADMIN_ID` | (Optional) | Telegram user ID for admin commands |
| `REPLICATE_MAX_CONCURRENT` | | Max parallel Replicate requests (default: 1) |

---

## 📁 Project Structure

```
flux-bot-azamat/
├── main.py                 # Entry: Flask + Telegram polling
├── webapp/
│   └── index.html          # Telegram Mini App (shop, settings, model picker)
├── src/
│   ├── application/        # GenerationService, business logic
│   ├── domain/             # Entities, interfaces
│   ├── infrastructure/     # DB, Replicate, OpenAI adapters
│   ├── presentation/       # Telegram handlers, keyboards
│   │   └── telegram/handlers/
│   │       ├── group_handler.py   # Groups: Gemini chat, credits, language
│   │       ├── menu_handler.py    # Menu, settings, WebApp actions
│   │       ├── payment_handler.py # Shop, Telegram Stars invoices
│   │       └── gen/               # Generation, navigation, media
│   ├── config/
│   └── utils/               # i18n strings, validation
└── doc/                     # Deployment guides, architecture
```

---

## 🌐 Menu Modes

| Mode | Description |
|------|-------------|
| `commands` | Classic: `/start`, `/shop` + inline buttons |
| `keyboard` | Reply keyboard with category buttons |
| `webapp` | Telegram Mini App — single UI for everything |

**Admin:** `/set_menu_mode commands|keyboard|webapp`

For WebApp mode, set `APP_URL` and whitelist the domain in [@BotFather](https://t.me/BotFather).

---

## 👥 Group Mode

When added to a **group**:

- **Chat:** Gemini-powered AI chat with a fun, cheeky personality
- **Credits:** Buy via inline buttons → DM with shop
- **Language:** Set DE, EN, RU, KK per group
- **Welcome:** One-time personalized greeting DM (AI-generated) for each new user

---

## 📦 Deployment

- **[Render](doc/render_deploy.md)** — Recommended, web service + health checks
- **[Railway](doc/railway_deploy.md)** — Simple alternative

---

## 📄 License

MIT
