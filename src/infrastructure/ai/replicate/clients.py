import replicate
import time
import random # Neu: Zufall, damit nicht alle Threads gleichzeitig hämmern
from replicate.exceptions import ReplicateError
from src.domain.interfaces import AIProvider
from src.domain.entities import AIModel, GenerationResult
from src.infrastructure.ai.replicate.adapters import get_input_params

class ReplicateClient(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = replicate.Client(api_token=api_key)

    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        inputs = {}
        
        # --- EINSTELLUNGEN FÜR MEHR STABILITÄT ---
        max_retries = 5   # Wir versuchen es öfter
        base_wait = 5      # Wir starten direkt mit 4 Sekunden Wartezeit
        
        try:
            inputs = get_input_params(model.replicate_id, prompt, image_url)
            print(f"⏳ Sende an Replicate: {model.replicate_id}...")
            
            # --- RETRY LOOP ---
            for attempt in range(max_retries):
                try:
                    output = self.client.run(model.replicate_id, input=inputs)
                    # Erfolg!
                    print("Erfolg")
                    break 
                    
                except ReplicateError as e:
                    # Prüfen auf Rate Limit (429) oder Server Overload (503)
                    error_msg = str(e).lower()
                    if "429" in error_msg or "throttled" in error_msg or "503" in error_msg:
                        if attempt < max_retries - 1:
                            # Exponentielles Warten + etwas Zufall (Jitter)
                            # Versuch 1: ~4s, Versuch 2: ~8s, Versuch 3: ~16s
                            wait_time = (base_wait * (2 ** attempt)) + random.uniform(0, 1)
                            
                            print(f"⚠️ Rate Limit! Warte {wait_time:.1f}s (Versuch {attempt+1}/{max_retries})...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise e # Aufgeben nach 5 Versuchen
                    else:
                        raise e # Anderer Fehler (z.B. falscher Input)

            # Ergebnis verarbeiten
            result_data = output[0] if isinstance(output, list) else output
            if model.type == "text" and isinstance(output, list):
                result_data = "".join(output)

                
            return GenerationResult(success=True, data=result_data)
            
        except Exception as e:
            print(f"❌ Replicate Error: {e}")
            return GenerationResult(success=False, error=str(e))
            
        finally:
            if inputs:
                for val in inputs.values():
                    if hasattr(val, 'close'): 
                        try: val.close() 
                        except: pass
                    elif isinstance(val, list):
                        for item in val:
                            if hasattr(item, 'close'):
                                try: item.close()
                                except: pass