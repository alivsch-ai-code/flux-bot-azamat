from src.domain.entities import AIModel

# KONVENTION: 1 Euro = 100 Credits

AI_MODELS = {
    # -------------------------------------------------------------------------
    # 💎 PREMIUM PIPELINES
    # -------------------------------------------------------------------------
    "premium-headshot-pipeline": AIModel(
        key="premium-headshot-pipeline",
        replicate_id="PIPELINE/PREMIUM-V1", 
        name="👔 Premium Business Set",
        description="4 professionelle Bilder.",
        cost=100, 
        type=["pipeline", "image"] # Ist eine Pipeline, erzeugt aber Bilder
    ),

    # -------------------------------------------------------------------------
    # 🎨 IMAGE GENERATION
    # -------------------------------------------------------------------------
    "flux-1.1-pro": AIModel(
        key="flux-1.1-pro",
        replicate_id="black-forest-labs/flux-1.1-pro",
        name="✨ Flux 1.1 Pro",
        description="Ultra Realism.",
        cost=8, 
        type=["image"] # Nur Bild-Generierung
    ),

    "flux-schnell": AIModel(
        key="flux-schnell",
        replicate_id="black-forest-labs/flux-schnell",
        name="⚡ Flux Schnell",
        description="Schnelle Entwürfe.",
        cost=2, 
        type=["image"]
    ),

    "recraft-v3": AIModel(
        key="recraft-v3",
        replicate_id="recraft-ai/recraft-v3",
        name="🎨 Recraft V3 (Vektor)",
        description="Grafikdesign & Logos.",
        cost=8, 
        type=["image", "edit"] # Könnte auch bei Tools auftauchen, da spezialisiert
    ),
    "nano-banana": AIModel(
        key="google/nano-banana",
        replicate_id="google/nano-banana",
        name="🍌 Nano Banana",
        description="Grafikdesign & Logos.",
        cost=10, #0.039 $ pro image 
        type=["image", "image_to_image"] # Könnte auch bei Tools auftauchen, da spezialisiert
    ),
    "nano-banana-pro": AIModel(
        key="google/nano-banana-pro",
        replicate_id="google/nano-banana-pro",
        name="🍌 🍌 Nano Banana Pro",
        description="Grafikdesign & Logos.",
        cost=20, #0.15 $ pro 1k-2k image 0,3 $ if 4K
        type=["image", "image_to_image"] # Könnte auch bei Tools auftauchen, da spezialisiert
    ),
    # -------------------------------------------------------------------------
    # 🛠️ TOOLS
    # -------------------------------------------------------------------------
    "upscale-esrgan": AIModel(
        key="upscale-esrgan",
        replicate_id="nightmareai/real-esrgan",
        name="🔍 4x Smart Upscaler",
        description="Vergrößern.",
        cost=5, 
        type=["upscale"] # Gehört zu Tools
    ),
        "gemini-2.5-flash-image": AIModel(
        key="google/gemini-2.5-flash-image",
        replicate_id="google/gemini-2.5-flash-image", 
        name="🤖 Gemini 2.5 Flash Image",
        description="Bildanalyse.",
        cost=3, 
        type=["image"] # Gehört zu Tools
    ),

    "face-swap": AIModel(
        key="face-swap",
        replicate_id="lucataco/faceswap:9a4298548422074c3f57258c5d544497314ae4112df80d116f0d2109e843d20d",
        name="🎭 Face Swap Fun",
        description="Gesicht tauschen.",
        cost=4, 
        type=["edit", "image_to_image"] # Gehört zu Tools
    ),

    "gemini-2.5-flash": AIModel(
        key="gemini-2.5-flash",
        replicate_id="google/gemini-2.5-flash", 
        name="🤖 Gemini 2.5 Flash",
        description="Bildanalyse.",
        cost=3, 
        type=["image"] # Gehört zu Tools
    ),

    # -------------------------------------------------------------------------
    # 🎥 VIDEO
    # -------------------------------------------------------------------------
    "minimax-video": AIModel(
        key="minimax-video",
        replicate_id="minimax/video-01",
        name="🎥 Minimax Video",
        description="Text-to-Video.",
        cost=80, 
        type=["video"]
    ),
}