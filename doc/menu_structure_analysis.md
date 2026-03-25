# Menü-Struktur – Analyse & Empfehlungen

Stand: März 2025

## 1. Aktuelle Struktur

### 1.1 Kategorien (menu_path)

| Pfad   | Anzeige (DE)    | Inhalt                                          |
|--------|-----------------|-------------------------------------------------|
| `image` | 🎨 Bild Studio  | txt2img, img2img, Fill, Depth, Canny, Redux     |
| `video` | 🎬 Video Studio | Kling, Hunyuan, Veo, Sora, Minimax, Ray, Wan    |
| `audio` | 🎙️ Audio Studio | Bark, MusicGen, Whisper, Stable Audio           |
| `text`  | 📝 Text / Chat  | GPT, Claude, Gemini, Llama, DeepSeek, Grok      |
| `tools` | 🛠️ Werkzeuge   | Remove-BG, ESRGAN (Upscale)                     |

### 1.2 Modell-Typen (model_type)

| Typ            | Bedeutung                                    | menu_path typisch |
|----------------|----------------------------------------------|-------------------|
| `image`        | Output ist Bild                              | image             |
| `image,img2img`| Braucht Bild-Input, Output Bild              | image, tools      |
| `text`         | Output ist Text (Chat)                       | text              |
| `text,image_analysis` | Vision: Bild-Input, Text-Output      | text              |
| `video`        | Output ist Video                             | video             |
| `audio`        | Output ist Audio                             | audio             |
| `upscale`      | Bild verbessern                              | tools             |

**Wichtig:** Der **Output-Typ** entscheidet über die Menü-Kategorie. So landen Vision-Modelle (GPT-4o, Claude mit Bild) in „Text / Chat“, nicht in „Bild Studio“.

---

## 2. Korrekte Klassifikation (replicate_fetcher)

Die Klassifikation nutzt nun **Input- und Output-Schema**:

- **Output Text** (array/iterator) + Input hat optional Bild → `text, image_analysis`, menu_path `text`
- **Output Bild** (URI/FileOutput) + Input nur Prompt → `image`, menu_path `image` (txt2img)
- **Output Bild** + Input braucht Bild → `image, img2img`, menu_path `image` oder `tools`

Damit werden z.B. Claude Sonnet, GPT-4o, Gemini korrekt unter „Text / Chat“ einsortiert.

---

## 3. UI-Komponenten

| Komponente                 | Quelle                      | Kategorien                                      |
|----------------------------|-----------------------------|-------------------------------------------------|
| Inline-Menü (commands)     | `keyboards.get_dynamic_model_menu` | Aus DB: menu_path pro Modell          |
| Reply-Keyboard             | `keyboards.get_main_reply_keyboard`| Fix: Bild, Video, Audio, Text, Tools  |
| Web-App                    | React `/webapp`              | Fix: gleiche 5 Karten                           |
| API `/api/models`          | `main.py`                   | path=root → Subkategorien, path=X → Modelle     |

---

## 4. Mögliche Erweiterungen

### 4.1 Unterkategorien (optional)

Aktuell flach: `image`, `video`, …  
Mögliche Erweiterung mit Unterordnern:

- `image/flux` – Flux-Modelle
- `image/tools` – Remove-BG, Upscale
- `text/chat` – reine Chat-Modelle
- `text/vision` – Vision (Bild beschreiben)

Die Logik in `keyboards.py` und `main.py` unterstützt bereits `menu_path` mit `/` (z.B. `image/flux`).

### 4.2 Reihenfolge der Kategorien

Aktuell: Bild, Video, Audio, Text, Tools.  
Alternativ: Text zuerst (Chat als Haupteinstieg), dann Medien.

### 4.3 Tool „Bild beschreiben“

Für `image_analysis`-Modelle könnte ein eigener Einstieg „🔍 Bild beschreiben“ in Text oder Tools sinnvoll sein. Aktuell erscheinen sie in „Text / Chat“.

---

## 5. Reclassify nach Anpassungen

Bestehende DB-Modelle neu klassifizieren (z.B. nach Änderungen an `replicate_fetcher`):

```bash
python -m src.tools.reclassify_models --main
```

Neue Modelle werden beim Import von Replicate automatisch korrekt klassifiziert.
