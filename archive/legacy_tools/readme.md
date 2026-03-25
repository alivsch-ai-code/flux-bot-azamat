# 🎛️ AI Bot Model Manager

Dieses Toolset dient dazu, KI-Modelle von Replicate (z.B. Flux, Llama, Video-Modelle) automatisiert abzurufen, in einer Staging-Datenbank zwischenzuspeichern und über ein bequemes Web-Interface für die Live-Produktion freizugeben.

## 📋 Voraussetzungen

Bevor du startest, stelle sicher, dass folgende Dinge eingerichtet sind:

- **Python:** Installiert auf deinem System (Version 3.8+ empfohlen).
- **PostgreSQL:** Eine laufende Datenbank.
- **Umgebungsvariablen:** Im Hauptverzeichnis des Projekts (`flux-bot-azamat`) muss eine `.env` Datei mit mindestens folgenden Schlüsseln liegen:
  ```env
  DATABASE_URL=postgres://dein_user:dein_passwort@dein_host:dein_port/deine_db
  REPLICATE_API_TOKEN=dein_replicate_token
  ```
- **Abhängigkeiten:** Stelle sicher, dass alle nötigen Python-Pakete installiert sind. Du kannst sie in der Regel mit folgendem Befehl installieren:
  ```bash
  pip install streamlit pandas psycopg2-binary replicate python-dotenv
  ```

---

## 🚀 Workflow & Nutzung

### Main GUI (empfohlen)

Alle Aktionen per Klick in einem Browser:

```bash
streamlit run archive/legacy_tools/main_gui.py
```

Dort findest du Buttons für: DB initialisieren, Default-Modelle laden, Approve & Push to Live. Die Admin-GUI zum Bearbeiten startest du separat (siehe unten).

---

### Kommandozeile

Der Prozess besteht aus drei Schritten.
**Wichtig:** Führe alle Befehle aus dem Projekt-Hauptverzeichnis aus. Verwende `python -m archive.legacy_tools.xxx` (nicht `python archive/legacy_tools/xxx.py`), damit die Imports funktionieren.

### Schritt 1: Datenbank initialisieren

Dieser Befehl bereinigt veraltete Tabellen und erstellt die Struktur für `ai_models` (Live) und `ai_models_staging` (Entwurf/Review) komplett neu.
_(Achtung: Dies löscht alle bisherigen Daten in diesen Tabellen!)_

```bash
python -m archive.legacy_tools.init
```

### Schritt 2: Modelle abrufen (Staging Import)

**Default (empfohlen):** Lädt ca. 10 kuratierte Best-of-Modelle (Flux, Kling, Llama, etc.):

```bash
python -m archive.legacy_tools.fetch_advanced
```

**Alternativ:** Breite Suche über Collections & Provider (mehr Modelle):

```bash
python -m archive.legacy_tools.import_staging
```

_Hinweis: Manuelle Änderungen (manual_override) bleiben bei erneuten Importen erhalten._

### Schritt 3: Admin GUI starten

Startet das interaktive Streamlit-Dashboard im Browser. Hier kannst du:

- Die importierten Modelle sichten und bearbeiten (Typ, Menü-Pfad, Credits).
- Modelle für die Produktion markieren (Checkbox "Approve?").
- Mit einem Klick auf "🚀 APPROVE & PUSH TO LIVE" alle markierten Modelle in die Live-Datenbank übertragen.

```bash
streamlit run archive/legacy_tools/admin_gui.py
```

---

## 📂 Dateistruktur (Übersicht)

- **`main_gui.py`**: Haupt-GUI – Ein-Klick-Aktionen für Init, Fetch, Approve. Start: `streamlit run archive/legacy_tools/main_gui.py`
- **`replicate_fetcher.py`**: Zentrales Modul zur Metadaten-Extraktion von Replicate-Modellen (Schema, Typ, `menu_path`, Credits). Wird von allen Import-Tools genutzt.
- **`init.py`**: Baut die PostgreSQL-Tabellenschemata auf (`ai_models` + `ai_models_staging`).
- **`fetch_advanced.py`**: **Default.** Holt 8 Best-of-Modelle (Image, Video, Text) und schreibt ins Staging.
- **`import_staging.py`**: Breite Suche (Collections, Provider, Keywords), mehr Modelle. Behält manuelle Edits (`manual_override`).
- **`admin_gui.py`**: Streamlit-Dashboard zur Bearbeitung und Freigabe.
- **`approve_to_main.py`**: Transfer von Staging (is_approved=1) nach Live.
- **`reclassify_models.py`**: Wendet die verbesserte Klassifikationslogik auf bestehende Modelle an (model_type, menu_path aus Input/Output-Schema).

**Default:** `python -m archive.legacy_tools.fetch_advanced` – schneller Import der Best-of-Modelle.

---

## 🔄 Modell-Klassifikation korrigieren

Nach Änderungen an `replicate_fetcher.py` oder bei falsch zugeordneten Modellen (z.B. Vision-Chat in "Bild" statt "Text"):

```bash
# Staging-Tabelle aktualisieren
python -m archive.legacy_tools.reclassify_models

# Haupt-Tabelle (Live) aktualisieren
python -m archive.legacy_tools.reclassify_models --main
```

**Klassifikation beim Import:** Modelle werden beim Laden von Replicate (`fetch_advanced`, `import_staging`) automatisch korrekt klassifiziert – Output-Typ entscheidet primär (Text→Chat, Bild→Bild Studio). `image_analysis` = Input Bild, Output Text. `img2img` nur wenn Bild-Input Pflicht.
