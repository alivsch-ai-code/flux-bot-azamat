# Performance & Security Hardening (2026-04)

## Ziel

- WebApp auf mobilen Geräten schneller und stabiler machen.
- Schutz gegen Massenanfragen / einfache DDoS-Bursts auf API-Ebene.
- Bestehende Features nicht brechen.

## Umgesetzte Maßnahmen

### 1) API Rate Limiting (Flask, in-memory)

Datei: `src/presentation/http/http_routes.py`

- Globales IP-Limit auf `/api/*` innerhalb eines Zeitfensters.
- Schärferes IP-Limit für teure Endpunkte:
  - `/api/webapp_action`
  - `/api/webapp_upload_reference`
  - `/api/user_info`
  - `/api/model`
  - `/api/models`
- Zusätzlich User-basiertes Limit (nach `init_data`-Validierung) für:
  - `webapp_action`
  - `user_info`
  - Upload-Endpunkt
- Bei Überschreitung: `429` + `Retry-After`.

Konfigurierbare ENV-Variablen:

- `HTTP_RATE_LIMIT_WINDOW_SECONDS` (default `10`)
- `HTTP_RATE_LIMIT_MAX_REQUESTS_PER_IP` (default `180`)
- `HTTP_RATE_LIMIT_MAX_REQUESTS_PER_IP_HEAVY` (default `50`)
- `HTTP_RATE_LIMIT_MAX_REQUESTS_PER_USER` (default `45`)

### 2) Schnellere WebApp-Auslieferung

Datei: `src/presentation/http/http_routes.py`

- Für hash-basierte Assets unter `/webapp/assets/*`:
  - `Cache-Control: public, max-age=31536000, immutable`

Effekt:

- Deutlich schnelleres Wiederladen im Telegram-WebView.
- Reduziert Last auf Flask/Waitress bei wiederkehrenden Nutzern.

### 3) UX/Speed-Basics (bereits integriert)

- Fokus-/Keyboard-Verbesserungen in Kachelansichten.
- Mobile 1-Spalten-Grid für kleine Displays.
- Build-Parsing-Fix in CSS (sauberer Build ohne alte CSS-Warnung).

## Verifikation

- Voller Pytest-Lauf grün.
- Zusätzlicher Test für Rate-Limit-Kernlogik:
  - `tests/test_http_rate_limit.py`
- WebApp-Build (`vite`) erfolgreich.

## Offene nächste Schritte (optional)

- Redis-basiertes Rate Limiting (prozessübergreifend) statt In-Memory.
- CDN vor Flask für statische Assets.
- Serverseitige Response-Compression/Brotli.
- Request-Signaturen/Nonce für besonders sensitive Endpunkte.

