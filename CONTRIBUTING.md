# Contributing to AZAMAT AI Hub

Thanks for your interest in contributing! This guide gets you from clone to merged PR.

## Development setup

```bash
git clone https://github.com/alivsch-ai-code/flux-bot-azamat.git
cd flux-bot-azamat
pip install -r requirements.txt
cp .env.example .env   # fill in TELEGRAM_TOKEN, REPLICATE_API_TOKEN, DATABASE_URL
python main.py
```

Python **3.10+** is required (CI runs on 3.12). A free [Neon](https://neon.tech) database works for development.

## Project layout

The codebase follows a clean architecture split — keep new code in the right layer:

| Layer | Path | What belongs here |
|-------|------|-------------------|
| Presentation | `src/presentation/` | Telegram handlers, Flask routes, keyboards |
| Application | `src/application/` | Business logic (`GenerationService`, daily services) |
| Domain | `src/domain/` | Entities and interfaces — no external dependencies |
| Infrastructure | `src/infrastructure/` | Database, Replicate/OpenAI/Gemini adapters, security |

Architecture details: [doc/architecture.md](doc/architecture.md)

## Before you open a PR

1. **Run the tests** — all of them must pass:
   ```bash
   python -m pytest tests/ -q
   ```
2. **Run the linter:**
   ```bash
   ruff check src/ tests/ main.py
   ```
3. **Add tests** for new behavior. Database code is tested against an in-memory repo (see `tests/support/`).
4. Keep PRs focused — one topic per PR is easier to review than a grab bag.

## Conventions

- Database access goes through `DatabaseManager` and always uses the `_connection()` context manager — never leave a connection without guaranteed release.
- SQL uses parameterized queries (`%s` placeholders), never f-string interpolation of user data.
- User-facing strings live in `src/utils/strings.py` and must be added for all four languages (DE, EN, RU, KK).
- Errors shown to users stay generic; details belong in the server logs.

## Reporting bugs

Open an issue with: what you did, what you expected, what happened instead, and relevant log output (with tokens redacted).
