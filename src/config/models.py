from src.domain.entities import AIModel

# Hier definieren wir alle Modelle aus deiner Tabelle
AI_MODELS = {
    # --- TEXT TO IMAGE ---
    "flux-2-pro": AIModel(
        key="flux-2-pro",
        replicate_id="black-forest-labs/flux-2-pro", # Beispiel ID
        name="Flux 2 Pro",
        cost=23, # 0,23 € -> wir rechnen intern in Cents/Credits
        type="image"
    ),
    "flux-1.1-pro": AIModel(
        key="flux-1.1-pro",
        replicate_id="black-forest-labs/flux-1.1-pro",
        name="Flux 1.1 Pro",
        cost=40,
        type="image"
    ),
    "flux-schnell": AIModel(
        key="flux-schnell",
        replicate_id="black-forest-labs/flux-schnell",
        name="Flux Schnell",
        cost=5,
        type="image"
    ),
    "imagen-4-ultra": AIModel(
        key="imagen-4-ultra",
        replicate_id="google/imagen-4-ultra", # Hypothetische ID
        name="Imagen 4 Ultra",
        cost=90,
        type="image"
    ),
    "imagen-4": AIModel(
        key="imagen-4",
        replicate_id="google/imagen-4",
        name="Imagen 4",
        cost=40,
        type="image"
    ),
    "imagen-4-fast": AIModel(
        key="imagen-4-fast",
        replicate_id="google/imagen-4-fast",
        name="Imagen 4 Fast",
        cost=30,
        type="image"
    ),
    "ideogram-v3": AIModel(
        key="ideogram-v3",
        replicate_id="ideogram-ai/ideogram-v3-turbo",
        name="Ideogram v3",
        cost=30,
        type="image"
    ),
    "nano-banana-pro": AIModel(
        key="nano-banana-pro",
        replicate_id="google/nano-banana-pro",
        name="Nano Banana Pro",
        cost=75,
        type="image"
    ),

    # --- EDIT IMAGE ---
    "gemini-2.5": AIModel(
        key="gemini-2.5",
        replicate_id="google/gemini-2.5-flash-image",
        name="Gemini 2.5 Flash",
        cost=39,
        type="edit"
    ),
    "qwen-image": AIModel(
        key="qwen-image",
        replicate_id="qwen/qwen-image-edit",
        name="Qwen Image Edit",
        cost=25,
        type="edit"
    ),

    # --- VIDEO ---
    "sora-2": AIModel(
        key="sora-2",
        replicate_id="openai/sora-2",
        name="Sora 2",
        cost=100, # 1,00 €
        type="video"
    ),
    "wan-2.5": AIModel(
        key="wan-2.5",
        replicate_id="wan-video/wan-2.5-t2v",
        name="Wan 2.5 T2V",
        cost=150,
        type="video"
    ),
    "veo-3.1": AIModel(
        key="veo-3.1",
        replicate_id="google/veo-3.1",
        name="Veo 3.1",
        cost=300,
        type="video"
    ),

    # --- AUDIO ---
    "sonauto": AIModel(
        key="sonauto",
        replicate_id="sonauto-ai/sonauto",
        name="Sonauto AI",
        cost=120,
        type="audio",
        provider="sonauto"
    ),
}