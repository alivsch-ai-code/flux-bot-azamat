# src/infrastructure/ai/unified_client.py
from src.domain.interfaces import AIProvider
from src.domain.entities import AIModel, GenerationResult

# Imports der Clients
from src.infrastructure.ai.replicate.clients import ReplicateClient
from src.infrastructure.ai.sonauto_client import SonautoClient
from src.infrastructure.ai.kling_client import KlingClient
from src.infrastructure.ai.openai_compatible_client import OpenAICompatibleClient

class UnifiedAIClient():
    def __init__(self, settings):
        # Wir übergeben hier das ganze Settings-Objekt, das ist sauberer
        self.replicate = ReplicateClient(settings.REPLICATE_API_TOKEN)
        
        # Optionale Clients initialisieren (nur wenn Key da ist)
        self.sonauto = SonautoClient(settings.SONAUTO_API_KEY) if settings.SONAUTO_API_KEY else None
        self.kling = KlingClient(settings.KLING_API_KEY) if settings.KLING_API_KEY else None
        
        # LLM Clients
        self.openai = OpenAICompatibleClient(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
        # Grok (xAI) Base URL: https://api.x.ai/v1
        self.grok = OpenAICompatibleClient(settings.GROK_API_KEY, base_url="https://api.x.ai/v1") if settings.GROK_API_KEY else None
        
        # DeepSeek Base URL: https://api.deepseek.com
        self.deepseek = OpenAICompatibleClient(settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com") if settings.DEEPSEEK_API_KEY else None


    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        
        # --- REPLICATE (Standard) ---
        if model.provider == "replicate":
            return self.replicate.generate(model, prompt, image_url)
            
        # --- SONAUTO (Musik) ---
        elif model.provider == "sonauto":
            if not self.sonauto: return GenerationResult(False, "Sonauto API Key fehlt.")
            return self.sonauto.generate(model, prompt, image_url)

        # --- KLING AI (Video) ---
        elif model.provider == "kling":
            if not self.kling: return GenerationResult(False, "Kling API Key fehlt.")
            return self.kling.generate(model, prompt, image_url)

        # --- OPENAI (DALL-E / GPT) ---
        elif model.provider == "openai":
            if not self.openai: return GenerationResult(False, "OpenAI API Key fehlt.")
            return self.openai.generate(model, prompt, image_url)

        # --- GROK (xAI) ---
        elif model.provider == "grok":
            if not self.grok: return GenerationResult(False, "Grok API Key fehlt.")
            return self.grok.generate(model, prompt, image_url)

        # --- DEEPSEEK ---
        elif model.provider == "deepseek":
            if not self.deepseek: return GenerationResult(False, "DeepSeek API Key fehlt.")
            return self.deepseek.generate(model, prompt, image_url)
            
        else:
            return GenerationResult(success=False, error=f"Unbekannter Provider: {model.provider}")