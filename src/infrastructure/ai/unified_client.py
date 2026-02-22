import os
import replicate
import time
from openai import OpenAI # pip install openai
from src.domain.entities import AIModel, GenerationResult
from src.config.settings import config

class UnifiedAIClient:
    def __init__(self, config):
        self.config = config
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

    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        """
        Verteilt die Anfrage an den richtigen Provider (Replicate, OpenAI, Kling etc.)
        """
        print(f"⏳ UnifiedClient: Starte Request für {model.name} (Provider: {model.provider})...")
        
        try:
            # --- 1. REPLICATE ---
            if model.provider == "replicate":
                return self._run_replicate(model, prompt, image_url)
            
            # --- 2. OPENAI (GPT & DALL-E) ---
            elif model.provider == "openai":
                return self._run_openai(model, prompt, image_url)
            
            # --- 3. KLING AI (Video) ---
            elif model.provider == "kling":
                return self._run_kling(model, prompt, image_url)

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
            print(f"❌ API Error ({model.provider}): {e}")
            return GenerationResult(success=False, error=str(e))

    # --- PROVIDER IMPLEMENTIERUNGEN ---

    def _run_replicate(self, model, prompt, image_url):
        input_data = {"prompt": prompt}
        
        # Bild-Input Logik
        if image_url:
            # Manche Modelle nennen es 'image', andere 'input_image'
            if "image_to_image" in model.type or "upscale" in model.type:
                input_data["image"] = image_url
            else:
                input_data["image"] = image_url
        
        # Parameter je nach Modell-Typ anpassen
        if "flux" in model.key:
            input_data["aspect_ratio"] = "16:9"
            input_data["safety_tolerance"] = 5
        
        if "minimax" in model.key:
             input_data["prompt_optimizer"] = True

        print(f"   🚀 Sende an Replicate: {model.replicate_id}")
        output = replicate.run(model.replicate_id, input=input_data)
        
        # Ergebnis normalisieren (Replicate gibt oft Listen zurück)
        if isinstance(output, list) and len(output) > 0:
            return GenerationResult(success=True, data=output[0])
        elif isinstance(output, str): # Stream URL oder Text
             return GenerationResult(success=True, data=output)
        # Manche Modelle geben Generatoren zurück
        elif hasattr(output, '__iter__'): 
            return GenerationResult(success=True, data="".join([str(x) for x in output]))
            
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