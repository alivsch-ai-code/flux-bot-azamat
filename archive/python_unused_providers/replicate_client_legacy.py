import replicate
import random
import time
from typing import List, Optional
import logging

from replicate.exceptions import ReplicateError

from src.domain.entities import AIModel, GenerationResult, MediaFile
from src.domain.interfaces import AIProvider
from src.infrastructure.ai.dynamic_adapter import DynamicSchemaAdapter
from src.infrastructure.ai.replicate_concurrency import replicate_run_slot
from src.presentation.telegram.handlers.gen.media_helpers import model_requires_image_for_video

logger = logging.getLogger(__name__)


class ReplicateClient(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = replicate.Client(api_token=api_key)
        # Adapter initialisieren
        self.adapter = DynamicSchemaAdapter()

    def generate(
        self,
        model: AIModel,
        prompt: str,
        media_files: Optional[List[MediaFile]] = None,
        **kwargs,
    ) -> GenerationResult:
        file_urls = [mf.path for mf in (media_files or []) if mf.path] if media_files else []

        # 2. Payload bauen via Adapter
        try:
            # model.input_schema ist dank database.py jetzt ein Dict
            inputs = self.adapter.build_input_payload(
                model_schema=model.input_schema,
                user_prompt=prompt,
                file_urls=file_urls,
                **kwargs
            )

            # Image-to-Video-only Modelle (z.B. Kling v1.6 Pro): mind. ein Bild nötig
            if model_requires_image_for_video(model):
                has_img = any(
                    k in inputs and inputs[k]
                    for k in ("start_image", "end_image", "reference_images")
                )
                if not has_img:
                    return GenerationResult(
                        success=False,
                        error="Dieses Modell benötigt ein Startbild (Image-to-Video). Bitte lade zuerst ein Bild hoch.",
                    )

            logger.info("Replicate Request für '%s' vorbereitet", model.key)
            
        except Exception as e:
            return GenerationResult(success=False, error=f"Input Mapping Error: {str(e)}")

        # 3. Execution mit Retry Logic
        max_retries = 3
        base_wait = 2
        
        for attempt in range(max_retries):
            try:
                with replicate_run_slot():
                    output = self.client.run(model.replicate_id, input=inputs)
                
                # Output normalisieren via Adapter
                final_data = self.adapter.parse_output(output, model.output_schema)
                return GenerationResult(success=True, data=final_data)

            except ReplicateError as e:
                if "rate limit" in str(e).lower():
                    wait_time = (base_wait * (2 ** attempt)) + random.uniform(0, 1)
                    logger.warning("Rate Limit! Warte %.1fs...", wait_time)
                    time.sleep(wait_time)
                    continue
                else:
                    # Echter API Fehler
                    return GenerationResult(success=False, error=str(e))
            except Exception as e:
                return GenerationResult(success=False, error=f"System Error: {str(e)}")
        
        return GenerationResult(success=False, error="Max Retries exceeded")