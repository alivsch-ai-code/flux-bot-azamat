import os
import replicate
from typing import List, Optional
import logging

from openai import OpenAI

from src.domain.entities import AIModel, GenerationResult, MediaFile
from src.infrastructure.ai.dynamic_adapter import DynamicSchemaAdapter
from src.infrastructure.ai.replicate_concurrency import replicate_run_slot

logger = logging.getLogger(__name__)


def _is_http_url(s: str) -> bool:
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))


def _local_paths_to_urls(paths: List[str], client) -> List[str]:
    """
    Konvertiert lokale Dateipfade zu URIs für Replicate (format: uri).
    - HTTP(S)-URLs bleiben unverändert.
    - Upload via Replicate Files API (damit Replicate-Input-Felder wie `format: uri`
      zuverlässig eine echte URL bekommen und nicht an `data:`-URIs scheitern).
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
                mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "application/octet-stream"
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


class UnifiedAIClient:
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
        Verteilt die Anfrage an den richtigen Provider (Replicate, OpenAI, Kling etc.)
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

    def _run_replicate(self, model, prompt, media_files, generation_params=None):
        with replicate_run_slot():
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
            # Optional model runtime params coming from WebApp.
            if isinstance(generation_params, dict):
                for k, v in generation_params.items():
                    if v is None:
                        continue
                    # prompt wird ausschließlich aus Chat/Prompt-Flow gesetzt
                    if k == "prompt":
                        continue
                    # Leere Listen/Strings nicht überschreiben
                    if isinstance(v, list) and not v:
                        continue
                    if isinstance(v, str) and v.strip() == "":
                        continue
                    input_data[k] = v
            output = replicate.run(model.replicate_id, input=input_data)

            return self._normalize_replicate_output(output)

    def _normalize_replicate_output(self, output):
        # FileOutput/Objekte mit .url erhalten – URL und read() für result_delivery verfügbar.
        # Text-Modelle liefern dagegen oft Listen/Iteratoren von Strings → komplett zusammenfügen.
        if hasattr(output, "url"):
            return GenerationResult(success=True, data=output)

        # Listen-Ausgabe
        if isinstance(output, list):
            if not output:
                return GenerationResult(success=True, data="")
            first = output[0]
            # Bilder/Media: erste URL / FileOutput
            if hasattr(first, "url"):
                return GenerationResult(success=True, data=first)
            # Text: alle Teile zusammenfügen
            return GenerationResult(success=True, data="".join(str(x) for x in output))

        # Reiner String
        if isinstance(output, str):
            return GenerationResult(success=True, data=output)

        # Generator / Iterator (z.B. Streaming-Text)
        if hasattr(output, "__iter__") and not isinstance(output, (str, bytes)):
            try:
                collected = list(output)
                if collected and hasattr(collected[0], "url"):
                    return GenerationResult(success=True, data=collected[0])
                return GenerationResult(success=True, data="".join(str(x) for x in collected))
            except (TypeError, StopIteration):
                pass

        # Fallback: alles in String gießen
        return GenerationResult(success=True, data=str(output))

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