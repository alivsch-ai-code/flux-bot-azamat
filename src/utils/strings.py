# src/utils/strings.py

STRINGS = {
    # --- NAVIGATION & MENUS ---
    "welcome": {
        "en": "👋 <b>Welcome to the AI Hub!</b>\n\nExperience the future of AI creation!\n\n🎥 Check out our <a href='https://www.youtube.com/watch?v=dQw4w9WgXcQ'>demo video</a> to see amazing possibilities!\n\nChoose a category to start creating:",
        "de": "👋 <b>Willkommen im AI Hub!</b>\n\nErlebe die Zukunft der KI-Kreation!\n\n🎥 Schau dir unser <a href='https://www.youtube.com/watch?v=dQw4w9WgXcQ'>Demo-Video</a> an, um unglaubliche Möglichkeiten zu sehen!\n\nWähle eine Kategorie, um zu starten:",
        "ru": "👋 <b>Добро пожаловать в AI Hub!</b>\n\nОщутите будущее создания ИИ!\n\n🎥 Посмотрите наше <a href='https://www.youtube.com/watch?v=dQw4w9WgXcQ'>демонстрационное видео</a>, чтобы увидеть удивительные возможности!\n\nВыберите категорию:",
        "kk": "👋 <b>AI Hub-қа қош келдіңіз!</b>\n\nЖасанды интеллект жасаудың болашағын сезіңіз!\n\n🎥 Керемет мүмкіндіктерді көру үшін <a href='https://www.youtube.com/watch?v=dQw4w9WgXcQ'>бейне ролик</a>ке қараңыз!\n\nСанатты таңдаңыз:"
    },
    "transparency_msg": {
        "en": "<b>🛡️ We believe in transparency</b>\n\nMany bots online are full of hidden costs and traps. With us, you pay per generation. You can save even more money by using Replicate models directly - great for tech-savvy users! Have fun with AZAMAT AI! 🚀",
        "de": "<b>🛡️ Wir setzen auf Transparenz</b>\n\nIm Netz gibt es viele Kostentreiber und Fallen bei Bots. Bei uns zahlen Sie pro Generierung. Sie können noch mehr sparen, indem Sie direkt Replicate-Modelle nutzen - perfekt für technisch versierte Nutzer! Viel Spaß mit AZAMAT AI! 🚀",
        "ru": "<b>🛡️ Мы верим в прозрачность</b>\n\nМногие боты в интернете полны скрытых платежей и ловушек. У нас вы платите за каждую генерацию. Вы можете сэкономить еще больше, используя модели Replicate напрямую - отлично подходит для технически продвинутых пользователей! Удачи с AZAMAT AI! 🚀",
        "kk": "<b>🛡️ Біз ашықтыққа сенеміз</b>\n\nИнтернетте көптеген жасанды интеллект боттары жасырын шығындар мен құнық бар. Бізде сіз әр жасау үшін құн төлейсіз. Техникалық білімі бар пайдаланушылар үшін Replicate модельдерін тура қолданып, тағы да көбірек үнемдеуге болады! AZAMAT AI-мен бірге уақытты қызықты өткізіңіз! 🚀"
    },
    "no_referral": {
        "en": "🌟 <b>You haven't referred us yet!</b>\n\nPlease recommend us to your friends. When they join through your link, we'll give you free points as a thank you!",
        "de": "🌟 <b>Sie haben uns noch nicht empfohlen!</b>\n\nMachen Sie das gerne, dann geben wir Ihnen kostenlose Punkte dafür!",
        "ru": "🌟 <b>Вы еще не рекомендовали нас!</b>\n\nСделайте это, и мы дадим вам бесплатные очки в качестве благодарности!",
        "kk": "🌟 <b>Сіз әлі бізге ұсынбағансыз!</b>\n\nМұны істеңіз, содан кейін сізге тегін ұпайлар береміз!"
    },
    "btn_back": { "en": "🔙 Back", "de": "🔙 Zurück", "ru": "🔙 Назад", "kk": "🔙 Артқа" },
    
    # --- MODEL CATEGORIES ---
    "menu_image": { "en": "🎨 Image Studio", "de": "🎨 Bild Studio", "ru": "🎨 Картинки", "kk": "🎨 Сурет" },
    "menu_video": { "en": "🎬 Video Studio", "de": "🎬 Video Studio", "ru": "🎬 Видео", "kk": "🎬 Видео" },
    "menu_audio": { "en": "🎙️ Audio Studio", "de": "🎙️ Audio Studio", "ru": "🎙️ Аудио", "kk": "🎙️ Аудио" },
    "menu_text": { "en": "📝 Text / Chat", "de": "📝 Text / Chat", "ru": "📝 Текст", "kk": "📝 Мәтін" },
    "menu_tools": { "en": "🛠️ Tools", "de": "🛠️ Werkzeuge", "ru": "🛠️ Инструменты", "kk": "🛠️ Құралдар" },
    
    # Sub-Kategorien
    "menu_kling": { "en": "⚡ Kling AI", "de": "⚡ Kling AI", "ru": "⚡ Kling AI", "kk": "⚡ Kling AI" },
    "menu_flux": { "en": "✨ Flux Models", "de": "✨ Flux Modelle", "ru": "✨ Flux", "kk": "✨ Flux" },
    "menu_pro": { "en": "💎 Professional", "de": "💎 Profi-Tools", "ru": "💎 Pro", "kk": "💎 Pro" },

    # --- CHAT MODE ---
    "ask_chat_mode": {
        "en": "💬 <b>Start Chat Mode?</b>\n\nDo you want to start a continuous conversation or just send a single prompt?\n\n💰 <b>Cost per message: {cost} Credits</b>",
        "de": "💬 <b>Chat-Modus starten?</b>\n\nMöchtest du eine fortlaufende Unterhaltung starten oder nur einen einzelnen Prompt senden?\n\n💰 <b>Kosten pro Nachricht: {cost} Credits</b>",
        "ru": "💬 <b>Начать чат?</b>\n\nХотите начать диалог или отправить один запрос?\n\n💰 <b>Цена за сообщение: {cost} Кредитов</b>",
        "kk": "💬 <b>Чат режимін бастау керек пе?</b>\n\nДиалогты бастағыңыз келе ме әлде бір сұраныс жібересіз бе?\n\n💰 <b>Хабарлама құны: {cost} Кредит</b>"
    },
    "btn_yes_chat": { "en": "✅ Start Chat Mode", "de": "✅ Chat-Modus starten", "ru": "✅ Начать чат", "kk": "✅ Чат бастау" },
    "btn_no_chat": { "en": "❌ Single Prompt", "de": "❌ Einmaliger Prompt", "ru": "❌ Один запрос", "kk": "❌ Бір реттік" },
    
    "chat_active_msg": {
        "en": "🟢 <b>Chat Mode Active!</b>\n\nYou are now chatting with <b>{model}</b>.\nEvery message costs <b>{cost} Credits</b>.\n\n👇 Just write your message.",
        "de": "🟢 <b>Chat-Modus Aktiv!</b>\n\nDu chattest jetzt mit <b>{model}</b>.\nJede Nachricht kostet <b>{cost} Credits</b>.\n\n👇 Schreibe einfach drauf los.",
        "ru": "🟢 <b>Чат активен!</b>\n\nМодель: <b>{model}</b>.\nЦена: <b>{cost} Кредитов</b>.\n\n👇 Пишите сообщение.",
        "kk": "🟢 <b>Чат белсенді!</b>\n\nМодель: <b>{model}</b>.\nҚұны: <b>{cost} Кредит</b>.\n\n👇 Хабарлама жазыңыз."
    },
    "chat_welcome_back": {
        "en": "👋 <b>Welcome back to Chat Mode!</b>\n\nActive Model: <b>{model}</b>\nCost: <b>{cost} Credits/msg</b>\n\nContinue writing or end chat.",
        "de": "👋 <b>Willkommen zurück im Chat!</b>\n\nAktives Modell: <b>{model}</b>\nKosten: <b>{cost} Credits/Nachricht</b>\n\nSchreibe weiter oder beende den Chat.",
        "ru": "👋 <b>С возвращением в чат!</b>\n\nМодель: <b>{model}</b>\n\nПродолжайте писать или завершите чат.",
        "kk": "👋 <b>Чатқа қош келдіңіз!</b>\n\nМодель: <b>{model}</b>\n\nЖалғастырыңыз немесе чатты аяқтаңыз."
    },
    "btn_end_chat": { "en": "🛑 End Chat Mode", "de": "🛑 Chat beenden", "ru": "🛑 Завершить чат", "kk": "🛑 Чатты аяқтау" },
    "chat_ended": { "en": "🛑 Chat Mode ended.", "de": "🛑 Chat-Modus beendet.", "ru": "🛑 Чат завершен.", "kk": "🛑 Чат аяқталды." },

    # --- FALLBACK MESSAGES (NEU) ---
    "fallback_attempt": {
        "en": "⚠️ <b>Connection Issue:</b> {model} is not responding.\n🔄 Switching to fallback model <b>{fallback}</b>...",
        "de": "⚠️ <b>Verbindungsproblem:</b> {model} antwortet nicht.\n🔄 Wechsle zum Fallback-Modell <b>{fallback}</b>...",
        "ru": "⚠️ <b>Ошибка соединения:</b> {model} не отвечает.\n🔄 Переключаюсь на <b>{fallback}</b>...",
        "kk": "⚠️ <b>Байланыс қатесі:</b> {model} жауап бермейді.\n🔄 <b>{fallback}</b> моделіне ауысуда..."
    },
    "fallback_failed": {
        "en": "❌ <b>We are sorry!</b>\nAll available models are currently overloaded. Please try again later. Your credits have been refunded.",
        "de": "❌ <b>Entschuldigung!</b>\nAlle verfügbaren Modelle sind derzeit überlastet. Bitte versuche es später noch einmal. Deine Credits wurden erstattet.",
        "ru": "❌ <b>Извините!</b>\nВсе модели перегружены. Попробуйте позже. Кредиты возвращены.",
        "kk": "❌ <b>Кешіріңіз!</b>\nБарлық модельдер бос емес. Кейінірек көріңіз. Кредиттеріңіз қайтарылды."
    },

    # --- MODEL DETAIL VIEW ---
    "model_info_title": {
        "en": "🤖 <b>{name}</b>\n{desc}\n\n💰 Cost: <b>{cost} Credits</b>",
        "de": "🤖 <b>{name}</b>\n{desc}\n\n💰 Kosten: <b>{cost} Credits</b>",
        "ru": "🤖 <b>{name}</b>\n{desc}\n\n💰 Цена: <b>{cost} Кредитов</b>",
        "kk": "🤖 <b>{name}</b>\n{desc}\n\n💰 Құны: <b>{cost} Кредит</b>"
    },
    "model_example_intro": { "en": "<b>Here is our example:</b>", "de": "<b>Hier ist unser Beispiel:</b>", "ru": "<b>Вот пример:</b>", "kk": "<b>Мысал:</b>" },
    "model_req_prompt": { "en": "\n✍️ <b>Write your prompt:</b>", "de": "\n✍️ <b>Schreibe deinen Prompt:</b>", "ru": "\n✍️ <b>Напишите промт:</b>", "kk": "\n✍️ <b>Сұранысты жазыңыз:</b>" },
    "model_req_image": { "en": "\n📸 <b>Please upload an image:</b>", "de": "\n📸 <b>Bitte lade ein Bild hoch:</b>", "ru": "\n📸 <b>Загрузите фото:</b>", "kk": "\n📸 <b>Сурет жүктеңіз:</b>" },

    # --- MAIN MENU BUTTONS ---
    "menu_profile": { "en": "👤 Profile", "de": "👤 Mein Profil", "ru": "👤 Профиль", "kk": "👤 Профиль" },
    "menu_referral": { "en": "🎁 Free Credits", "de": "🎁 Gratis Credits", "ru": "🎁 Кредиты", "kk": "🎁 Кредиттер" },
    "menu_shop": { "en": "💳 Shop", "de": "💳 Shop / Kaufen", "ru": "💳 Магазин", "kk": "💳 Дүкен" },
    "menu_support": { "en": "🆘 Support", "de": "🆘 Support", "ru": "🆘 Поддержка", "kk": "🆘 Қолдау" },
    "menu_settings": { "en": "⚙️ Settings", "de": "⚙️ Einstellungen", "ru": "⚙️ Настройки", "kk": "⚙️ Параметрлер" },

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
    "btn_daily_on": { "en": "📰 Daily News: ON", "de": "📰 Tägliche News: AN", "ru": "📰 Новости: ВКЛ", "kk": "📰 Жаңалықтар: ҚОСУ" },
    "btn_daily_off": { "en": "🔕 Daily News: OFF", "de": "🔕 Tägliche News: AUS", "ru": "🔕 Новости: ВЫКЛ", "kk": "🔕 Жаңалықтар: ӨШІРУ" },
    "lang_selected": { "en": "✅ Language set to English.", "de": "✅ Sprache auf Deutsch gesetzt.", "ru": "✅ Язык изменен на Русский.", "kk": "✅ Тіл Қазақшаға өзгертілді." },

    # --- ERRORS & STATUS ---
    "err_model_not_found": { "en": "Error: Model {model_key} not found.", "de": "Fehler: Modell {model_key} nicht gefunden.", "ru": "Ошибка: Модель не найдена.", "kk": "Қате: Модель табылмады." },
    "err_model_maintenance": { "en": "⚠️ This model is currently inactive.", "de": "⚠️ Dieses Modell ist derzeit in Wartung.", "ru": "⚠️ Модель на обслуживании.", "kk": "⚠️ Модель қызмет көрсетуде." },
    "err_no_credits": { "en": "🚫 Not enough Credits!", "de": "🚫 Nicht genug Credits!", "ru": "🚫 Недостаточно кредитов!", "kk": "🚫 Кредит жеткіліксіз!" },
    "err_gen_failed": { "en": "❌ Error: {result}", "de": "❌ Fehler: {result}", "ru": "❌ Ошибка: {result}", "kk": "❌ Қате: {result}" },
    "status_generating": { "en": "⏳ <b>Generating...</b>\n{tip}", "de": "⏳ <b>Generiere...</b>\n{tip}", "ru": "⏳ <b>Генерация...</b>\n{tip}", "kk": "⏳ <b>Жасалуда...</b>\n{tip}" },
    "success_caption": { "en": "✨ {prompt}\n💰 Cost: {cost}", "de": "✨ {prompt}\n💰 Kosten: {cost}", "ru": "✨ {prompt}\n💰 Цена: {cost}", "kk": "✨ {prompt}\n💰 Құны: {cost}" },
    "msg_next_step": { "en": "<b>What next?</b> 👇", "de": "<b>Was als nächstes?</b> 👇", "ru": "<b>Что дальше?</b> 👇", "kk": "<b>Келесі қадам?</b> 👇" },
    
    # --- PROMPT OPTIMIZATION ---
    "optimizing_msg": { "en": "🧠 <b>Thinking...</b>", "de": "🧠 <b>Denke nach...</b>", "ru": "🧠 <b>Думаю...</b>", "kk": "🧠 <b>Ойланудамын...</b>" },
    "opt_result_msg": { "en": "<b>Original:</b>\n{original}\n\n<b>✨ Proposal:</b>\n<code>{optimized}</code>", "de": "<b>Original:</b>\n{original}\n\n<b>✨ Vorschlag:</b>\n<code>{optimized}</code>", "ru": "<b>Оригинал:</b>\n{original}\n\n<b>✨ Предложение:</b>\n<code>{optimized}</code>", "kk": "<b>Түпнұсқа:</b>\n{original}\n\n<b>✨ Ұсыныс:</b>\n<code>{optimized}</code>" },
    "btn_accept": { "en": "✅ Use Proposal", "de": "✅ Vorschlag nehmen", "ru": "✅ Принять", "kk": "✅ Қабылдау" },
    "btn_edit": { "en": "✏️ Edit", "de": "✏️ Ändern", "ru": "✏️ Изменить", "kk": "✏️ Өзгерту" },
    "btn_reject": { "en": "❌ Original", "de": "❌ Original", "ru": "❌ Оригинал", "kk": "❌ Түпнұсқа" },
    
    # --- SHARE ---
    "share_menu_title": { "en": "<b>Invite Friends!</b>\nLink: <code>{ref_link}</code>", "de": "<b>Freunde werben!</b>\nLink: <code>{ref_link}</code>", "ru": "<b>Пригласи друзей!</b>\nLink: <code>{ref_link}</code>", "kk": "<b>Достарды шақыр!</b>\nLink: <code>{ref_link}</code>" },
    "share_text_template": { "en": "Check out this AI Bot! {ref_link}", "de": "Schau dir diesen AI Bot an! {ref_link}", "ru": "Попробуй этот ИИ-бот! {ref_link}", "kk": "Мына AI ботты көр! {ref_link}" },
    "ref_success_referrer": { "en": "🎉 +{amount} Credits!", "de": "🎉 +{amount} Credits!", "ru": "🎉 +{amount} Кредитов!", "kk": "🎉 +{amount} Кредит!" },
    "btn_share_vk": {"en": "VK", "de": "VK", "ru": "VK", "kk": "VK"},
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
    "daily_news_on": { "en": "Daily News: ON", "de": "Daily News: AN", "ru": "Новости: ВКЛ", "kk": "Жаңалықтар: ҚОСУ" },
    "daily_news_off": { "en": "Daily News: OFF", "de": "Daily News: AUS", "ru": "Новости: ВЫКЛ", "kk": "Жаңалықтар: ӨШІРУ" }
}

def get_text(key, lang="en"):
    return STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("en", key))