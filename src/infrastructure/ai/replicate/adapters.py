import os
import random

# --- PROMPT VORLAGEN FÜR VARIATION ---
def get_premium_prompts(user_prompt):
    """
    Erzeugt 4 Variationen basierend auf dem Geschlecht im User-Prompt.
    """
    # 1. Geschlecht und Basis ermitteln
    p_lower = user_prompt.lower()
    if "mann" in p_lower or "man" in p_lower or "male" in p_lower:
        subject = "handsome professional businessman"
        attire = "dark navy tailored italian suit, crisp white shirt, silk tie"
    elif "frau" in p_lower or "woman" in p_lower or "female" in p_lower:
        subject = "beautiful professional businesswoman"
        attire = "modern dark business blazer, white blouse, elegant necklace"
    else:
        # Fallback
        subject = "professional corporate person"
        attire = "modern dark business suit, white shirt"

    # 2. Die 4 Szenarien (Variationen)
    scenarios = [
        "bright modern office background with window light", # 1. Hell & Modern
        "neutral grey studio background, professional lighting", # 2. Klassisch Studio
        "blurred corporate office depth of field background", # 3. Corporate Bokeh
        "dark navy textured studio background, dramatic lighting" # 4. Seriös & Kontrastreich
    ]

    # 3. Prompts bauen
    prompts = []
    for bg in scenarios:
        final_p = (
            f"Medium shot, professional headshot of a {subject}, wearing {attire}, "
            f"looking confidently directly at camera, friendly slight smile, "
            f"{bg}, "
            "soft studio lighting, 8k uhd, sharp focus, canon r5, 85mm lens, f/1.8, "
            "photorealistic, high detail skin texture, no artifacts."
        )
        prompts.append(final_p)
    
    return prompts


# --- ADAPTER FÜR FLUX PRO (Basis-Gen) ---
# FIX: Hier fehlte "image_url=None". Jetzt akzeptiert er das 2. Argument!
def prepare_flux_base_input(full_prompt: str, image_url: str = None):
    return {
        "prompt": full_prompt,
        "aspect_ratio": "3:4", # Headshot Standard
        "output_format": "jpg",
        "safety_tolerance": 2
    }

# --- STANDARD ADAPTER (Bleiben erhalten) ---
def prepare_standard_input(prompt: str, image_url: str = None):
    inputs = {}
    if prompt and prompt != "Upscaling...": inputs["prompt"] = prompt
    if image_url:
        if image_url.startswith("http"): inputs['image'] = image_url
        elif os.path.exists(image_url): inputs['image'] = open(image_url, "rb")
    return inputs

def prepare_upscale_esrgan_input(prompt: str, image_url: str = None):
    inputs = {"scale": 4, "face_enhance": True}
    if image_url and os.path.exists(image_url): inputs['image'] = open(image_url, "rb")
    return inputs

def prepare_gemini_input(prompt: str, image_url: str = None):
    inputs = {"prompt": prompt, "aspect_ratio": "match_input_image", "output_format": "jpg"}
    if image_url:
        if image_url.startswith("http"): inputs['image_input'] = [image_url]
        elif os.path.exists(image_url): inputs['image_input'] = [open(image_url, "rb")]
    return inputs

def prepare_gemini_flash(prompt: str, image_url: str = None):
    # Basis-Inputs gemäß deinem JSON-Beispiel
    inputs = {
        "top_p": 0.95,
        "images": [], # Initialisiere als leere Liste
        "prompt": prompt,
        "videos": [],  # Auch videos scheinen laut JSON erwartet zu werden
        "temperature": 1,
        "dynamic_thinking": False,
        "max_output_tokens": 65535,
    }

    if image_url:
        if image_url.startswith("http"):
            # Fügt die URL der Liste hinzu
            inputs['images'] = [image_url]
        elif os.path.exists(image_url):
            # Fügt das geöffnete Datei-Objekt der Liste hinzu
            inputs['images'] = [open(image_url, "rb")]
            
    return inputs

def prepare_gemini_flash_image(prompt: str, image_url: str = None):
    # Basis-Inputs gemäß deinem JSON-Beispiel
    inputs = {
        "prompt": prompt,
        "image_input": [], # Initialisiere als leere Liste
        "aspect_ration": "match_input_image",
        "output_format": "jpg"
    }

    if image_url:
        if image_url.startswith("http"):
            # Fügt die URL der Liste hinzu
            inputs['image_input'] = [image_url]
        elif os.path.exists(image_url):
            # Fügt das geöffnete Datei-Objekt der Liste hinzu
            inputs['image_input'] = [open(image_url, "rb")]
            
    return inputs

def prepare_minimax_input(prompt: str, image_url: str = None):
    inputs = {"prompt": prompt, "prompt_optimizer": True}
    if image_url:
        if image_url.startswith("http"): inputs['first_frame_image'] = image_url
        elif os.path.exists(image_url): inputs['first_frame_image'] = open(image_url, "rb")
    return inputs

# --- MAPPING ---
MODEL_ADAPTERS = {
    "black-forest-labs/flux-1.1-pro": prepare_flux_base_input,
    "nightmareai/real-esrgan": prepare_upscale_esrgan_input,
    "google/gemini-2.5-flash-image": prepare_gemini_flash_image,
    "google/gemini-2.5-flash": prepare_gemini_flash,
    "google/nano-banana": prepare_gemini_input,
    "google/nano-banana-pro": prepare_gemini_input,
    "minimax/video-01": prepare_minimax_input,
}

def get_input_params(model_id: str, prompt: str, image_url: str = None):
    clean_model_id = model_id.split(":")[0]
    adapter_func = MODEL_ADAPTERS.get(clean_model_id)
    
    # Der Fehler passierte hier, weil adapter_func mit 2 Args aufgerufen wurde,
    # aber prepare_flux_base_input nur 1 Arg akzeptierte. Jetzt ist es gefixt!
    if adapter_func: return adapter_func(prompt, image_url)
    return prepare_standard_input(prompt, image_url)