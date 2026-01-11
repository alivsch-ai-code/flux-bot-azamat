# src/utils/strings.py

STRINGS = {
    # --- NAVIGATION & MENUS ---
    "welcome": {
        "en": "👋 Welcome to the AI Hub!\nWhat would you like to create?",
        "de": "👋 Willkommen im AI Hub!\nWas möchtest du erstellen?",
        "ru": "👋 Добро пожаловать в AI Hub!\nЧто вы хотите создать?",
        "kk": "👋 AI Hub-қа қош келдіңіз!\nНе жасағыңыз келеді?"
    },
    "transparency_msg": {
        "en": (
            "<b>🛡️ We believe in transparency</b>\n\n"
            "We use established networks like Replicate to provide top-tier AI technology.\n"
            "<b>Have fun with AZAMAT AI!</b> 🚀"
        ),
        "de": (
            "<b>🛡️ Wir setzen auf Transparenz</b>\n\n"
            "Wir nutzen etablierte Netzwerke wie Replicate, um euch KI-Technologie zur Verfügung zu stellen.\n"
            "<b>Viel Spaß mit AZAMAT AI!</b> 🚀"
        ),
        "ru": (
            "<b>🛡️ Мы верим в прозрачность</b>\n\n"
            "Мы используем проверенные сети, такие как Replicate, чтобы предоставить вам лучшие ИИ-технологии.\n"
            "<b>Удачи с AZAMAT AI!</b> 🚀"
        ),
        "kk": (
            "<b>🛡️ Біз ашықтыққа сенеміз</b>\n\n"
            "Біз сізге озық ИИ технологияларын ұсыну үшін Replicate сияқты танымал желілерді қолданамыз.\n"
            "<b>AZAMAT AI-мен бірге уақытты қызықты өткізіңіз!</b> 🚀"
        )
    },
    "btn_back": {
        "en": "🔙 Back",
        "de": "🔙 Zurück",
        "ru": "🔙 Назад",
        "kk": "🔙 Артқа"
    },
    "msg_main_menu": {
        "en": "Main Menu",
        "de": "Hauptmenü",
        "ru": "Главное меню",
        "kk": "Басты мәзір"
    },
    "msg_select_model": {
        "en": "Choose a model:",
        "de": "Wähle ein Modell:",
        "ru": "Выберите модель:",
        "kk": "Модельді таңдаңыз:"
    },
    "msg_select_tool": {
        "en": "Choose a tool:",
        "de": "Wähle ein Tool:",
        "ru": "Выберите инструмент:",
        "kk": "Құралды таңдаңыз:"
    },

    # --- MAIN MENU BUTTONS ---
    "btn_pro_headshot": {
        "en": "👔 Pro Headshot",
        "de": "👔 Pro Bewerbungsfoto",
        "ru": "👔 Проф. фото",
        "kk": "👔 Кәсіби сурет"
    },
    "menu_image_studio": {
        "en": "🎨 Image Studio",
        "de": "🎨 Bild Studio",
        "ru": "🎨 Студия изображений",
        "kk": "🎨 Сурет студиясы"
    },
    "menu_video_studio": {
        "en": "🎬 Video Studio",
        "de": "🎬 Video Studio",
        "ru": "🎬 Видео-студия",
        "kk": "🎬 Видео студиясы"
    },
    "menu_tools_edit": {
        "en": "🛠️ Tools & Edit",
        "de": "🛠️ Tools & Edit",
        "ru": "🛠️ Инструменты",
        "kk": "🛠️ Құралдар"
    },
    "menu_image_description": {
        "en": "🖼️ Describe Image",
        "de": "🖼️ Bildbeschreibung",
        "ru": "🖼️ Описание изображения",
        "kk": "🖼️ Сурет сипаттамасы"
    },
    # --- ADMIN MESSAGES ---
    "admin_cheat_success": {
        "en": "🫡 Cheat Mode activated: +10,000 Credits added!",
        "de": "🫡 Chef-Modus aktiviert: +10.000 Credits hinzugefügt!",
        "ru": "🫡 Режим бога активирован: начислено +10 000 кредитов!",
        "kk": "🫡 Бастық режимі қосылды: +10 000 кредит қосылды!"
    },

    # --- ERRORS & STATUS ---
    "err_model_not_found": {
        "en": "Error: Model {model_key} not found.",
        "de": "Fehler: Modell {model_key} nicht gefunden.",
        "ru": "Ошибка: Модель {model_key} не найдена.",
        "kk": "Қате: {model_key} моделі табылмады."
    },
    "err_no_credits": {
        "en": "🚫 <b>Not enough Credits!</b>\nRequired: {cost}\nAvailable: {balance}\n\nUse /buy to top up.",
        "de": "🚫 <b>Nicht genug Credits!</b>\nBenötigt: {cost}\nVerfügbar: {balance}\n\nNutze /buy um aufzuladen.",
        "ru": "🚫 <b>Недостаточно кредитов!</b>\nТребуется: {cost}\nДоступно: {balance}\n\nИспользуйте /buy для пополнения.",
        "kk": "🚫 <b>Кредит жеткіліксіз!</b>\nҚажет: {cost}\nБар: {balance}\n\nТолықтыру үшін /buy қолданыңыз."
    },
    "err_gen_failed": {
        "en": "❌ Error: {result}",
        "de": "❌ Fehler: {result}",
        "ru": "❌ Ошибка: {result}",
        "kk": "❌ Қате: {result}"
    },
    "err_critical": {
        "en": "Critical Error: {error}",
        "de": "Kritischer Fehler: {error}",
        "ru": "Критическая ошибка: {error}",
        "kk": "Критикалық қате: {error}"
    },
    "err_img_missing": {
        "en": "📸 Please upload an image first!",
        "de": "📸 Bitte lade zuerst ein Bild hoch!",
        "ru": "📸 Пожалуйста, сначала загрузите изображение!",
        "kk": "📸 Алдымен суретті жүктеңіз!"
    },
    "err_aborted": {
        "en": "🛑 Aborted.",
        "de": "🛑 Abgebrochen.",
        "ru": "🛑 Отменено.",
        "kk": "🛑 Тоқтатылды."
    },
    "status_generating": {
        "en": "⏳ <b>Generating with {model_name}...</b>\n\n{tip}",
        "de": "⏳ <b>Generiere mit {model_name}...</b>\n\n{tip}",
        "ru": "⏳ <b>Генерация с помощью {model_name}...</b>\n\n{tip}",
        "kk": "⏳ <b>{model_name} арқылы жасалуда...</b>\n\n{tip}"
    },
    "status_downloading_img": {
        "en": "⬇️ Downloading image...",
        "de": "⬇️ Lade Bild...",
        "ru": "⬇️ Скачиваю изображение...",
        "kk": "⬇️ Сурет жүктелуде..."
    },
    "status_starting_upscale": {
        "en": "✅ Image received! Starting Upscaling immediately...",
        "de": "✅ Bild empfangen! Starte Upscaling sofort...",
        "ru": "✅ Изображение получено! Начинаю улучшение качества...",
        "kk": "✅ Сурет қабылданды! Сапаны жақсарту басталуда..."
    },

    # --- SUCCESS MESSAGES ---
    "success_caption": {
        "en": "✨ {prompt}...\n💰 Cost: {cost} | Remaining: {balance}",
        "de": "✨ {prompt}...\n💰 Kosten: {cost} | Rest: {balance}",
        "ru": "✨ {prompt}...\n💰 Цена: {cost} | Остаток: {balance}",
        "kk": "✨ {prompt}...\n💰 Құны: {cost} | Қалғаны: {balance}"
    },
    "success_album_caption": {
        "en": "✨ Premium Set for '{prompt}'\n💰 Cost: {cost} | Remaining: {balance}",
        "de": "✨ Premium Set für '{prompt}'\n💰 Kosten: {cost} | Rest: {balance}",
        "ru": "✨ Премиум сет для '{prompt}'\n💰 Цена: {cost} | Остаток: {balance}",
        "kk": "✨ '{prompt}' үшін премиум жиынтық\n💰 Құны: {cost} | Қалғаны: {balance}"
    },
    "success_uncompressed": {
        "en": "\n(Uncompressed File)",
        "de": "\n(Unkomprimierte Datei)",
        "ru": "\n(Файл без сжатия)",
        "kk": "\n(Сығылмаған файл)"
    },
    "msg_next_step": {
        "en": "<b>What would you like to do next?</b> 👇",
        "de": "<b>Was möchtest du als nächstes tun?</b> 👇",
        "ru": "<b>Что вы хотите сделать дальше?</b> 👇",
        "kk": "<b>Келесі қадамыңыз қандай?</b> 👇"
    },
    "msg_copy_edit": {
        "en": "Copy and edit:\n<code>{optimized}</code>",
        "de": "Kopiere und bearbeite:\n<code>{optimized}</code>",
        "ru": "Скопируйте и отредактируйте:\n<code>{optimized}</code>",
        "kk": "Көшіріп, өңдеңіз:\n<code>{optimized}</code>"
    },

    # --- MODEL INFO TEXTS ---
    "info_premium_pipeline": {
        "en": (
            "✅ Model: <b>{model_name}</b>\n"
            "💰 Cost: {cost} Credits\n\n"
            "🚀 <b>Premium Business Set activated!</b>\n"
            "I will create 4 professional variations (Office, Studio, etc.).\n"
            "The process takes about 30-60 seconds.\n\n"
            "📸 <b>Please upload your selfie now:</b>"
        ),
        "de": (
            "✅ Modell: <b>{model_name}</b>\n"
            "💰 Kosten: {cost} Credits\n\n"
            "🚀 <b>Premium Business Set aktiviert!</b>\n"
            "Ich erstelle 4 professionelle Variationen (Büro, Studio, etc.).\n"
            "Der Prozess dauert ca. 30-60 Sekunden.\n\n"
            "📸 <b>Bitte lade jetzt dein Selfie hoch:</b>"
        ),
        "ru": (
            "✅ Модель: <b>{model_name}</b>\n"
            "💰 Цена: {cost} кредитов\n\n"
            "🚀 <b>Премиум бизнес-сет активирован!</b>\n"
            "Я создам 4 профессиональных варианта (Офис, Студия и т.д.).\n"
            "Процесс займет около 30-60 секунд.\n\n"
            "📸 <b>Пожалуйста, загрузите ваше селфи:</b>"
        ),
        "kk": (
            "✅ Модель: <b>{model_name}</b>\n"
            "💰 Құны: {cost} кредит\n\n"
            "🚀 <b>Премиум бизнес жиынтығы қосылды!</b>\n"
            "Мен 4 кәсіби нұсқаны жасаймын (Офис, Студия және т.б.).\n"
            "Процесс шамамен 30-60 секундты алады.\n\n"
            "📸 <b>Қазір селфиіңізді жүктеңіз:</b>"
        )
    },
    "info_needs_image": {
        "en": "✅ Model: <b>{model_name}</b>\n💰 Cost: {cost} Credits\n\n📸 <b>Please upload a photo now:</b>",
        "de": "✅ Modell: <b>{model_name}</b>\n💰 Kosten: {cost} Credits\n\n📸 <b>Bitte lade jetzt das Foto hoch:</b>",
        "ru": "✅ Модель: <b>{model_name}</b>\n💰 Цена: {cost} кредитов\n\n📸 <b>Пожалуйста, загрузите фото:</b>",
        "kk": "✅ Модель: <b>{model_name}</b>\n💰 Құны: {cost} кредит\n\n📸 <b>Фотосуретті жүктеңіз:</b>"
    },
    "info_optional_image": {
        "en": "✅ Model: <b>{model_name}</b>\n💰 Cost: {cost} Credits\n\n📸 <b>Upload a photo</b> OR write a prompt.",
        "de": "✅ Modell: <b>{model_name}</b>\n💰 Kosten: {cost} Credits\n\n📸 <b>Lade ein Foto</b> ODER schreibe einen Prompt.",
        "ru": "✅ Модель: <b>{model_name}</b>\n💰 Цена: {cost} кредитов\n\n📸 <b>Загрузите фото</b> ИЛИ напишите запрос.",
        "kk": "✅ Модель: <b>{model_name}</b>\n💰 Құны: {cost} кредит\n\n📸 <b>Сурет жүктеңіз</b> НЕМЕСЕ сұраныс жазыңыз."
    },
    "info_text_only": {
        "en": "✅ Model: <b>{model_name}</b>\n💰 Cost: {cost} Credits\n\n✍️ <b>Write your prompt:</b>",
        "de": "✅ Modell: <b>{model_name}</b>\n💰 Kosten: {cost} Credits\n\n✍️ <b>Schreibe deinen Prompt:</b>",
        "ru": "✅ Модель: <b>{model_name}</b>\n💰 Цена: {cost} кредитов\n\n✍️ <b>Напишите ваш запрос:</b>",
        "kk": "✅ Модель: <b>{model_name}</b>\n💰 Құны: {cost} кредит\n\n✍️ <b>Сұранысыңызды жазыңыз:</b>"
    },

    # --- PROMPT REQUESTS ---
    "prompt_req_pipeline": {
        "en": "✅ Selfie received!\n👤 <b>Who is it?</b> (e.g. 'A man', 'A woman')",
        "de": "✅ Selfie da!\n👤 <b>Wer soll es sein?</b> (z.B. 'Ein Mann', 'Eine Frau')",
        "ru": "✅ Селфи получено!\n👤 <b>Кто это?</b> (напр. 'Мужчина', 'Женщина')",
        "kk": "✅ Селфи қабылданды!\n👤 <b>Бұл кім?</b> (мыс. 'Ер адам', 'Әйел адам')"
    },
    "prompt_req_standard": {
        "en": "✅ Image received!\n✍️ <b>What should I do? (Prompt):</b>",
        "de": "✅ Bild da!\n✍️ <b>Was soll ich tun? (Prompt):</b>",
        "ru": "✅ Изображение получено!\n✍️ <b>Что нужно сделать? (Промт):</b>",
        "kk": "✅ Сурет қабылданды!\n✍️ <b>Не істеу керек? (Сұраныс):</b>"
    },

    # --- PROMPT OPTIMIZATION ---
    "optimizing_msg": {
        "en": "🧠 <b>Thinking...</b>\nI am optimizing your prompt for better results.",
        "de": "🧠 <b>Denke nach...</b>\nIch optimiere deinen Prompt für bessere Ergebnisse.",
        "ru": "🧠 <b>Думаю...</b>\nЯ оптимизирую ваш запрос для лучшего результата.",
        "kk": "🧠 <b>Ойланудамын...</b>\nНәтижені жақсарту үшін сұранысыңызды оңтайландырудамын."
    },
    "opt_result_msg": {
        "en": "<b>Original:</b>\n{original}\n\n<b>✨ Proposal:</b>\n<code>{optimized}</code>\n\nHow do you want to proceed?",
        "de": "<b>Original:</b>\n{original}\n\n<b>✨ Vorschlag:</b>\n<code>{optimized}</code>\n\nWie möchtest du fortfahren?",
        "ru": "<b>Оригинал:</b>\n{original}\n\n<b>✨ Предложение:</b>\n<code>{optimized}</code>\n\nКак вы хотите продолжить?",
        "kk": "<b>Түпнұсқа:</b>\n{original}\n\n<b>✨ Ұсыныс:</b>\n<code>{optimized}</code>\n\nҚалай жалғастырамыз?"
    },
    "btn_accept": {
        "en": "✅ Use Proposal",
        "de": "✅ Vorschlag nehmen",
        "ru": "✅ Принять предложение",
        "kk": "✅ Ұсынысты қабылдау"
    },
    "btn_edit": {
        "en": "✏️ Edit Proposal",
        "de": "✏️ Vorschlag ändern",
        "ru": "✏️ Изменить предложение",
        "kk": "✏️ Ұсынысты өзгерту"
    },
    "btn_reject": {
        "en": "❌ Use Original",
        "de": "❌ Original nehmen",
        "ru": "❌ Использовать оригинал",
        "kk": "❌ Түпнұсқаны қолдану"
    },
    "session_expired": {
        "en": "⚠️ Session expired.",
        "de": "⚠️ Sitzung abgelaufen.",
        "ru": "⚠️ Сессия истекла.",
        "kk": "⚠️ Сессия аяқталды."
    },

    # --- MODEL DETAIL INFO & BEISPIELE ---
    "info_model_desc": {
        "en": "ℹ️ <b>Description:</b>\n{desc}",
        "de": "ℹ️ <b>Beschreibung:</b>\n{desc}",
        "ru": "ℹ️ <b>Описание:</b>\n{desc}",
        "kk": "ℹ️ <b>Сипаттамасы:</b>\n{desc}"
    },
    "info_example_prompt": {
        "en": "📝 <b>Example Prompt:</b>\n<code>{prompt}</code>",
        "de": "📝 <b>Beispiel-Prompt:</b>\n<code>{prompt}</code>",
        "ru": "📝 <b>Пример промта:</b>\n<code>{prompt}</code>",
        "kk": "📝 <b>Мысал сұраныс:</b>\n<code>{prompt}</code>"
    },
    "info_examples_disclaimer": {
        "en": "⚠️ <i>Note: The images/videos shown are examples. Actual quality depends on input.</i>",
        "de": "⚠️ <i>Hinweis: Die gezeigten Medien sind Beispiele. Die Qualität hängt vom Input ab.</i>",
        "ru": "⚠️ <i>Примечание: Это примеры. Качество зависит от исходных данных.</i>",
        "kk": "⚠️ <i>Ескерту: Бұл мысалдар. Сапасы енгізілген деректерге байланысты.</i>"
    },
    "lbl_example_input": {
        "en": "🖼 Example Input",
        "de": "🖼 Beispiel Input",
        "ru": "🖼 Пример входа",
        "kk": "🖼 Мысал кіріс"
    },
    "lbl_example_output": {
        "en": "🎨 Example Output",
        "de": "🎨 Beispiel Output",
        "ru": "🎨 Пример результата",
        "kk": "🎨 Мысал нәтиже"
    },
    # Füge dies in dein STRINGS Dictionary in strings.py ein:

    # --- REFERRAL / SHARE ---
    "btn_free_credits": {
        "en": "🎁 Free Credits",
        "de": "🎁 Gratis Credits",
        "ru": "🎁 Бесплатные кредиты",
        "kk": "🎁 Тегін кредиттер"
    },
    "share_menu_title": {
        "en": "<b>🎁 Invite Friends & Earn Credits!</b>\n\nShare your personal link. For every new user who joins via your link, you get <b>{amount} Credits</b>!\n\nYour Link:\n<code>{ref_link}</code>",
        "de": "<b>🎁 Freunde werben & Credits verdienen!</b>\n\nTeile deinen persönlichen Link. Für jeden neuen Nutzer, der über deinen Link kommt, erhältst du <b>{amount} Credits</b>!\n\nDein Link:\n<code>{ref_link}</code>",
        "ru": "<b>🎁 Пригласи друзей и получи кредиты!</b>\n\nПоделись ссылкой. За каждого нового пользователя ты получишь <b>{amount} кредитов</b>!\n\nТвоя ссылка:\n<code>{ref_link}</code>",
        "kk": "<b>🎁 Достарды шақырып, кредит жина!</b>\n\nСілтемеңізді бөлісіңіз. Сілтеме арқылы қосылған әр жаңа қолданушы үшін <b>{amount} кредит</b> аласыз!\n\nСілтемеңіз:\n<code>{ref_link}</code>"
    },
    "share_text_template": {
        "en": "Check out this AI Bot! 🚀 Create amazing images and videos: {ref_link}",
        "de": "Schau dir diesen AI Bot an! 🚀 Erstelle krasse Bilder und Videos: {ref_link}",
        "ru": "Попробуй этот ИИ-бот! 🚀 Создавай крутые фото и видео: {ref_link}",
        "kk": "Мына AI ботты көр! 🚀 Керемет суреттер мен видеолар жаса: {ref_link}"
    },
    "ref_success_referrer": {
        "en": "🎉 <b>New Referral!</b>\nA new user joined via your link.\n<b>+{amount} Credits</b> added!",
        "de": "🎉 <b>Erfolgreich geworben!</b>\nEin neuer Nutzer ist deinem Link gefolgt.\n<b>+{amount} Credits</b> gutgeschrieben!",
        "ru": "🎉 <b>Новый рефералл!</b>\nПользователь перешел по твоей ссылке.\n<b>+{amount} кредитов</b> начислено!",
        "kk": "🎉 <b>Жаңа шақыру!</b>\nЖаңа қолданушы сілтемеңіз арқылы қосылды.\n<b>+{amount} кредит</b> қосылды!"
    },
    "btn_share_vk": {"en": "VKontakte", "de": "VKontakte", "ru": "ВКонтакте", "kk": "VKontakte"},
    "btn_share_x": {"en": "X (Twitter)", "de": "X (Twitter)", "ru": "X (Twitter)", "kk": "X (Twitter)"},
    "btn_share_fb": {"en": "Facebook", "de": "Facebook", "ru": "Facebook", "kk": "Facebook"},
    "btn_share_ok": {"en": "Odnoklassniki", "de": "Odnoklassniki", "ru": "Odnoklassniki", "kk": "Odnoklassniki"},
    "btn_share_tg": {"en": "Telegram", "de": "Telegram", "ru": "Telegram", "kk": "Telegram"},
}

def get_text(key, lang="en"):
    """Holt den Text basierend auf Key und Sprache."""
    return STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("en", key))