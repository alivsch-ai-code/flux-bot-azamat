import replicate
import os
from src.domain.interfaces import AIProvider
from src.domain.entities import AIModel, GenerationResult

class ReplicateClient(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = replicate.Client(api_token=api_key)

    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        """
        image_url: Kann eine Web-URL ("https://...") ODER ein lokaler Dateipfad sein.
        """
        try:
            inputs = {"prompt": prompt}
            
            # --- VERBESSERTE LOGIK FÜR BILDER ---
            opened_file = None # Platzhalter, falls wir eine Datei öffnen

            if image_url:
                # Fall A: Es ist eine Web-URL (fängt an mit http)
                if image_url.startswith("http"):
                    inputs['image'] = image_url
                
                # Fall B: Es ist ein lokaler Pfad auf deinem Server (z.B. vom Telegram Download)
                elif os.path.exists(image_url):
                    # WICHTIG: Wir müssen die Datei als 'binary' öffnen
                    opened_file = open(image_url, "rb")
                    inputs['image'] = opened_file
                else:
                    print(f"⚠️ Warnung: Bildpfad '{image_url}' nicht gefunden oder keine URL.")

            # Der eigentliche Call
            print(f"⏳ Sende an Replicate: {model.replicate_id}...")
            output = self.client.run(model.replicate_id, input=inputs)
            
            # Datei wieder schließen, falls wir eine geöffnet haben
            if opened_file:
                opened_file.close()

            # Normalisierung (bleibt gleich)
            result_data = output[0] if isinstance(output, list) else output
            if model.type == "text" and isinstance(output, list):
                result_data = "".join(output)
                
            return GenerationResult(success=True, data=result_data)
            
        except Exception as e:
            # Datei sicherheitshalber schließen im Fehlerfall
            if 'opened_file' in locals() and opened_file:
                opened_file.close()
            print(f"❌ Replicate Error: {e}")
            return GenerationResult(success=False, error=str(e))