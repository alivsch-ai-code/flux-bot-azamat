import logging
import os
import time
import replicate
from PIL import Image
from typing import List, Optional

from src.domain.entities import AIModel, MediaFile
from src.utils.strings import get_text

logger = logging.getLogger(__name__)
from src.infrastructure.ai.replicate_concurrency import replicate_run_slot
from src.infrastructure.metrics import record_timing
from src.infrastructure.security.validator import InputValidator

class GenerationService:
    """
    Business-Layer zwischen Telegram/WebApp und dem AI-Inferenz-Clients.

    Verantwortlichkeiten:
    - Prompt-Sicherheit (InputValidator)
    - Credits/Abrechnung (User oder Gruppe)
    - Routing nach Modell-Key (Sonder-Pipelines) oder via `UnifiedAIClient` (Standard)
    - Nachlauf: Timings + Fehlerbehandlung

    Wichtig: Diese Klasse kapselt die Logik so, dass Telegram-Handler und
    WebApp/HTTP nur noch "Requests" anfragen, ohne Provider-spezifische Details
    kennen zu müssen (Unified-Prinzip).
    """
    def __init__(self, db_manager, ai_unified_client):
        self.db_manager = db_manager
        self.ai_unified_client = ai_unified_client

    def process_request(
        self,
        user_id: int,
        model: AIModel,
        prompt: str,
        media_files: Optional[List[MediaFile]] = None,
        no_charge: bool = False,
        group_chat_id: Optional[int] = None,
        generation_params: Optional[dict] = None,
        charge_cost: Optional[int] = None,
        lang: str = "en",
    ):
        """
        Verarbeitet eine Generierungsanfrage.

        Rückgabe:
        - `(success: bool, data: str|list|GenerationResult.error)`
        Datenformat hängt vom Modell/Provider ab (z. B. URL, Text, Listen/Iteratoren).
        """
        start = time.perf_counter()
        try:
            # 0) Prompt-Sicherheit & Bereinigung
            validation_result = InputValidator.validateSafetyPromptInput(prompt or "")
            if not validation_result.is_safe:
               #logger.warning("Safety Corruption detected: error=%s", validation_result.reason)
                return False, get_text("gen_service_input_rejected_safety", lang)

            # 0.1) Prompt-Bereinigung
            prompt = InputValidator.sanitize_prompt(prompt or "")

            # 1) Credits-Check (überspringen bei no_charge, z.B. Willkommens-Gruß)
            effective_cost = int(charge_cost if charge_cost is not None else model.cost)

            if not no_charge:
                if group_chat_id is not None:
                    user_credits = self.db_manager.get_effective_credits_for_group(user_id, group_chat_id)
                else:
                    user_credits = self.db_manager.get_user_credits(user_id)
                if user_credits < effective_cost:
                    return False, get_text("gen_service_insufficient_balance", lang)

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
                            return False, get_text("gen_service_image_resolution_low", lang)
                except Exception:
                    pass

            # 3. Routing nach Modelltyp
            def _charge(reason_suffix: str) -> bool:
                if group_chat_id is not None:
                    return self.db_manager.deduct_credits_for_group(user_id, group_chat_id, effective_cost, reason=reason_suffix)
                self.db_manager.update_credits(user_id, -effective_cost, reason=reason_suffix)
                return True  # User-Credits wurden oben bereits geprüft

            if model.key == "premium-headshot-pipeline":
                success, result_list = self._run_premium_pipeline(prompt, first_image_path, lang)
                if not success:
                    return False, result_list
                if not no_charge:
                    if group_chat_id is not None:
                        self.db_manager.deduct_credits_for_group(user_id, group_chat_id, model.cost, reason="premium_pipeline")
                    else:
                        self.db_manager.update_credits(user_id, -model.cost, reason="premium_pipeline")
                return True, result_list

            elif model.key == "ultimate-headshot-pipeline":
                success, result_url = self._run_single_pipeline(prompt, first_image_path, lang)
                if not success:
                    return False, result_url
                if not no_charge:
                    if group_chat_id is not None:
                        self.db_manager.deduct_credits_for_group(user_id, group_chat_id, model.cost, reason="ultimate_pipeline")
                    else:
                        self.db_manager.update_credits(user_id, -model.cost, reason="ultimate_pipeline")
                return True, result_url

            # --- Standard-Modelle (Unified Client) ---
            else:
                result = self.ai_unified_client.generate(
                    model,
                    prompt,
                    media_files=media_files,
                    generation_params=generation_params or {},
                )
                if not result.success:
                    logger.warning("Generation FAILED (no charge): user_id=%s model=%s error=%s", user_id, model.key, result.error)
                    return False, get_text("gen_service_error_prefix", lang) + str(result.error or "")
                if not no_charge and not _charge(f"gen_{model.key}"):
                    return False, get_text("gen_service_insufficient_balance", lang)
                return True, result.data

        except Exception as e:
            logger.exception("CRITICAL ERROR in GenerationService: %s", e)
            return False, get_text("gen_service_system_prefix", lang) + str(e)
        finally:
            record_timing("generation_service.process_request", time.perf_counter() - start)

    # --- PRIVATE FUNKTIONEN ---

    def _run_premium_pipeline(self, user_prompt: str, user_image_path: str, lang: str = "en"):
        """Erstellt 4 Variationen mittels Flux Pro und FaceSwap."""
        logger.info("Starte Premium Pipeline")

        if not user_image_path or not os.path.exists(user_image_path):
            return False, get_text("gen_service_selfie_missing", lang)

        # WICHTIG: Modelle jetzt aus der DB holen statt aus statischem Dict
        flux_model = self.db_manager.get_model_by_key("flux-1.1-pro")
        swap_model = self.db_manager.get_model_by_key("face-swap")
        # enhance_model = self.db_manager.get_model_by_key("face-enhance") # Optional

        if not flux_model or not swap_model:
            return False, get_text("gen_service_internal_config_missing", lang)

        # Prompts generieren (Hardcoded Variationen, um Import-Loop zu vermeiden)
        prompts = [
            f"Professional LinkedIn headshot of a person, wearing a dark blue suit, white shirt, studio lighting, 8k, {user_prompt}",
            f"Business portrait, modern grey blazer, confident look, blurred office background, high quality, {user_prompt}",
            f"Corporate headshot, cinematic lighting, navy suit, professional posture, sharp focus, {user_prompt}",
            f"Close up executive portrait, elegant black suit, neutral background, soft lighting, 4k, {user_prompt}"
        ]
        
        final_urls = []
        logger.info("Starte Generierung von %s Varianten", len(prompts))

        for i, specific_prompt in enumerate(prompts):
            logger.info("Variante %s/4 wird erstellt", i + 1)
            
            try:
                # SCHRITT 1: Basis-Bild mit Flux
                res_base = self.ai_unified_client.generate(flux_model, specific_prompt, media_files=None)
                if not res_base.success:
                    logger.warning("Skipping Variante %s: %s", i + 1, res_base.error)
                    continue
                
                base_url = str(res_base.data)
                
                # Rate Limit Schutz
                logger.debug("Warte 5s auf FaceSwap...")
                time.sleep(5) 

                # SCHRITT 2: Face Swap via Replicate direkt (da Pipeline-Logik spezifisch ist)
                with open(user_image_path, "rb") as swap_image_file:
                    with replicate_run_slot():
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
                logger.info("Variante %s fertig", i + 1)

            except Exception as e:
                logger.warning("Fehler bei Variante %s: %s", i + 1, e)
                continue
        
        if len(final_urls) == 0:
            return False, get_text("gen_service_pipeline_failed", lang)
            
        return True, final_urls

    def _run_single_pipeline(self, user_prompt: str, user_image_path: str, lang: str = "en"):
        """Backup Pipeline für Einzelbilder."""
        # Modelle aus DB laden
        flux_model = self.db_manager.get_model_by_key("flux-1.1-pro")
        swap_model = self.db_manager.get_model_by_key("face-swap")

        if not flux_model or not swap_model:
            return False, get_text("gen_service_models_not_found", lang)
        
        # 1. Bild generieren
        res_step1 = self.ai_unified_client.generate(flux_model, user_prompt, media_files=None)
        if not res_step1.success:
            return False, get_text("gen_service_error_prefix", lang) + str(res_step1.error or "")
        base_url = str(res_step1.data)
        
        time.sleep(5) 

        # 2. Face Swap
        try:
            with open(user_image_path, "rb") as swap_image_file:
                with replicate_run_slot():
                    output = replicate.run(
                        swap_model.replicate_id,
                        input={"target_image": base_url, "swap_image": swap_image_file}
                    )
            final_url = output[0] if isinstance(output, list) else str(output)
            return True, final_url
        except Exception as e:
            return False, get_text("gen_service_system_prefix", lang) + str(e)