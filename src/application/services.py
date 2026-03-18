import os
import time
import replicate
from PIL import Image
from typing import List, Optional

from src.domain.entities import AIModel, GenerationResult, MediaFile
from src.infrastructure.security.validator import InputValidator

class GenerationService:
    def __init__(self, repo, ai):
        self.repo = repo  # Das ist der DatabaseManager
        self.ai = ai      # Das ist der UnifiedAIClient

    def process_request(
        self,
        user_id: int,
        model: AIModel,
        prompt: str,
        media_files: Optional[List[MediaFile]] = None,
    ):
        # 0. Prompt-Sicherheit & Bereinigung
        if not InputValidator.validate_safety(prompt or ""):
            return False, "⚠️ Deine Eingabe wurde aus Sicherheitsgründen abgelehnt."
        prompt = InputValidator.sanitize_prompt(prompt or "")

        # 1. User & Credits Check
        user_credits = self.repo.get_user_credits(user_id)
        if user_credits < model.cost:
            return False, "Zu wenig Guthaben! Bitte aufladen."

        # Erste Bild-Datei für Pipelines (Backward-Kompatibilität)
        first_image_path = None
        if media_files:
            for mf in media_files:
                if mf.media_type.value == "image" and mf.path and os.path.exists(mf.path):
                    first_image_path = mf.path
                    break

        # 2. Input Validation (Bildgröße Check für erste Bild-Datei)
        if first_image_path and "image_analysis" not in (model.type or []):
            try:
                with Image.open(first_image_path) as img:
                    width, height = img.size
                    if width < 500 or height < 500:
                        return False, "⚠️ Bildqualität zu niedrig. Bitte lade ein Bild mit mindestens 500px hoch."
            except Exception:
                pass

        try:
            if model.key == "premium-headshot-pipeline":
                success, result_list = self._run_premium_pipeline(prompt, first_image_path)
                
                if not success: 
                    return False, result_list # Fehlermeldung zurückgeben
                
                # Abrechnung nur bei Erfolg
                self.repo.update_credits(user_id, -model.cost, reason="premium_pipeline")
                return True, result_list # Gibt eine LISTE von URLs zurück!
            
            # --- FALL B: ULTIMATE PIPELINE (Legacy Einzelbild) ---
            elif model.key == "ultimate-headshot-pipeline":
                success, result_url = self._run_single_pipeline(prompt, first_image_path)
                if not success: 
                    return False, result_url
                
                self.repo.update_credits(user_id, -model.cost, reason="ultimate_pipeline")
                return True, result_url

            # --- FALL C: STANDARD MODELLE (Via Unified Client) ---
            else:
                result = self.ai.generate(model, prompt, media_files=media_files)
                if not result.success:
                    return False, f"Fehler: {result.error}"
                
                self.repo.update_credits(user_id, -model.cost, reason=f"gen_{model.key}")
                return True, result.data

        except Exception as e:
            print(f"CRITICAL ERROR in Service: {e}")
            return False, f"Systemfehler: {str(e)}"

    # --- PRIVATE FUNKTIONEN ---

    def _run_premium_pipeline(self, user_prompt: str, user_image_path: str):
        """Erstellt 4 Variationen mittels Flux Pro und FaceSwap."""
        print(f"⚙️ Starte Premium Pipeline für: '{user_prompt}'")

        if not user_image_path or not os.path.exists(user_image_path):
            return False, "Selfie für Face-Swap fehlt!"

        # WICHTIG: Modelle jetzt aus der DB holen statt aus statischem Dict
        flux_model = self.repo.get_model_by_key("flux-1.1-pro")
        swap_model = self.repo.get_model_by_key("face-swap")
        # enhance_model = self.repo.get_model_by_key("face-enhance") # Optional

        if not flux_model or not swap_model:
            return False, "Interne Konfiguration fehlt (Hilfsmodelle nicht in DB)."

        # Prompts generieren (Hardcoded Variationen, um Import-Loop zu vermeiden)
        prompts = [
            f"Professional LinkedIn headshot of a person, wearing a dark blue suit, white shirt, studio lighting, 8k, {user_prompt}",
            f"Business portrait, modern grey blazer, confident look, blurred office background, high quality, {user_prompt}",
            f"Corporate headshot, cinematic lighting, navy suit, professional posture, sharp focus, {user_prompt}",
            f"Close up executive portrait, elegant black suit, neutral background, soft lighting, 4k, {user_prompt}"
        ]
        
        final_urls = []
        print(f"➡️ Starte Generierung von {len(prompts)} Varianten...")

        for i, specific_prompt in enumerate(prompts):
            print(f"   📸 Variante {i+1}/4 wird erstellt...")
            
            try:
                # SCHRITT 1: Basis-Bild mit Flux
                res_base = self.ai.generate(flux_model, specific_prompt, image_url=None)
                if not res_base.success:
                    print(f"Skipping Variant {i+1}: {res_base.error}")
                    continue
                
                base_url = str(res_base.data)
                
                # Rate Limit Schutz
                print("      ⏳ Warte 5s auf FaceSwap...")
                time.sleep(5) 

                # SCHRITT 2: Face Swap via Replicate direkt (da Pipeline-Logik spezifisch ist)
                with open(user_image_path, "rb") as swap_image_file:
                    output_swap = replicate.run(
                        swap_model.replicate_id,
                        input={
                            "target_image": base_url,
                            "swap_image": swap_image_file
                        }
                    )
                
                # Ergebnis normalisieren
                if isinstance(output_swap, list) and len(output_swap) > 0: 
                    swap_url = output_swap[0]
                elif isinstance(output_swap, str): 
                    swap_url = output_swap
                else: 
                    swap_url = str(output_swap)

                final_urls.append(swap_url)
                print(f"      ✅ Variante {i+1} fertig.")

            except Exception as e:
                print(f"⚠️ Fehler bei Variante {i+1}: {e}")
                continue
        
        if len(final_urls) == 0:
            return False, "Generierung fehlgeschlagen."
            
        return True, final_urls

    def _run_single_pipeline(self, user_prompt: str, user_image_path: str):
        """Backup Pipeline für Einzelbilder."""
        # Modelle aus DB laden
        flux_model = self.repo.get_model_by_key("flux-1.1-pro")
        swap_model = self.repo.get_model_by_key("face-swap")

        if not flux_model or not swap_model:
            return False, "Modelle nicht gefunden."
        
        # 1. Bild generieren
        res_step1 = self.ai.generate(flux_model, user_prompt, image_url=None)
        if not res_step1.success: return False, res_step1.error
        base_url = str(res_step1.data)
        
        time.sleep(5) 

        # 2. Face Swap
        try:
            with open(user_image_path, "rb") as swap_image_file:
                output = replicate.run(
                    swap_model.replicate_id,
                    input={"target_image": base_url, "swap_image": swap_image_file}
                )
            final_url = output[0] if isinstance(output, list) else str(output)
            return True, final_url
        except Exception as e:
            return False, str(e)