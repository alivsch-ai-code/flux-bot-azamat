# Broadcast-Kanäle & Daily News

Dieses Dokument beschreibt, wie **Telegram-Broadcast-Kanäle** (Channels) für **Azamat Daily News** und Metadaten in der **gleichen Neon-Datenbank** (`DATABASE_URL`) registriert werden. Technische Umsetzung: [`menu_register_impl.py`](../src/presentation/telegram/handlers/menu_register_impl.py) (`DailyService` in [`daily_services.py`](../src/application/daily_services.py), Tabelle `telegram_channels` in [`database.py`](../src/infrastructure/database.py)).

---

## 1. Überblick

| Thema | Beschreibung |
|--------|----------------|
| **Speicherort** | Tabelle `telegram_channels` in derselben PostgreSQL-Instanz wie `DATABASE_URL` (keine zweite DB-URL). |
| **Wer darf Befehle im Kanal?** | Nur der in `ADMIN_ID` konfigurierte Telegram-User. |
| **Bot im Kanal** | Der Bot sollte **Administrator** sein, damit er Posts empfängt und Antworten senden kann. |
| **Telegram-Updates** | Beiträge im Kanal kommen als **`channel_post`**, nicht als normale Chat-`message`. Die Handler sind für beides registriert. |

---

## 2. Befehle im Broadcast-Kanal

Diese Befehle **im Kanal selbst** schreiben (nicht im Privatchat mit dem Bot).

### 2.1 `/azamat_take_channel_as_group`

- **Zweck:** Channel in `telegram_channels` + `group_settings` eintragen (Sprache wie bei Gruppen, `treat_as_group`).
- **Syntax:**  
  `/azamat_take_channel_as_group`  
  oder mit Sprache:  
  `/azamat_take_channel_as_group de` · `en` · `ru` · `kk`
- **Daily News:** Automatischer Versand in den Kanal **noch nicht** aktiv — dafür Schritt 2.2.

### 2.2 `/azamat_post_daily`

- **Zweck:** `receive_daily_news` für diesen Kanal aktivieren **und** sofort einen Daily-News-Lauf nur für diesen Kanal auslösen.
- **Syntax:** `/azamat_post_daily` (ohne Parameter; Sprache kommt aus `group_settings`).

### 2.3 Absender (wichtig)

Telegram liefert bei Kanal-Posts oft nur dann einen **Nutzer-Absender** (`from_user`), wenn der Beitrag **mit sichtbarem Profil** geschrieben wird. Poste den Befehl so, dass **dein Nutzerprofil** als Autor erscheint — nicht nur der Kanalname ohne Person.  
Sonst kann der Bot nicht prüfen, ob du `ADMIN_ID` bist, und antwortet mit einer entsprechenden Hinweisnachricht.

---

## 3. Admin-Befehle im Privatchat (optional)

| Befehl | Zweck |
|--------|--------|
| `/track_channel -1001234567890 [de\|en\|ru\|kk]` | Negative `chat_id` manuell eintragen (inkl. `group_settings`). |
| `/tracked_channels` | Liste der in `group_settings` getrackten Gruppen (negative IDs) + Einträge aus `telegram_channels`. |

Nutzer: nur sinnvoll für den **Admin** (`ADMIN_ID`); genaue Prüfung siehe Code in `menu_register_impl.py`.

---

## 4. Konfiguration (`.env`)

| Variable | Rolle |
|----------|--------|
| `DATABASE_URL` | **Pflicht** für Persistenz von `telegram_channels` und Gruppeneinstellungen. |
| `ADMIN_ID` | **Pflicht** für die Kanal-Befehle oben — Abgleich mit `message.from_user.id`. |

---

## 5. Fehlerdiagnose

| Symptom | Mögliche Ursache |
|---------|------------------|
| Gar keine Reaktion (vor Fix) | Nur `message`-Handler ohne `channel_post` — sollte im aktuellen Stand behoben sein. |
| Hinweis „kein Nutzer-Absender“ | Post nur als Kanal ohne sichtbares Profil — siehe Abschnitt 2.3. |
| „Nur Bot-Admin“ | Deine User-ID ≠ `ADMIN_ID`. |
| DB-Fehlermeldung | `DATABASE_URL` fehlt oder Pool nicht erreichbar. |

---

## 6. Verwandte Dokumentation

- [README](../README.md) — Konfiguration, Deploy
- [use_cases_und_schnittstellen.md](use_cases_und_schnittstellen.md) — Handler-Überblick
