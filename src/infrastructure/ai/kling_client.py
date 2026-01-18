import time
import requests
import jwt # pip install pyjwt
from src.domain.interfaces import AIProvider
from src.domain.entities import AIModel, GenerationResult

class KlingClient(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Kling nutzt JWT Tokens, die man aus dem Key generieren muss, 
        # ODER (neuerdings) direkt Bearer Tokens. Wir nehmen hier den Standard Access Token Weg.
        self.base_url = "https://api.klingai.com/v1"

    def _get_headers(self):
        # HINWEIS: Kling hat eine spezifische Auth-Methode. 
        # Oft ist es ein "Bearer <TOKEN>". 
        # Checke die Doku, ob du den API Key direkt nutzen kannst oder einen Token generieren musst.
        # Für dieses Beispiel nehmen wir an, der API Key ist direkt der Bearer Token.
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        url = f"{self.base_url}/videos/text2video"
        
        payload = {
            "model": "kling-v1",
            "prompt": prompt,
            "cfg_scale": 0.5,
            "mode": "std",
            "aspect_ratio": "16:9"
        }
        
        # Falls Image-to-Video gewünscht ist:
        if image_url:
            url = f"{self.base_url}/videos/image2video"
            payload["image"] = image_url # Muss eine URL sein
            del payload["prompt"] # Bei Image2Video oft optional oder anders benannt

        try:
            # 1. Start Task
            resp = requests.post(url, json=payload, headers=self._get_headers())
            if resp.status_code != 200:
                return GenerationResult(success=False, error=f"Kling Error: {resp.text}")
            
            data = resp.json()
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return GenerationResult(success=False, error="Keine Task ID von Kling erhalten.")

            # 2. Polling (Warten auf Ergebnis)
            return self._poll_result(task_id)

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    def _poll_result(self, task_id):
        check_url = f"{self.base_url}/videos/text2video/{task_id}"
        
        for _ in range(60): # 5 Minuten Timeout (60 * 5s)
            try:
                resp = requests.get(check_url, headers=self._get_headers())
                data = resp.json().get("data", {})
                status = data.get("task_status")

                if status == "succeeded":
                    video_url = data["task_result"]["videos"][0]["url"]
                    return GenerationResult(success=True, data=video_url)
                
                elif status == "failed":
                    return GenerationResult(success=False, error=f"Kling Generation failed: {data.get('task_status_msg')}")
                
                time.sleep(5)
            except Exception as e:
                print(f"Polling Error: {e}")
                time.sleep(5)

        return GenerationResult(success=False, error="Timeout bei Kling AI")