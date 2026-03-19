# Menü-Modi & Web-App

## Übersicht

Der Bot unterstützt drei Menü-Modi (Admin: `/set_menu_mode <modus>`):

| Modus     | Beschreibung                                      |
|-----------|---------------------------------------------------|
| `commands`| Standard: /-Menü + Inline-Buttons                 |
| `keyboard`| Tastatur am Eingabefeld + Untermenüs              |
| `webapp`  | Telegram Mini App (HTML/CSS/JS)                   |

## Web-App Modus

Die Mini App ist eine HTML-Oberfläche, die im Telegram-Client geöffnet wird.

### Voraussetzungen

1. **URL – nur HTTPS erlaubt (Telegram-Vorgabe):**
   - **Lokal testen:** [ngrok](https://ngrok.com): `ngrok http 5000` → in `.env`: `APP_URL=https://xxxx.ngrok-free.app`
   - **Render:** `RENDER_EXTERNAL_URL` wird automatisch genutzt – siehe [doc/render_deploy.md](render_deploy.md).
   - **Eigener Server:** `APP_URL=https://deine-domain.de` in `.env`.

2. **Bot neu starten** nach `/set_menu_mode webapp`.

### BotFather – Domain freigeben (oft nötig)

Damit die Web-App geladen wird, muss die Domain für den Bot freigegeben sein:

1. Öffne [@BotFather](https://t.me/BotFather)
2. `/setmenubutton` → deinen Bot wählen
3. „Configure menu button“ → „Configure web app“
4. URL eingeben: `https://deine-domain.de/webapp`  
   (ngrok: `https://xxxx.ngrok-free.app/webapp` | Render: `https://xxx.onrender.com/webapp`)

Ohne diesen Schritt kann es sein, dass die Web-App nicht öffnet (Domain nicht erlaubt). Der Menü-Button wird vom Bot trotzdem gesetzt – die Domain muss aber zuvor in BotFather hinterlegt sein.

### Routen

- `GET /webapp` – Mini App HTML
- `GET /api/models?path=image` – Modelle einer Kategorie (JSON)

## HTML-Formatierung

Bot-Nachrichten nutzen durchgängig HTML (`parse_mode='HTML'`):
- Listen mit • 
- `<b>`, `<i>`, `<code>` für Struktur
- `<a href="">` für Links
