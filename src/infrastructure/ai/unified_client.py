from src.domain.interfaces import AIProvider
from src.domain.entities import AIModel, GenerationResult
from src.infrastructure.ai.replicate_client import ReplicateClient
from src.infrastructure.ai.sonauto_client import SonautoClient

class UnifiedAIClient(AIProvider):
    """
    Dieser Client entscheidet anhand des Modells, welcher echte Provider
    (Replicate oder Sonauto) benutzt wird.
    """
    def __init__(self, replicate_key: str, sonauto_key: str):
        self.replicate = ReplicateClient(replicate_key)
        self.sonauto = SonautoClient(sonauto_key)

    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        
        # Die Weiche:
        if model.provider == "sonauto":
            return self.sonauto.generate(model, prompt, image_url)
        
        elif model.provider == "replicate":
            return self.replicate.generate(model, prompt, image_url)
            
        else:
            return GenerationResult(success=False, error=f"Unbekannter Provider: {model.provider}")