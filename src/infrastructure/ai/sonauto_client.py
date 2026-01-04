import requests
import time
import json
from src.domain.interfaces import AIProvider
from src.domain.entities import AIModel, GenerationResult

class SonautoClient(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.sonauto.ai/v1/generations" 

    def generate(self, model: AIModel, prompt: str, image_url: str = None) -> GenerationResult:
        if not self.api_key:
            return GenerationResult(success=False, error="Sonauto API Key fehlt.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Payload anpassen (Instrumental/Lyrics Steuerung kann hier erweitert werden)
        payload = {
            "prompt": prompt,
            "instrumental": False,
        }

        try:
            print(f"🎵 Starte Sonauto Request: {prompt[:30]}...")
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            # --- DEBUG INFO ---
            # print(f"Init Response: {response.text}") 
            
            if response.status_code not in [200, 201]:
                return GenerationResult(success=False, error=f"API Error {response.status_code}: {response.text}")

            data = response.json()
            
            # ID holen
            task_id = data.get("task_id") or data.get("id")
            
            if task_id:
                print(f"⏳ Task ID {task_id} erhalten. Warte auf Fertigstellung...")
                return self._poll_result(task_id, headers)
            
            return GenerationResult(success=False, error="Keine task_id erhalten.")

        except Exception as e:
            return GenerationResult(success=False, error=str(e))

    def _poll_result(self, task_id, headers):
        check_url = f"{self.api_url}/{task_id}" 
        
        # Wir erhöhen auf 45 Durchläufe à 2 Sekunden = 90 Sekunden Timeout
        for i in range(45): 
            try:
                resp = requests.get(check_url, headers=headers)
                if resp.status_code == 200:
                    res_data = resp.json()
                    
                    # --- FIX: Status normalisieren (alles in Großbuchstaben umwandeln) ---
                    raw_status = res_data.get("status", "").upper()
                    
                    # Nur alle 5 Durchläufe oder bei Änderung printen, damit die Konsole sauber bleibt
                    if i % 5 == 0: 
                        print(f"   ... Status: {raw_status}")

                    # --- FIX: Auch "SUCCESS" akzeptieren ---
                    if raw_status in ["COMPLETED", "SUCCEEDED", "SUCCESS"]:
                        
                        # --- FIX: URL Suche verbessern (basierend auf Screenshot "Song Paths") ---
                        # Wir drucken einmal das ganze Ergebnis, damit wir es 100% sicher sehen
                        print(f"✅ Status SUCCESS! Analysiere Antwort...")
                        # print(json.dumps(res_data, indent=2)) # <--- Kannst du einkommentieren zum Debuggen

                        final_url = None
                        
                        # Strategie 1: Es ist direkt eine URL
                        if res_data.get("audio_url"): 
                            final_url = res_data.get("audio_url")
                        
                        # Strategie 2: Es ist eine Liste von "song_paths" (wie im Screenshot)
                        elif res_data.get("song_paths") and len(res_data["song_paths"]) > 0:
                            final_url = res_data["song_paths"][0]
                            
                        # Strategie 3: Fallback auf allgemeine URL
                        elif res_data.get("url"):
                            final_url = res_data.get("url")

                        if final_url:
                            # Falls die URL relativ ist (beginnt nicht mit http), Domain davor setzen
                            if not final_url.startswith("http"):
                                final_url = "https://sonauto.ai" + final_url # Annahme, ggf. anpassen
                            
                            print(f"🎉 Song fertig: {final_url}")
                            return GenerationResult(success=True, data=final_url)
                        else:
                            print("❌ Status SUCCESS, aber keine URL gefunden. Raw Data:")
                            print(json.dumps(res_data, indent=2))
                            return GenerationResult(success=False, error="URL nicht im JSON gefunden")

                    elif raw_status == "FAILED":
                         return GenerationResult(success=False, error=f"Generation failed: {res_data}")
                
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ Polling Fehler: {e}")
                time.sleep(2)
        
        return GenerationResult(success=False, error="Timeout: Song wurde nicht fertig.")