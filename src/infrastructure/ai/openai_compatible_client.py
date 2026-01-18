from openai import OpenAI
from src.domain.interfaces import AIProvider
from src.domain.entities import AIModel, GenerationResult

class OpenAICompatibleClient(AIProvider):
    def __init__(self, api_key: str, base_url: str = None):
        # Wenn base_url None ist, nutzt er automatisch standard OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        try:
            # UNTERSCHEIDUNG: BILD ODER TEXT
            if "image" in model.type:
                # DALL-E Logic
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                return GenerationResult(success=True, data=response.data[0].url)

            else:
                # Chat Logic (Grok, DeepSeek, GPT)
                # Das 'model.replicate_id' feld nutzen wir hier als Modell-Namen für die API
                response = self.client.chat.completions.create(
                    model=model.replicate_id, 
                    messages=[{"role": "user", "content": prompt}]
                )
                return GenerationResult(success=True, data=response.choices[0].message.content)

        except Exception as e:
            return GenerationResult(success=False, error=f"LLM Error: {str(e)}")