import replicate
import random
import time
from typing import List, Optional

from replicate.exceptions import ReplicateError

from src.domain.entities import AIModel, GenerationResult, MediaFile
from src.domain.interfaces import AIProvider
from src.infrastructure.ai.dynamic_adapter import DynamicSchemaAdapter
from src.infrastructure.ai.replicate_concurrency import replicate_run_slot


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
            print(f"⏳ Replicate Request für '{model.key}': {inputs}")
            
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
                    print(f"⚠️ Rate Limit! Warte {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Echter API Fehler
                    return GenerationResult(success=False, error=str(e))
            except Exception as e:
                return GenerationResult(success=False, error=f"System Error: {str(e)}")
        
        return GenerationResult(success=False, error="Max Retries exceeded")