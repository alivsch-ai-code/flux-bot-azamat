from src.domain.entities import AIModel
from pathlib import Path

# KONVENTION: 1 Euro = 100 Credits
base_path = Path(__file__).parent

AI_MODELS = {
    # -------------------------------------------------------------------------
    # 💎 PREMIUM PIPELINES (Bestehend - Beispiele verfeinert)
    # -------------------------------------------------------------------------
    "premium-headshot-pipeline": AIModel(
        key="premium-headshot-pipeline",
        replicate_id="PIPELINE/PREMIUM-V1", 
        name="👔 Premium Business Set",
        description="Erstellt 4 professionelle LinkedIn-Fotos von deinem Selfie.",
        cost=100, 
        type=["pipeline", "image"],
        provider="replicate",
        example_input_image="Ein klares Selfie von vorne",
        example_output_image="4x Hochauflösende Business-Porträts im Anzug"
    ),

    # -------------------------------------------------------------------------
    # 🎨 IMAGE GENERATION (Bestehend - Beispiele verfeinert)
    # -------------------------------------------------------------------------
    "flux-1.1-pro": AIModel(
        key="flux-1.1-pro",
        replicate_id="black-forest-labs/flux-1.1-pro",
        name="✨ Flux 1.1 Pro",
        description="Der Marktführer für ultra-realistische Bilder.",
        original_dollar_per_run=0.04,
        cost=10,# 1 Telegram Star == 1 Cent 
        type=["text-to-image","image-to-image"],
        provider="replicate",
        example_prompt="Cinematic portrait of a Viking warrior in a snowstorm, hyper-realistic, 8k, extreme detail.",
        example_output_image=base_path / "prompt_example" / "flux_1_1_pro.jpg"
    ),

    "flux-schnell": AIModel(
        key="flux-schnell",
        replicate_id="black-forest-labs/flux-schnell",
        name="⚡ Flux Schnell",
        description="Ideal für schnelle Entwürfe und Tests.",
        cost=2, 
        type=["image"],
        provider="replicate",
        example_prompt="A modern glass villa in the jungle, architectural photography.",
        example_output_image="Ein hochwertiges Bild in Sekunden"
    ),

    "recraft-v3": AIModel(
        key="recraft-v3",
        replicate_id="recraft-ai/recraft-v3",
        name="🎨 Recraft V3",
        description="Spezialisiert auf Vektorgrafiken und Logos mit Text.",
        cost=8, 
        type=["image", "edit"],
        provider="replicate",
        example_prompt="A retro travel poster for Mars, bold typography 'VISIT MARS', flat vector style."
    ),

    "nano-banana-pro": AIModel(
        key="google/nano-banana-pro",
        replicate_id="google/nano-banana-pro",
        name="🍌 Nano Banana Pro",
        description="Grafikdesign & Logos.",
        cost=20,
        type=["image", "image_to_image"],
        provider="replicate",
        example_prompt="Minimalist logo of a golden leaf, professional branding, white background."
    ),
    
    # -------------------------------------------------------------------------
    # 🎥 VIDEO (Bestehend & Neu hinzugefügt)
    # -------------------------------------------------------------------------
    "minimax-video": AIModel(
        key="minimax-video",
        replicate_id="minimax/video-01",
        name="🎥 Minimax Video",
        description="Erstelle kinoreife 5-Sekunden-Videos aus Text.",
        cost=80, 
        type=["video"],
        provider="replicate",
        example_prompt="A majestic dragon soaring through a narrow canyon, cinematic lighting, 4k."
    ),

    "hunyuan-video": AIModel(
        key="hunyuan-video",
        replicate_id="tencent/hunyuan-video",
        name="🎬 Hunyuan Video",
        description="State-of-the-Art Video-Generierung mit hoher Konsistenz.",
        cost=70,
        type=["video"],
        provider="replicate",
        example_prompt="An astronaut walking through a neon-lit futuristic market on a rainy night."
    ),

    "ltx-video": AIModel(
        key="ltx-video",
        replicate_id="lightricks/ltx-video",
        name="🎞️ LTX Video",
        description="Sehr schnelle Videogenerierung für kreative Clips.",
        cost=40,
        type=["video"],
        provider="replicate",
        example_prompt="Time-lapse of a blooming flower in a dark forest, magical atmosphere."
    ),

    # -------------------------------------------------------------------------
    # 🎭 FACE & STYLE (Neu hinzugefügt)
    # -------------------------------------------------------------------------
    "face-swap": AIModel(
        key="face-swap",
        replicate_id="easel/advanced-face-swap",
        name="👤 Face Swap",
        description="Tauscht Gesichter zwischen zwei Bildern perfekt aus.",
        cost=15,
        type=["image", "edit"],
        provider="replicate",
        example_input_image="Zielbild + Gesichtsquelle",
        example_output_image="Das Zielbild mit deinem Gesicht"
    ),

    "face-enhance": AIModel(
        key="face-enhance",
        replicate_id="sczhou/codeformer",
        name="✨ Face Enhance",
        description="Stellt alte Fotos wieder her und verbessert KI-generierte Gesichter.",
        cost=10,
        type=["edit"],
        provider="replicate"
    ),

    "instant-id": AIModel(
        key="instant-id",
        replicate_id="instantx/instantid",
        name="🆔 Instant-ID",
        description="Erstellt Bilder von dir in jedem beliebigen Stil (z.B. Cyberpunk, Comic).",
        cost=15,
        type=["image"],
        provider="replicate",
        example_input_image="Dein Porträtfoto",
        example_prompt="As a medieval knight in shining armor, oil painting style."
    ),

    # -------------------------------------------------------------------------
    # 🛠️ TOOLS & EDITING (Bestehend & Neu hinzugefügt)
    # -------------------------------------------------------------------------
    "upscale-esrgan": AIModel(
        key="upscale-esrgan",
        replicate_id="nightmareai/real-esrgan",
        name="🔍 4x Smart Upscaler",
        description="Macht kleine Bilder riesig und scharf.",
        cost=5, 
        type=["upscale"],
        provider="replicate",
        example_input_image="Ein verpixeltes oder kleines Foto",
        example_output_image="Gestochen scharfe 4K-Version"
    ),

    "remove-bg": AIModel(
        key="remove-bg",
        replicate_id="lucataco/remove-bg",
        name="✂️ Background Remover",
        description="Entfernt den Hintergrund präzise in Sekunden.",
        cost=3,
        type=["edit"],
        provider="replicate",
        example_input_image="Foto mit unruhigem Hintergrund",
        example_output_image="Freigestelltes Objekt (PNG)"
    ),

    "image-to-prompt": AIModel(
        key="image-to-prompt",
        replicate_id="methexis-inc/img2prompt",
        name="👁️ Image to Prompt",
        description="Analysiert ein Bild und erstellt den passenden KI-Prompt dazu.",
        cost=2,
        type=["tool"],
        provider="replicate",
        example_input_image="Beliebiges Bild",
        example_output_image="Ein detaillierter Text-Prompt für Midjourney/Flux"
    ),

    # -------------------------------------------------------------------------
    # 🎙️ AUDIO & MUSIC (Neu hinzugefügt)
    # -------------------------------------------------------------------------
    "stable-audio": AIModel(
        key="stable-audio",
        replicate_id="stability-ai/stable-audio-open-1.0",
        name="🎵 Stable Audio",
        description="Generiert hochwertige Musik-Loops und Soundeffekte.",
        cost=15,
        type=["audio"],
        provider="replicate",
        example_prompt="Lo-fi hip hop beat for studying, chill atmosphere, 90 bpm."
    ),

    "xtts-v2": AIModel(
        key="xtts-v2",
        replicate_id="lucataco/xtts-v2",
        name="🗣️ Voice Clone (XTTS)",
        description="Lasse Text mit deiner eigenen oder einer fremden Stimme sprechen.",
        cost=10,
        type=["audio"],
        provider="replicate",
        example_prompt="Text, der gesprochen werden soll + Audio-Probe der Stimme."
    ),
    # -------------------------------------------------------------------------
    # 🤖 LLM & TEXT (Neu: Grok, DeepSeek, GPT)
    # -------------------------------------------------------------------------
    "grok-beta": AIModel(
        key="grok-beta",
        replicate_id="grok-beta", # ID für den internen Call
        name="🧠 Grok (xAI)",
        description="Der KI-Chatbot von Elon Musk (xAI). Unzensierter & witziger.",
        cost=5,
        type=["text"],
        provider="grok" # Neuer Provider
    ),

    "deepseek-chat": AIModel(
        key="deepseek-chat",
        replicate_id="deepseek-chat",
        name="🐳 DeepSeek V3",
        description="Intelligentes Coding- & Chat-Modell, extrem günstig.",
        cost=2,
        type=["text"],
        provider="deepseek" # Neuer Provider
    ),

    "gpt-4o": AIModel(
        key="gpt-4o",
        replicate_id="gpt-4o",
        name="🟢 GPT-4o",
        description="Das Flaggschiff von OpenAI. Schnell & intelligent.",
        cost=10,
        type=["text"],
        provider="openai"
    ),

    # -------------------------------------------------------------------------
    # 🎨 OPENAI BILDER (DALL-E 3)
    # -------------------------------------------------------------------------
    "dall-e-3": AIModel(
        key="dall-e-3",
        replicate_id="dall-e-3",
        name="🎨 DALL-E 3",
        description="Exzellent im Verstehen von komplexen Prompts.",
        cost=12,
        type=["image"],
        provider="openai"
    ),

    # -------------------------------------------------------------------------
    # 🎬 KLING AI (Video)
    # -------------------------------------------------------------------------
    "kling-video": AIModel(
        key="kling-video",
        replicate_id="kling-v1", # Platzhalter ID
        name="🎥 Kling AI Video",
        description="Erstellt realistische Videos (5s) mit Motion Control.",
        cost=60,
        type=["video"],
        provider="kling"
    )
}