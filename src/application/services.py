import os
import time
import replicate
from PIL import Image # pip install Pillow nötig
from src.domain.interfaces import UserRepository, AIProvider
from src.domain.entities import AIModel
from src.domain.models import AI_MODELS
from src.infrastructure.ai.replicate.adapters import get_premium_prompts

class GenerationService:
    def __init__(self, repo: UserRepository, ai: AIProvider):
        self.repo = repo
        self.ai = ai

    def process_request(self, user_id: int, model: AIModel, prompt: str, image_url: str = None):
        # 1. User & Credits Check
        user = self.repo.get_user(user_id)
        if user.credits < model.cost:
            return False, "Zu wenig Guthaben! Bitte aufladen."

        # 2. Input Validation (Phase 1) - Einfacher Check
        print(model.type)
        if image_url and os.path.exists(image_url) and model.type != ["image_analysis"]:
            try:
                with Image.open(image_url) as img:
                    width, height = img.size
                    if width < 500 or height < 500:
                        return False, "⚠️ Bildqualität zu niedrig. Bitte lade ein Bild mit mindestens 500px hoch."
            except Exception:
                # Falls es kein Bild ist oder Fehler wirft, ignorieren wir es hier (Soft Fail)
                pass

        # 3. Generierung Starten
        try:
            # --- FALL A: PREMIUM PIPELINE (4 Bilder) ---
            if model.key == "premium-headshot-pipeline":
                success, result_list = self._run_premium_pipeline(prompt, image_url)
                if not success: return False, result_list # Fehlermeldung
                
                # Abrechnung nur bei Erfolg
                self.repo.update_credits(user_id, -model.cost)
                return True, result_list # Gibt eine LISTE von URLs zurück!
            
            # --- FALL B: ULTIMATE PIPELINE (Legacy Einzelbild) ---
            elif model.key == "ultimate-headshot-pipeline":
                success, result_url = self._run_single_pipeline(prompt, image_url)
                if not success: return False, result_url
                self.repo.update_credits(user_id, -model.cost)
                return True, result_url

            # --- FALL C: STANDARD MODELLE ---
            else:
                result = self.ai.generate(model, prompt, image_url)
                if not result.success:
                    return False, f"Fehler: {result.error}"
                
                self.repo.update_credits(user_id, -model.cost)
                return True, result.data

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            return False, f"Systemfehler: {str(e)}"

    def get_balance(self, user_id: int) -> int:
        user = self.repo.get_user(user_id)
        return user.credits

    # --- PRIVATE FUNKTION: DIE PREMIUM SCHLEIFE (4 BILDER) ---
    def _run_premium_pipeline(self, user_prompt: str, user_image_path: str):
        print(f"⚙️ Starte Premium Pipeline für: '{user_prompt}'")

        if not user_image_path or not os.path.exists(user_image_path):
             return False, "Selfie fehlt!"

        # Sub-Modelle laden
        flux_model = AI_MODELS.get("flux-1.1-pro")
        swap_model = AI_MODELS.get("face-swap")
        enhance_model = AI_MODELS.get("face-enhance")

        # 1. Prompts generieren (4 Variationen)
        prompts = get_premium_prompts(user_prompt)
        final_urls = []

        print(f"➡️ Starte Generierung von {len(prompts)} Varianten...")

        # LOOP DURCH DIE 4 SZENARIEN
        for i, specific_prompt in enumerate(prompts):
            print(f"   📸 Variante {i+1}/4 wird erstellt...")
            
            # SCHRITT A: Basis-Bild Generieren
            try:
                # Flux Pro generiert den Anzugträger
                res_base = self.ai.generate(flux_model, specific_prompt, image_url=None)
                if not res_base.success:
                    print(f"Skipping Variant {i+1}: {res_base.error}")
                    continue
                
                # WICHTIG: Ergebnis in String umwandeln
                base_url = str(res_base.data)
                
                # --- RATE LIMIT SCHUTZ ---
                # Wir warten 10 Sekunden, damit Replicate uns nicht blockt (Burst Limit)
                print("      ⏳ Warte 10s auf FaceSwap (Rate Limit Schutz)...")
                time.sleep(10) 

                # SCHRITT B: Face Swap
                # Hier war der Fehler: Variable hieß base_image_url, muss aber base_url heißen!
                output_swap = replicate.run(
                    swap_model.replicate_id,
                    input={
                        "target_image": base_url, # <--- FIX: Hier stand vorher base_image_url
                        "swap_image": open(user_image_path, "rb")
                    }
                )
                
                # URL Extrahieren
                if isinstance(output_swap, list) and len(output_swap) > 0: swap_url = output_swap[0]
                elif isinstance(output_swap, str): swap_url = output_swap
                else: swap_url = str(output_swap)

                # SCHRITT C: Face Enhancer (Optional, falls Augen unscharf)
                # Wir warten kurz, um sicherzugehen
                # time.sleep(2)
                # output_enhance = replicate.run(
                #     enhance_model.replicate_id,
                #     input={"image": swap_url, "codeformer_fidelity": 0.7, "upscale": 1}
                # )
                # if isinstance(output_enhance, list): final_url = output_enhance[0]
                # else: final_url = str(output_enhance)
                
                # Vorerst ohne Enhancer, um Credits/Zeit zu sparen. Swap ist meist gut genug.
                final_url = swap_url
                
                final_urls.append(final_url)
                print(f"      ✅ Variante {i+1} fertig.")

            except Exception as e:
                print(f"⚠️ Fehler bei Variante {i+1}: {e}")
                continue
        
        if len(final_urls) == 0:
            return False, "Generierung fehlgeschlagen (Rate Limit oder Server-Fehler)."
            
        print(f"✅ Premium Pipeline fertig! {len(final_urls)} Bilder generiert.")
        return True, final_urls

    # --- PRIVATE FUNKTION: ALTE EINZEL-PIPELINE (Backup) ---
    def _run_single_pipeline(self, user_prompt: str, user_image_path: str):
        flux_model = AI_MODELS.get("flux-1.1-pro")
        swap_model = AI_MODELS.get("face-swap")
        
        # 1. Gen
        res_step1 = self.ai.generate(flux_model, user_prompt, image_url=None)
        if not res_step1.success: return False, res_step1.error
        base_url = str(res_step1.data)
        
        time.sleep(10) # Safety wait

        # 2. Swap
        try:
            output = replicate.run(
                swap_model.replicate_id,
                input={"target_image": base_url, "swap_image": open(user_image_path, "rb")}
            )
            final_url = output[0] if isinstance(output, list) else str(output)
            return True, final_url
        except Exception as e:
            return False, str(e)