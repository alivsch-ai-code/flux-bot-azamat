"""
Zentraler Einstieg für Modell-Inferenz: **ein** Client pro App (`UnifiedAIClient`).

Alle aktiven Provider (Replicate, OpenAI, Grok, Platzhalter Kling/DeepSeek) werden hier
verdrahtet. Ältere, eigenständige `AIProvider`-Klassen (z. B. `ReplicateClient`, Kling,
Sonauto) liegen unter `archive/python_unused_providers/` und sind nicht eingebunden.

**Replicate (Predictions)** — siehe offizielle Doku:
https://replicate.com/docs/topics/predictions/create-a-prediction

- Drei Wege, Predictions anzulegen: Community (`POST /v1/predictions` + `version`),
  Official Models (`POST /v1/models/{owner}/{name}/predictions`), Deployments
  (`deployments.predictions.create`).
- **Sync-Modus:** HTTP-Header `Prefer: wait` (optional `wait=<Sekunden>`); Verbindung
  bleibt offen, Response enthält bei Abschluss `output`. Default-Wartezeit i. d. R. 60 s;
  wenn die Zeit nicht reicht: Prediction-Objekt mit Status wie `starting`/`processing`,
  Ergebnis per Poll (`GET` auf `urls.get`) oder Webhook nachziehen.
- **Async (API-Default ohne `Prefer: wait`):** sofortige Antwort mit Prediction-ID;
  Fertigstellung per Webhook oder Polling (wie in der Doku beschrieben).
  **Wir nutzen diesen reinen HTTP-Async-Modus hier nicht:** kein `wait=False` und keine
  Webhook-gestützte Prediction — stattdessen Sync wie unten.
- **Deadline:** optionaler Header `Cancel-After` (z. B. `5m`) — wir setzen ihn hier
  nicht; Lifecycle/Timeouts: https://replicate.com/docs/topics/predictions/lifecycle

Unser Aufruf `replicate.run(...)` nutzt das Python-SDK mit Default `wait=True` → **Sync**
(`Prefer: wait`); bei nicht-terminaler Antwort pollt das SDK intern weiter. Das ist nicht
derselbe Modus wie der API-Default „async create + später holen“.

**Rate limits (Server-seitig bei Replicate):**
https://replicate.com/docs/topics/predictions/rate-limits

- u. a. **600 Creates/Minute** für Predictions; **3000/Minute** für andere Endpunkte;
  kurze Bursts darüber sind möglich, danach Throttling.
- Bei wenig Guthaben verschärfte Limits; Antwort typisch **HTTP 429** mit Text wie
  „throttled“ / „rate limit“.
- Spezialfall: gewährter Credit ohne Zahlungsmittel → sehr niedrige Limits (Doku).

**Unser Code:** kein zentraler 429-Retry im `UnifiedAIClient` — Fehler gehen als Text nach
oben. Parallelität begrenzen wir mit `REPLICATE_MAX_CONCURRENT` (Semaphore), siehe
`replicate_concurrency.py`. Im Telegram-`runner` gibt es **Retries bei erkanntem
Rate-Limit** (`is_rate_limit`, Pause ~20 s, bis zu 4 Versuche).
"""
import logging
import os
import time
from typing import Any, List, Optional

import replicate
from openai import OpenAI

from src.domain.entities import AIModel, GenerationResult, MediaFile
from src.infrastructure.ai.dynamic_adapter import DynamicSchemaAdapter
from src.infrastructure.ai.replicate_concurrency import replicate_run_slot

logger = logging.getLogger(__name__)

# Replicate-hosted Anthropic: zu hohe max_tokens-Werte führen zu API-Fehlern; harte Obergrenze.
ANTHROPIC_REPLICATE_MAX_TOKENS = 4000


def _is_anthropic_replicate_model(model) -> bool:
    rid = (getattr(model, "replicate_id", None) or "").lower()
    key = (getattr(model, "key", None) or "").lower()
    return "anthropic" in rid or "anthropic" in key


def _cap_max_tokens_for_anthropic(model, input_data: dict) -> None:
    if not _is_anthropic_replicate_model(model) or not isinstance(input_data, dict):
        return
    if "max_tokens" not in input_data:
        return
    raw = input_data["max_tokens"]
    try:
        mt = int(raw)
    except (TypeError, ValueError):
        return
    if mt > ANTHROPIC_REPLICATE_MAX_TOKENS:
        input_data["max_tokens"] = ANTHROPIC_REPLICATE_MAX_TOKENS


def _is_http_url(s: str) -> bool:
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))


def _replicate_prefer_wait_seconds() -> int:
    """SDK erlaubt ``wait`` als int nur 1–60 s (Prefer-Header); größere Werte clampen."""
    try:
        w = int(os.getenv("REPLICATE_PREFER_WAIT_SECONDS", "60"))
    except (TypeError, ValueError):
        w = 60
    return max(1, min(60, w))


def _collect_replicate_iterator_chunks(output: Any, log: logging.Logger) -> list:
    """
    SDK liefert bei manchen Modellen einen Iterator (Polling/Streaming). ``list(output)``
    kann ohne Grenze hängen, wenn der Status nie terminal wird — daher Deadline + Char-Cap.
    """
    try:
        max_sec = float(os.getenv("REPLICATE_OUTPUT_COLLECT_MAX_SEC", "600"))
    except (TypeError, ValueError):
        max_sec = 600.0
    max_sec = max(1.0, min(max_sec, 3600.0))
    try:
        max_chars = int(os.getenv("REPLICATE_STREAM_MAX_CHARS", "500000"))
    except (TypeError, ValueError):
        max_chars = 500_000
    max_chars = max(10_000, min(max_chars, 2_000_000))

    deadline = time.monotonic() + max_sec
    chunks: list = []
    total_chars = 0
    it = iter(output)
    while True:
        if time.monotonic() > deadline:
            log.warning(
                "Replicate-Iterator: Sammel-Timeout nach %.0fs (%s Teile, %s Zeichen)",
                max_sec,
                len(chunks),
                total_chars,
            )
            raise TimeoutError("replicate_output_collect_timeout")
        try:
            chunk = next(it)
        except StopIteration:
            break
        chunks.append(chunk)
        total_chars += len(str(chunk))
        if total_chars >= max_chars:
            log.warning(
                "Replicate-Iterator: REPLICATE_STREAM_MAX_CHARS (%s) erreicht, breche ab",
                max_chars,
            )
            break
    return chunks


def _coerce_generation_param_value(prop: dict, value: Any) -> Any:
    """
    Striktes, aber pragmatisches Coercion gegen JSON-Schema-Property.
    Wir akzeptieren nur Werte, die nach Coercion zum erwarteten Typ/Enum passen.
    """
    if not isinstance(prop, dict):
        return value
    expected_type = str(prop.get("type", "") or "").strip().lower()
    enum_vals = prop.get("enum")
    if isinstance(enum_vals, list) and enum_vals:
        # Enum streng: nur erlaubte Werte; Stringvergleich tolerant.
        for ev in enum_vals:
            if value == ev:
                return value
            if isinstance(value, str) and str(ev) == value:
                return ev
        return None

    if expected_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("true", "1", "yes", "on"):
                return True
            if v in ("false", "0", "no", "off"):
                return False
        return None
    if expected_type == "integer":
        try:
            # bool ausschließen, da int(True)==1
            if isinstance(value, bool):
                return None
            return int(value)
        except Exception:
            return None
    if expected_type == "number":
        try:
            if isinstance(value, bool):
                return None
            return float(value)
        except Exception:
            return None
    if expected_type == "array":
        if isinstance(value, list):
            return value
        return None
    if expected_type == "string":
        if isinstance(value, str):
            return value
        # numerische/bool Werte als String zulassen wenn Schema string erwartet.
        if isinstance(value, (int, float, bool)):
            return str(value)
        return None
    # Kein/anderer Typ im Schema: Originalwert übernehmen.
    return value


def _local_paths_to_urls(paths: List[str], client) -> List[str]:
    """
    Konvertiert lokale Dateipfade zu URIs für Replicate (format: uri).
    - HTTP(S)-URLs bleiben unverändert.
    - Upload via Replicate Files API (damit Replicate-Input-Felder wie `format: uri`
      zuverlässig eine echte URL bekommen und nicht an `data:`-URIs scheitern).

    Input-Dateien / URLs: https://replicate.com/docs/topics/predictions/input-files
    """
    urls = []
    for p in paths or []:
        if _is_http_url(p):
            urls.append(p)
        elif os.path.isfile(p):
            try:
                with open(p, "rb") as f:
                    content = f.read()
                ext = os.path.splitext(p)[1].lower() or ".jpg"
                if ext in [".jpg", ".jpeg"]:
                    mime = "image/jpeg"
                elif ext == ".png":
                    mime = "image/png"
                elif ext == ".webp":
                    mime = "image/webp"
                elif ext in [".mp4", ".m4v"]:
                    mime = "video/mp4"
                elif ext == ".mov":
                    mime = "video/quicktime"
                elif ext == ".webm":
                    mime = "video/webm"
                elif ext == ".avi":
                    mime = "video/x-msvideo"
                elif ext == ".mkv":
                    mime = "video/x-matroska"
                elif ext == ".mp3":
                    mime = "audio/mpeg"
                elif ext == ".wav":
                    mime = "audio/wav"
                elif ext in [".m4a", ".aac"]:
                    mime = "audio/aac"
                elif ext == ".ogg":
                    mime = "audio/ogg"
                elif ext == ".flac":
                    mime = "audio/flac"
                else:
                    mime = "application/octet-stream"
                import io

                fn = os.path.basename(p) or "image.jpg"
                # replicate SDK verlangt hier zwingend `file=`.
                resp = client.files.create(file=io.BytesIO(content), filename=fn, type=mime)
                url = getattr(resp, "url", None)
                if not url and hasattr(resp, "urls") and isinstance(resp.urls, dict):
                    url = resp.urls.get("get")
                if url:
                    urls.append(url)
                else:
                    # Letzter Fallback: data:-URI. Falls Replicate das ebenfalls ablehnt,
                    # wäre es besser, vorher zu garantieren, dass Upload immer eine URL liefert.
                    import base64
                    b64 = base64.b64encode(content).decode("ascii")
                    urls.append(f"data:{mime};base64,{b64}")
            except Exception:
                # Notfalls originalen Pfad weiterreichen; kann beim Provider validierungsfehlschlagen.
                # Aber: vorherige Bugs zeigen, dass `data:`/non-URI Werte hier problematisch sind.
                urls.append(p)
        else:
            urls.append(p)
    return urls


def _first_image_path(media_files: Optional[List[MediaFile]]) -> Optional[str]:
    if not media_files:
        return None
    for mf in media_files:
        if mf.media_type.value == "image" and mf.path and os.path.exists(mf.path):
            return mf.path
    return None


# Nur Typen, die ausschließlich Text/Bild (inkl. Bildanalyse) sind → HTTP/Sync (replicate.run).
# Video, Audio, gemischte oder unbekannte Typen → async Prediction + Webhook.
_HTTP_REPLICATE_TYPES = frozenset({"text", "image", "image_analysis"})


def replicate_model_types_allow_http(model: AIModel) -> bool:
    types = set(model.type or [])
    if not types:
        return True
    return types.issubset(_HTTP_REPLICATE_TYPES)


def replicate_should_use_webhook(model: AIModel) -> bool:
    return model.provider == "replicate" and not replicate_model_types_allow_http(model)


def replicate_webhook_delivery_configured(config) -> bool:
    url = (getattr(config, "APP_URL", None) or "").strip()
    secret = (getattr(config, "REPLICATE_WEBHOOK_SIGNING_SECRET", None) or "").strip()
    return url.startswith("https://") and bool(secret)


def is_replicate_webhook_pending_result(result) -> bool:
    return isinstance(result, dict) and result.get("__replicate_webhook__") is True


def make_replicate_webhook_pending_result(prediction_id: str) -> dict:
    return {"__replicate_webhook__": True, "prediction_id": prediction_id}


class UnifiedAIClient:
    """
    UnifiedAIClient ist der einzige aktive Inferenz-Einstieg für die App.

    Design:
    - Provider-spezifisches Wissen (Replicate/OpenAI/etc.) ist hier gebündelt.
    - Telegram/WebApp ruft nur `generate(model, prompt, media_files, generation_params)` auf.
    - Falls künftig neue Provider hinzukommen: Implementierung hier ergänzen und
      die Zuordnung (model.provider) sicherstellen.

    Hinweis:
    - Bisherige eigenständige Provider-Clients sind als Referenz archiviert
      (siehe `archive/python_unused_providers/`) und werden nicht importiert.
    """
    def __init__(self, config):
        self.config = config
        self.schema_adapter = DynamicSchemaAdapter()
        # OpenAI Client initialisieren (falls Key vorhanden)
        self.openai_client = None
        if config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            
        # Hier könnten weitere Clients (Grok, DeepSeek) folgen
        self.grok_client = None
        if config.GROK_API_KEY:
            self.grok_client = OpenAI(
                api_key=config.GROK_API_KEY, 
                base_url="https://api.x.ai/v1"
            )

    def generate(
        self,
        model: AIModel,
        prompt: str,
        media_files: Optional[List[MediaFile]] = None,
        generation_params: Optional[dict] = None,
    ) -> GenerationResult:
        """
        Verteilt die Anfrage an den richtigen Provider.

        Erwartung:
        - `model.provider` bestimmt den Provider-Typ.
        - `model.input_schema` (falls vorhanden) steuert die Eingabe-Mapping-Logik über
          `DynamicSchemaAdapter`.
        - `generation_params` kommt aus der WebApp (z. B. duration/resolution) und wird
          optional in das Provider-Input gemappt.
        """
        logger.info("UnifiedClient startet Request für %s (Provider: %s)", model.name, model.provider)
        
        try:
            # --- 1. REPLICATE ---
            if model.provider == "replicate":
                return self._run_replicate(model, prompt, media_files, generation_params=generation_params or {})

            elif model.provider == "openai":
                img_path = _first_image_path(media_files)
                return self._run_openai(model, prompt, img_path)
            
            elif model.provider == "kling":
                img_path = _first_image_path(media_files)
                return self._run_kling(model, prompt, img_path)

            # --- 4. GROK (xAI) ---
            elif model.provider == "grok":
                return self._run_openai_compatible(self.grok_client, model, prompt, "grok-beta")

            # --- 5. DEEPSEEK ---
            elif model.provider == "deepseek":
                # DeepSeek ist oft OpenAI-kompatibel via Base URL
                return GenerationResult(success=False, error="DeepSeek Integration coming soon.")

            else:
                return GenerationResult(success=False, error=f"Unbekannter Provider: {model.provider}")

        except Exception as e:
            logger.exception("API Error (%s): %s", model.provider, e)
            return GenerationResult(success=False, error=str(e))

    # --- PROVIDER IMPLEMENTIERUNGEN ---

    def build_replicate_input_dict(
        self,
        model: AIModel,
        prompt: str,
        media_files: Optional[List[MediaFile]] = None,
        generation_params: Optional[dict] = None,
    ) -> dict:
        """Baut das Replicate-``input``-Objekt (ohne Prediction anzulegen)."""
        gp = generation_params or {}
        file_paths = [mf.path for mf in (media_files or []) if mf.path] if media_files else []
        file_urls = file_paths
        if file_paths and any(not _is_http_url(p) for p in file_paths):
            client = replicate.Client(api_token=self.config.REPLICATE_API_TOKEN)
            file_urls = _local_paths_to_urls(file_paths, client)
        if model.input_schema and isinstance(model.input_schema, dict):
            input_data = self.schema_adapter.build_input_payload(
                model_schema=model.input_schema,
                user_prompt=prompt,
                file_urls=file_urls if file_urls else None,
            )
        else:
            input_data = {"prompt": prompt}
            if file_urls:
                input_data["image"] = file_urls[0]
        if "flux" in model.key and "aspect_ratio" not in input_data:
            input_data["aspect_ratio"] = "16:9"
            input_data["safety_tolerance"] = 5
        if "minimax" in (model.key or ""):
            input_data["prompt_optimizer"] = True
        if isinstance(gp, dict):
            schema_props = {}
            if isinstance(model.input_schema, dict):
                schema_props = model.input_schema.get("properties") or {}
            for k, v in gp.items():
                if v is None:
                    continue
                if k == "prompt":
                    continue
                if isinstance(v, list) and not v:
                    continue
                if isinstance(v, str) and v.strip() == "":
                    continue
                # Strikt: nur Keys erlauben, die im Schema existieren.
                if not isinstance(schema_props, dict) or k not in schema_props:
                    continue
                coerced = _coerce_generation_param_value(schema_props.get(k) or {}, v)
                if coerced is None:
                    continue
                input_data[k] = coerced
        _cap_max_tokens_for_anthropic(model, input_data)
        return input_data

    def create_replicate_prediction_with_webhook(self, model: AIModel, input_data: dict, webhook_url: str) -> str:
        """
        Async-Modus: Prediction ohne ``Prefer: wait``, Abschluss per Webhook.
        https://replicate.com/docs/topics/predictions/create-a-prediction
        https://replicate.com/docs/topics/webhooks
        """
        from replicate import identifier as rid

        client = replicate.Client(api_token=self.config.REPLICATE_API_TOKEN)
        ref = model.replicate_id
        try:
            _, owner, name, version_id = rid._resolve(ref)
        except Exception:
            owner, name, version_id = None, None, None
        kw = dict(
            input=input_data,
            webhook=webhook_url,
            webhook_events_filter=["completed"],
            wait=False,
        )
        if owner and name:
            pred = client.models.predictions.create(model=f"{owner}/{name}", **kw)
        elif version_id:
            pred = client.predictions.create(version=version_id, **kw)
        else:
            pred = client.predictions.create(version=ref, **kw)
        return pred.id

    def _run_replicate(self, model, prompt, media_files, generation_params=None):
        """
        Führt ein Replicate-Modell aus.

        `model.replicate_id` im Format ``owner/name`` (Official Model) führt im SDK zu
        ``models.predictions.create`` — ``POST .../v1/models/{owner}/{name}/predictions``.
        Eine Version-Hash-Referenz nutzt stattdessen ``POST /v1/predictions`` mit
        ``version`` (Community-Modelle), siehe:
        https://replicate.com/docs/topics/predictions/create-a-prediction

        ``replicate.run(ref, input=...)`` wartet standardmäßig auf das Ergebnis
        (SDK-Default ``wait=True`` ≈ Sync mit ``Prefer: wait``; bei Bedarf internes
        Polling). Alternative in der API: rein asynchron + Webhook oder manuelles
        Pollen auf ``urls.get``.
        """
        gp = generation_params or {}
        types_set = set(model.type or [])
        # Nur reine Text-Modelle: rohes ``prediction.output`` statt FileOutput-Wrapper (s. replicate.run).
        use_file_output = not (types_set and types_set.issubset({"text"}))
        wait_s = _replicate_prefer_wait_seconds()
        with replicate_run_slot():
            input_data = self.build_replicate_input_dict(model, prompt, media_files, gp)
            # ``wait=60``: maximale erste Prefer-wait-Phase (SDK-Doku); danach pollt das SDK weiter.
            output = replicate.run(
                model.replicate_id,
                input=input_data,
                wait=wait_s,
                use_file_output=use_file_output,
            )

            return self.normalize_replicate_output(output)

    def normalize_replicate_output(self, output):
        # FileOutput/Objekte mit .url erhalten – URL und read() für result_delivery verfügbar.
        # Text-Modelle liefern dagegen oft Listen/Iteratoren von Strings → komplett zusammenfügen.
        if hasattr(output, "url"):
            return GenerationResult(success=True, data=output)

        # Listen-Ausgabe
        if isinstance(output, list):
            if not output:
                return GenerationResult(success=True, data="")
            # Bilder/Media: komplette Liste behalten (z. B. Multi-Image/Multi-Asset Outputs).
            if any(hasattr(item, "url") for item in output):
                return GenerationResult(success=True, data=output)
            # Text: alle Teile zusammenfügen
            return GenerationResult(success=True, data="".join(str(x) for x in output))

        # Reiner String
        if isinstance(output, str):
            return GenerationResult(success=True, data=output)

        # Generator / Iterator (z.B. Streaming-Text)
        if hasattr(output, "__iter__") and not isinstance(output, (str, bytes)):
            try:
                collected = _collect_replicate_iterator_chunks(output, logger)
                if collected and any(hasattr(item, "url") for item in collected):
                    return GenerationResult(success=True, data=collected)
                return GenerationResult(success=True, data="".join(str(x) for x in collected))
            except TimeoutError:
                return GenerationResult(
                    success=False,
                    error="Replicate-Ausgabe-Iterator: Timeout beim Sammeln (replicate_output_collect_timeout).",
                )
            except (TypeError, StopIteration):
                pass

        # Fallback: alles in String gießen
        return GenerationResult(success=True, data=str(output))

    def _normalize_replicate_output(self, output):
        return self.normalize_replicate_output(output)

    def _run_openai(self, model, prompt, image_url):
        if not self.openai_client:
            return GenerationResult(success=False, error="OPENAI_API_KEY fehlt in .env")

        # A) BILDER (DALL-E)
        if "image" in model.type:
            response = self.openai_client.images.generate(
                model="dall-e-3", # Modell ID aus model.replicate_id nehmen wenn variabel
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            return GenerationResult(success=True, data=response.data[0].url)

        # B) TEXT (GPT-4o)
        else:
            messages = [{"role": "user", "content": prompt}]
            # Falls Bild-Analyse gewünscht (GPT-4 Vision)
            if image_url: 
                # OpenAI braucht Bild-URLs im Message Content (komplexer), 
                # hier vereinfacht für reinen Text-Chat
                pass 
                
            response = self.openai_client.chat.completions.create(
                model=model.replicate_id, # z.B. "gpt-4o"
                messages=messages
            )
            return GenerationResult(success=True, data=response.choices[0].message.content)

    def _run_openai_compatible(self, client, model, prompt, model_name):
        """Für Grok, DeepSeek etc."""
        if not client:
            return GenerationResult(success=False, error=f"{model.provider.upper()}_API_KEY fehlt.")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return GenerationResult(success=True, data=response.choices[0].message.content)

    def _run_kling(self, model, prompt, image_url):
        # Placeholder für Kling API
        # Kling hat eine asynchrone API (Task ID -> Polling)
        # Das hier ist nur ein Dummy, da echte Implementierung komplexer ist (Callback nötig)
        return GenerationResult(success=False, error="Kling API Integration benötigt Webhook/Polling (noch nicht aktiv).")