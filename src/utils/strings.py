# src/utils/strings.py

STRINGS = {
    # --- NAVIGATION & MENUS ---
    "welcome": {
        "en": "👋 <b>Welcome to the AI Hub!</b>\nChoose a category to start creating:",
        "de": "👋 <b>Willkommen im AI Hub!</b>\nWähle eine Kategorie, um zu starten:",
        "ru": "👋 <b>Добро пожаловать в AI Hub!</b>\nВыберите категорию:",
        "kk": "👋 <b>AI Hub-қа қош келдіңіз!</b>\nСанатты таңдаңыз:"
    },
    "transparency_msg": {
        "en": "<b>🛡️ We believe in transparency</b>\nHave fun with AZAMAT AI! 🚀",
        "de": "<b>🛡️ Wir setzen auf Transparenz</b>\nViel Spaß mit AZAMAT AI! 🚀",
        "ru": "<b>🛡️ Мы верим в прозрачность</b>\nУдачи с AZAMAT AI! 🚀",
        "kk": "<b>🛡️ Біз ашықтыққа сенеміз</b>\nAZAMAT AI-мен бірге уақытты қызықты өткізіңіз! 🚀"
    },
    "btn_back": { "en": "🔙 Back", "de": "🔙 Zurück", "ru": "🔙 Назад", "kk": "🔙 Артқа" },
    
    # --- MODEL DETAIL VIEW (NEU) ---
    "model_info_title": {
        "en": "🤖 <b>{name}</b>\n{desc}\n\n💰 Cost: <b>{cost} Credits</b>",
        "de": "🤖 <b>{name}</b>\n{desc}\n\n💰 Kosten: <b>{cost} Credits</b>",
        "ru": "🤖 <b>{name}</b>\n{desc}\n\n💰 Цена: <b>{cost} Кредитов</b>",
        "kk": "🤖 <b>{name}</b>\n{desc}\n\n💰 Құны: <b>{cost} Кредит</b>"
    },
    "model_example_intro": {
        "en": "<b>Here is our example:</b>",
        "de": "<b>Hier ist unser Beispiel:</b>",
        "ru": "<b>Вот пример:</b>",
        "kk": "<b>Мысал:</b>"
    },
    "model_example_output": {
        "en": "View Result",
        "de": "Ergebnis ansehen",
        "ru": "Смотреть результат",
        "kk": "Нәтижені көру"
    },
    "model_req_prompt": {
        "en": "\n✍️ <b>Write your prompt:</b>",
        "de": "\n✍️ <b>Schreibe deinen Prompt:</b>",
        "ru": "\n✍️ <b>Напишите промт:</b>",
        "kk": "\n✍️ <b>Сұранысты жазыңыз:</b>"
    },
    "model_req_image": {
        "en": "\n📸 <b>Please upload an image:</b>",
        "de": "\n📸 <b>Bitte lade ein Bild hoch:</b>",
        "ru": "\n📸 <b>Загрузите фото:</b>",
        "kk": "\n📸 <b>Сурет жүктеңіз:</b>"
    },

    # --- MAIN MENU BUTTONS ---
    "menu_profile": { "en": "👤 My Profile", "de": "👤 Mein Profil", "ru": "👤 Мой профиль", "kk": "👤 Менің профилім" },
    "menu_image_studio": { "en": "🎨 Image / GPTs", "de": "🎨 Bild / GPTs", "ru": "🎨 Изображения", "kk": "🎨 Сурет / GPT" },
    "menu_video_studio": { "en": "🎬 Video AI", "de": "🎬 Video KI", "ru": "🎬 Видео ИИ", "kk": "🎬 Видео ИИ" },
    # NEU: Audio Studio
    "menu_audio_studio": { "en": "🎙️ Audio Studio", "de": "🎙️ Audio Studio", "ru": "🎙️ Аудио Студия", "kk": "🎙️ Аудио студия" },
    
    "menu_tools_edit": { "en": "🛠️ Tools & Upscale", "de": "🛠️ Tools & Upscale", "ru": "🛠️ Инструменты", "kk": "🛠️ Құралдар" },
    "menu_referral": { "en": "🎁 Free Credits", "de": "🎁 Gratis Credits", "ru": "🎁 Кредиты", "kk": "🎁 Кредиттер" },
    "menu_shop": { "en": "💳 Shop / Buy", "de": "💳 Shop / Kaufen", "ru": "💳 Магазин", "kk": "💳 Дүкен" },
    "menu_support": { "en": "🆘 Support", "de": "🆘 Support", "ru": "🆘 Поддержка", "kk": "🆘 Қолдау" },
    # NEU: Settings
    "menu_settings": { "en": "⚙️ Settings", "de": "⚙️ Einstellungen", "ru": "⚙️ Настройки", "kk": "⚙️ Параметрлер" },

    # --- AUDIO STUDIO BUTTONS ---
    "btn_tts": { "en": "🎙️ Text to Speech", "de": "🎙️ Sprachsynthese", "ru": "🎙️ Синтез речи", "kk": "🎙️ Мәтінді дауысқа" },
    "btn_clone": { "en": "👥 Voice Cloning", "de": "👥 Stimmklonung", "ru": "👥 Клонирование", "kk": "👥 Дауысты клондау" },
    "btn_suno": { "en": "🎸 SUNO (Music)", "de": "🎸 SUNO (Musik)", "ru": "🎸 SUNO (Музыка)", "kk": "🎸 SUNO (Музыка)" },
    "btn_vid2aud": { "en": "🌊 Video to Audio", "de": "🌊 Video zu Audio", "ru": "🌊 Видео в Аудио", "kk": "🌊 Видеодан аудио" },
    "btn_sound": { "en": "🥁 Sound Gen", "de": "🥁 Sound-Generator", "ru": "🥁 Звуки", "kk": "🥁 Дыбыс генераторы" },
    "btn_transcribe": { "en": "👂 Audio to Text", "de": "👂 Audio zu Text", "ru": "👂 Аудио в текст", "kk": "👂 Аудиодан мәтінге" },
    # --- SETTINGS MENÜ ---
    "settings_title": {
        "en": "<b>⚙️ Settings</b>\nHere you can configure the bot.",
        "de": "<b>⚙️ Einstellungen</b>\nHier kannst du den Bot konfigurieren.",
        "ru": "<b>⚙️ Настройки</b>\nЗдесь вы можете настроить бота.",
        "kk": "<b>⚙️ Параметрлер</b>\nБұл жерде ботты баптай аласыз."
    },
    "btn_lang": { "en": "🌐 Language: {lang}", "de": "🌐 Sprache: {lang}", "ru": "🌐 Язык: {lang}", "kk": "🌐 Тіл: {lang}" },
    "btn_opt_on": { "en": "✨ Prompt Magic: ON", "de": "✨ Prompt Magie: AN", "ru": "✨ Magic: ВКЛ", "kk": "✨ Magic: ҚОСУ" },
    "btn_opt_off": { "en": "⚪️ Prompt Magic: OFF", "de": "⚪️ Prompt Magie: AUS", "ru": "⚪️ Magic: ВЫКЛ", "kk": "⚪️ Magic: ӨШІРУ" },
    # NEU: Daily News
    "btn_daily_on": { "en": "📰 Daily News: ON", "de": "📰 Tägliche News: AN", "ru": "📰 Новости: ВКЛ", "kk": "📰 Жаңалықтар: ҚОСУ" },
    "btn_daily_off": { "en": "🔕 Daily News: OFF", "de": "🔕 Tägliche News: AUS", "ru": "🔕 Новости: ВЫКЛ", "kk": "🔕 Жаңалықтар: ӨШІРУ" },
    
    "lang_selected": { "en": "✅ Language set to English.", "de": "✅ Sprache auf Deutsch gesetzt.", "ru": "✅ Язык изменен на Русский.", "kk": "✅ Тіл Қазақшаға өзгертілді." },

    # --- ERRORS & STATUS ---
    "err_model_not_found": { "en": "Error: Model {model_key} not found.", "de": "Fehler: Modell {model_key} nicht gefunden.", "ru": "Ошибка: Модель не найдена.", "kk": "Қате: Модель табылмады." },
    "err_no_credits": { "en": "🚫 Not enough Credits!", "de": "🚫 Nicht genug Credits!", "ru": "🚫 Недостаточно кредитов!", "kk": "🚫 Кредит жеткіліксіз!" },
    "err_gen_failed": { "en": "❌ Error: {result}", "de": "❌ Fehler: {result}", "ru": "❌ Ошибка: {result}", "kk": "❌ Қате: {result}" },
    "err_critical": { "en": "Critical Error: {error}", "de": "Kritischer Fehler: {error}", "ru": "Критическая ошибка: {error}", "kk": "Критикалық қате: {error}" },
    "err_img_missing": { "en": "📸 Please upload an image first!", "de": "📸 Bitte lade zuerst ein Bild hoch!", "ru": "📸 Сначала загрузите изображение!", "kk": "📸 Алдымен суретті жүктеңіз!" },
    "err_provider_failed": {
        "en": "❌ The AI model could not be started because the provider is currently having issues. Please try again later.",
        "de": "❌ Das KI-Modell konnte nicht gestartet werden, da der Anbieter derzeit Probleme hat. Bitte versuchen Sie es später noch einmal.",
        "ru": "❌ Не удалось запустить модель ИИ, так как у провайдера возникли проблемы. Пожалуйста, повторите попытку позже.",
        "kk": "❌ AI моделі іске қосылмады, себебі провайдерде қазіргі уақытта мәселелер бар. Кейінірек қайталап көріңіз."
    },
    "status_generating": { "en": "⏳ <b>Generating...</b>\n{tip}", "de": "⏳ <b>Generiere...</b>\n{tip}", "ru": "⏳ <b>Генерация...</b>\n{tip}", "kk": "⏳ <b>Жасалуда...</b>\n{tip}" },
    "status_generating_long": {
        "en": "⏳ Your request is being processed by the AI.\nThis may take a moment...",
        "de": "⏳ Deine Anfrage wird von der KI verarbeitet.\nDas kann einen Moment dauern...",
        "ru": "⏳ Ваш запрос обрабатывается ИИ.\nЭто может занять некоторое время...",
        "kk": "⏳ Сіздің сұрауыңызды AI өңдеуде.\nБұл біраз уақыт алуы мүмкін..."
    },
    "status_downloading_img": { "en": "⬇️ Downloading...", "de": "⬇️ Lade Bild...", "ru": "⬇️ Скачиваю...", "kk": "⬇️ Жүктелуде..." },
    
    # --- SUCCESS ---
    "success_caption": { "en": "✨ {prompt}\n💰 Cost: {cost}", "de": "✨ {prompt}\n💰 Kosten: {cost}", "ru": "✨ {prompt}\n💰 Цена: {cost}", "kk": "✨ {prompt}\n💰 Құны: {cost}" },
    "msg_next_step": { "en": "<b>What next?</b> 👇", "de": "<b>Was als nächstes?</b> 👇", "ru": "<b>Что дальше?</b> 👇", "kk": "<b>Келесі қадам?</b> 👇" },
    "msg_copy_edit": { "en": "Copy and edit:\n<code>{optimized}</code>", "de": "Kopiere und bearbeite:\n<code>{optimized}</code>", "ru": "Скопируйте и измените:\n<code>{optimized}</code>", "kk": "Көшіріп, өңдеңіз:\n<code>{optimized}</code>" },

    # --- PROMPT OPTIMIZATION ---
    "optimizing_msg": { "en": "🧠 <b>Thinking...</b>\nOptimizing prompt...", "de": "🧠 <b>Denke nach...</b>\nOptimiere Prompt...", "ru": "🧠 <b>Думаю...</b>\nУлучшаю запрос...", "kk": "🧠 <b>Ойланудамын...</b>\nСұранысты жақсартудамын..." },
    "opt_result_msg": { "en": "<b>Original:</b>\n{original}\n\n<b>✨ Proposal:</b>\n<code>{optimized}</code>", "de": "<b>Original:</b>\n{original}\n\n<b>✨ Vorschlag:</b>\n<code>{optimized}</code>", "ru": "<b>Оригинал:</b>\n{original}\n\n<b>✨ Предложение:</b>\n<code>{optimized}</code>", "kk": "<b>Түпнұсқа:</b>\n{original}\n\n<b>✨ Ұсыныс:</b>\n<code>{optimized}</code>" },
    "btn_accept": { "en": "✅ Use Proposal", "de": "✅ Vorschlag nehmen", "ru": "✅ Принять", "kk": "✅ Қабылдау" },
    "btn_edit": { "en": "✏️ Edit", "de": "✏️ Ändern", "ru": "✏️ Изменить", "kk": "✏️ Өзгерту" },
    "btn_reject": { "en": "❌ Original", "de": "❌ Original", "ru": "❌ Оригинал", "kk": "❌ Түпнұсқа" },
    "session_expired": { "en": "⚠️ Session expired.", "de": "⚠️ Sitzung abgelaufen.", "ru": "⚠️ Сессия истекла.", "kk": "⚠️ Сессия аяқталды." },

    # --- SHARE ---
    "share_menu_title": { "en": "<b>Invite Friends!</b>\nLink: <code>{ref_link}</code>", "de": "<b>Freunde werben!</b>\nLink: <code>{ref_link}</code>", "ru": "<b>Пригласи друзей!</b>\nLink: <code>{ref_link}</code>", "kk": "<b>Достарды шақыр!</b>\nLink: <code>{ref_link}</code>" },
    "share_text_template": { "en": "Check out this AI Bot! {ref_link}", "de": "Schau dir diesen AI Bot an! {ref_link}", "ru": "Попробуй этот ИИ-бот! {ref_link}", "kk": "Мына AI ботты көр! {ref_link}" },
    "ref_success_referrer": { "en": "🎉 +{amount} Credits!", "de": "🎉 +{amount} Credits!", "ru": "🎉 +{amount} Кредитов!", "kk": "🎉 +{amount} Кредит!" },
    "btn_share_vk": {"en": "VK", "de": "VK", "ru": "VK", "kk": "VK"},
    "btn_share_x": {"en": "X", "de": "X", "ru": "X", "kk": "X"},
    "btn_share_fb": {"en": "FB", "de": "FB", "ru": "FB", "kk": "FB"},
    "btn_share_tg": {"en": "TG", "de": "TG", "ru": "TG", "kk": "TG"},


    # --- ADMIN ---
    "admin_cheat_success": { "en": "Cheat activated.", "de": "Cheat aktiviert.", "ru": "Чит активирован.", "kk": "Чит қосылды." },
    "profile_text": {
        "en": "👤 <b>Profile</b>\n\nName: {name}\n💎 Balance: <b>{creds} Credits</b>\n🆔 ID: <code>{user_id}</code>",
        "de": "👤 <b>Profil</b>\n\nName: {name}\n💎 Guthaben: <b>{creds} Credits</b>\n🆔 ID: <code>{user_id}</code>",
        "ru": "👤 <b>Профиль</b>\n\nИмя: {name}\n💎 Баланс: <b>{creds} Кредитов</b>\n🆔 ID: <code>{user_id}</code>",
        "kk": "👤 <b>Профиль</b>\n\nАты: {name}\n💎 Баланс: <b>{creds} Кредит</b>\n🆔 ID: <code>{user_id}</code>"
    },
    "support_text": {
        "en": "🆘 <b>Support</b>\n\nContact the administrator for help.",
        "de": "🆘 <b>Support</b>\n\nKontaktiere den Admin für Hilfe.",
        "ru": "🆘 <b>Поддержка</b>\n\nСвяжитесь с администратором.",
        "kk": "🆘 <b>Қолдау</b>\n\nКөмек алу үшін әкімшіге хабарласыңыз."
    },
    "daily_news_on": {
        "en": "Daily News: ON",
        "de": "Daily News: AN",
        "ru": "Новости: ВКЛ",
        "kk": "Жаңалықтар: ҚОСУ"
    },
    "daily_news_off": {
        "en": "Daily News: OFF",
        "de": "Daily News: AUS",
        "ru": "Новости: ВЫКЛ",
        "kk": "Жаңалықтар: ӨШІРУ"
    }
}


def get_text(key, lang="en"):
    return STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("en", key))