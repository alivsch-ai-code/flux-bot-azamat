import random

# Struktur: Key = Sprache, Value = Liste von Tipps
# HTML-Tags wie <b> sind erlaubt und erwünscht für Telegram.
TIPS_DICT = {
    "de": [
        "💡 <b>Tipp:</b> Nutze Wörter wie 'cinematic lighting' oder 'golden hour' für besseres Licht.",
        "💡 <b>Wusstest du?</b> Ein Seitenverhältnis von 16:9 wirkt oft filmischer als quadratisch.",
        "💡 <b>Pro-Tipp:</b> Beschreibe auch den Hintergrund, nicht nur das Hauptobjekt.",
        "💡 <b>Kamera:</b> Versuche 'shot on 35mm lens' für einen realistischen Foto-Look.",
        "🚀 <b>Modell-Info:</b> Flux Schnell ist günstig, Flux Pro hat mehr Details.",
        "🎨 <b>Stil:</b> Du kannst Stile mixen, z.B. 'Cyberpunk mixed with Art Nouveau'.",
        "🤖 <b>Editieren:</b> Mit Gemini kannst du Dinge im Bild ändern, ohne Photoshop.",
        "📹 <b>Video:</b> Image-to-Video funktioniert am besten mit klaren, statischen Startbildern.",
        "✨ <b>Magic:</b> Das Wort 'masterpiece' im Prompt wirkt manchmal Wunder.",
        "👔 <b>Bewerbung:</b> Achte beim Upload für InstantID auf gute Ausleuchtung im Gesicht.",
        "💡 <b>Tipp:</b> Nutze negative Prompts (bei Modellen die es unterstützen), um Hässliches zu vermeiden.",
        "📝 <b>Text:</b> Flux Modelle können Text rendern! Schreibe: 'a sign that says Hello'.",
        "🔍 <b>Details:</b> Wörter wie '8k', 'highly detailed' oder 'sharp focus' helfen oft.",
        "🕶️ <b>Vibe:</b> Füge 'vaporwave' oder 'retro 80s style' hinzu für coole Farben.",
        "📸 <b>Realismus:</b> Nutze 'skin texture', 'pores' und 'natural lighting' für echte Porträts.",
        "🏎️ <b>Geschwindigkeit:</b> Die 'Schnell'-Modelle sind perfekt, um Prompts zu testen.",
        "🌌 <b>Atmosphäre:</b> 'Foggy', 'misty' oder 'rainy' erzeugen sofort Stimmung.",
        "🦁 <b>Tiere:</b> KI generiert Fell besonders gut mit 'fluffy' oder 'soft fur'.",
        "📐 <b>Perspektive:</b> Versuche 'drone view', 'wide angle' oder 'close-up'.",
        "💎 <b>Credits:</b> Spare Credits, indem du erst 'Schnell' nutzt und dann das Beste hochskalierst."
    ],
    "en": [
        "💡 <b>Tip:</b> Use words like 'cinematic lighting' or 'golden hour' for better atmosphere.",
        "💡 <b>Did you know?</b> A 16:9 aspect ratio often looks more cinematic than square.",
        "💡 <b>Pro Tip:</b> Describe the background too, not just the main subject.",
        "💡 <b>Camera:</b> Try 'shot on 35mm lens' for a realistic photo look.",
        "🚀 <b>Model Info:</b> Flux Schnell is cheap, Flux Pro offers more details.",
        "🎨 <b>Style:</b> You can mix styles, e.g., 'Cyberpunk mixed with Art Nouveau'.",
        "🤖 <b>Editing:</b> Use Gemini to change things in the image without Photoshop.",
        "📹 <b>Video:</b> Image-to-Video works best with clear, static input images.",
        "✨ <b>Magic:</b> The word 'masterpiece' in the prompt sometimes works wonders.",
        "👔 <b>Headshots:</b> Ensure good lighting on your face when uploading for InstantID.",
        "💡 <b>Tip:</b> Use negative prompts (where supported) to avoid ugly artifacts.",
        "📝 <b>Text:</b> Flux models can render text! Write: 'a sign that says Hello'.",
        "🔍 <b>Details:</b> Words like '8k', 'highly detailed', or 'sharp focus' often help.",
        "🕶️ <b>Vibe:</b> Add 'vaporwave' or 'retro 80s style' for cool colors.",
        "📸 <b>Realism:</b> Use 'skin texture', 'pores', and 'natural lighting' for real portraits.",
        "🏎️ <b>Speed:</b> 'Schnell' models are perfect for testing prompts efficiently.",
        "🌌 <b>Atmosphere:</b> 'Foggy', 'misty', or 'rainy' instantly create mood.",
        "🦁 <b>Animals:</b> AI generates fur especially well with 'fluffy' or 'soft fur'.",
        "📐 <b>Perspective:</b> Try 'drone view', 'wide angle', or 'close-up'.",
        "💎 <b>Credits:</b> Save credits by using 'Schnell' first, then upscaling the best one."
    ],
    "ru": [
        "💡 <b>Совет:</b> Используйте 'cinematic lighting' или 'golden hour' для лучшего света.",
        "💡 <b>Знаете ли вы?</b> Формат 16:9 выглядит более кинематографично, чем квадрат.",
        "💡 <b>Про-совет:</b> Описывайте не только объект, но и задний план.",
        "💡 <b>Камера:</b> Попробуйте 'shot on 35mm lens' для эффекта настоящего фото.",
        "🚀 <b>Инфо:</b> Flux Schnell дешевле, а Flux Pro дает больше деталей.",
        "🎨 <b>Стиль:</b> Смешивайте стили! Например: 'Cyberpunk mixed with Art Nouveau'.",
        "🤖 <b>Редактура:</b> Gemini поможет изменить детали на фото без Photoshop.",
        "📹 <b>Видео:</b> Для Image-to-Video лучше всего подходят четкие статичные фото.",
        "✨ <b>Магия:</b> Слово 'masterpiece' в промте иногда творит чудеса.",
        "👔 <b>Фото:</b> Для InstantID важно хорошее освещение вашего лица.",
        "💡 <b>Совет:</b> Используйте негативные промты, чтобы убрать лишнее.",
        "📝 <b>Текст:</b> Модели Flux умеют писать текст! Пишите: 'a sign that says Hello'.",
        "🔍 <b>Детали:</b> Слова '8k', 'highly detailed' или 'sharp focus' улучшают резкость.",
        "🕶️ <b>Вайб:</b> Добавьте 'vaporwave' или 'retro 80s style' для крутых цветов.",
        "📸 <b>Реализм:</b> Используйте 'skin texture', 'pores' для реалистичных портретов.",
        "🏎️ <b>Скорость:</b> Модели 'Schnell' идеальны для тестов.",
        "🌌 <b>Атмосфера:</b> 'Foggy' (туман) или 'rainy' (дождь) создают настроение.",
        "🦁 <b>Животные:</b> Мех отлично получается с промтами 'fluffy' или 'soft fur'.",
        "📐 <b>Ракурс:</b> Попробуйте 'drone view' (вид с дрона) или 'close-up' (крупный план).",
        "💎 <b>Кредиты:</b> Экономьте: сначала тестируйте на Schnell, потом делайте апскейл."
    ],
    "kk": [
        "💡 <b>Кеңес:</b> Жарық жақсы болу үшін 'cinematic lighting' немесе 'golden hour' қолданыңыз.",
        "💡 <b>Білгеніңіз жөн:</b> 16:9 форматы шаршыға қарағанда киноға көбірек ұқсайды.",
        "💡 <b>Кәсіби кеңес:</b> Тек негізгі нысанды ғана емес, фонды да сипаттаңыз.",
        "💡 <b>Камера:</b> Шынайы фото үшін 'shot on 35mm lens' деп жазып көріңіз.",
        "🚀 <b>Ақпарат:</b> Flux Schnell арзан, ал Flux Pro толығырақ детальдар береді.",
        "🎨 <b>Стиль:</b> Стильдерді араластырыңыз! Мысалы: 'Cyberpunk mixed with Art Nouveau'.",
        "🤖 <b>Өңдеу:</b> Gemini арқылы суретті Photoshop-сыз өзгертуге болады.",
        "📹 <b>Видео:</b> Image-to-Video үшін анық, қозғалмайтын суреттер жақсы нәтиже береді.",
        "✨ <b>Сиқыр:</b> 'Masterpiece' сөзі кейде ғажайыптар жасайды.",
        "👔 <b>Сурет:</b> InstantID үшін жүзіңіз жақсы жарықтандырылған болуы маңызды.",
        "💡 <b>Кеңес:</b> Артық нәрселерді болдырмау үшін негативті сұраныстарды қолданыңыз.",
        "📝 <b>Мәтін:</b> Flux модельдері мәтін жаза алады! Байқап көріңіз: 'a sign that says Hello'.",
        "🔍 <b>Сапа:</b> '8k', 'highly detailed' сөздері суреттің сапасын арттырады.",
        "🕶️ <b>Вайб:</b> Керемет түстер үшін 'vaporwave' немесе 'retro 80s style' қосыңыз.",
        "📸 <b>Шынайылық:</b> Портреттер үшін 'skin texture' және 'natural lighting' қолданыңыз.",
        "🏎️ <b>Жылдамдық:</b> 'Schnell' модельдері тестілеу үшін өте қолайлы.",
        "🌌 <b>Атмосфера:</b> 'Foggy' (тұман) немесе 'rainy' (жаңбыр) ерекше көңіл-күй сыйлайды.",
        "🦁 <b>Жануарлар:</b> 'fluffy' немесе 'soft fur' сөздерімен жүни өте әдемі шығады.",
        "📐 <b>Ракурс:</b> 'drone view' немесе 'wide angle' қолданып көріңіз.",
        "💎 <b>Кредиттер:</b> Үнемдеу үшін алдымен Schnell қолданып, кейін сапасын арттырыңыз."
    ]
}

def get_random_tip(lang="de"):
    """
    Gibt einen zufälligen Tipp in der gewünschten Sprache zurück.
    Fallback auf Englisch, falls Sprache nicht gefunden wird.
    """
    # Wenn Sprache nicht im Dict, nutze Englisch
    tips_list = TIPS_DICT.get(lang, TIPS_DICT["en"])
    return random.choice(tips_list)