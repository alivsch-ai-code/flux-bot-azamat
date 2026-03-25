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
| ⏱️ **Chat message batching** | Private & group text chat: debounced replies (20s → 10s → 5s → 10s; flush on 5th message) so bursts get one coherent answer |
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

**Daily News (DB):** Optional `daily_posts` rows by date. `message_text` can be a single HTML string or JSON `{"de":"…","en":"…","ru":"…","kk":"…"}` for per-user language. Example: `python tools/seed_daily_alexa_plus_tomorrow.py` (requires `DATABASE_URL`).

---

## 🛡️ Ops & Security Notes
- Flask/WebApp: bei unerwarteten Fehlern geben APIs an Clients nur `error="internal_error"` zurück; die Details stehen in den Server-Logs.
- CI: GitHub Actions testet jetzt mit Python **3.12**.
- DB: `DatabaseManager` sorgt zuverlässig dafür, dass Connections auch bei Exceptions wieder an den Pool zurückgegeben werden (verhindert Pool-„Lecks“ im Fehlerfall).

---

## 📁 Project Structure

```
flux-bot-azamat/
├── main.py                 # Entry: Flask + Telegram polling
├── webapp-react/           # Vite + React Mini App (build → dist/, served under /webapp)
├── archive/                # Unused providers + legacy operator tools (see archive/README.md)
├── src/
│   ├── application/        # GenerationService, business logic
│   ├── domain/             # Entities, interfaces
│   ├── infrastructure/     # DB, Replicate, OpenAI adapters
│   ├── presentation/       # Telegram handlers, HTTP routes (Mini-App API), keyboards
│   │   ├── http/           # Flask routes for /webapp and /api/*
│   │   └── telegram/handlers/
│   │       ├── group_handler.py   # Groups: Gemini chat, credits, language
│   │       ├── chat_debounce.py   # Batched text chat (timers, flush callback)
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
- **Burst replies:** Multiple quick messages are merged: wait 20s after the first, then shorter windows after each new line (10s / 5s / 10s); the **5th message in a row** forces an immediate reply that addresses the whole batch (same behavior in private text chat mode)

---

## 📋 Use cases

| Scenario | What happens |
|----------|----------------|
| **Creative generation** | User picks image/video/audio model → sends prompt (and optional media) → Stars are charged → result is delivered in chat. |
| **Private LLM chat** | User enables chat for a text model or sends plain text from the home screen → history is stored (with periodic summarization) → answers respect the full thread; rapid multi-line typing is batched (see Group Mode). |
| **Mini App** | User opens the Web App from the menu → browses models, buys packages, changes settings; actions call the Flask API with signed `init_data`. |
| **Group collaboration** | Members talk to AZAMAT; each burst is one API call; credits use group-aware rules on the paying user. |
| **Ops / admin** | Switch menu mode, reload models, optional cheat/test flows — see code and `ADMIN_ID`. |

For a **German, detailed** breakdown (handlers, HTTP routes, `GenerationService`, debounce API), see **[doc/use_cases_und_schnittstellen.md](doc/use_cases_und_schnittstellen.md)**.

---

## 🔌 Interfaces (overview)

| Layer | Interface | Notes |
|-------|-----------|--------|
| **Telegram** | pyTelegramBotAPI handlers | Order: `group_handler` → `menu_handler` → `payment_handler` → `gen_handler`. Group text is **not** handled by `prompt_handlers` (early return). |
| **HTTP** | Flask in `main.py` + `src/presentation/http/http_routes.py` | `/webapp`, `/api/*` — see doc above. |
| **Application** | `GenerationService.process_request(...)` | Credits, validation, routing by model type, Replicate/OpenAI/Gemini via `UnifiedAIClient`. |
| **Domain** | `UserRepository`, `AIProvider` in `src/domain/interfaces.py` | Contracts; `DatabaseManager` + adapters implement behavior. |
| **Chat batching** | `schedule_batched_text_message`, `cancel_pending_batch` | `src/presentation/telegram/handlers/chat_debounce.py` |

---

## 📦 Deployment

- **[Render](doc/render_deploy.md)** — Recommended, web service + health checks
- **[Railway](doc/railway_deploy.md)** — Simple alternative

---

## 📄 License

MIT
