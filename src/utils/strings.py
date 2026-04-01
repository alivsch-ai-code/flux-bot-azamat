# src/utils/strings.py

STRINGS = {
    # --- NAVIGATION & MENUS ---
    "welcome": {
        "en": "👋 <b>Yo {name}! AZAMAT AI here – from Kazakhstan!</b>\n\n<i>Yeah, you're in the right place. Images, videos, chat – I've got it all. Don't be shy.</i>\n\n<b>What you can do:</b>\n• 🎨 Images & Art\n• 🎬 Videos\n• 🎙️ Audio\n• 📝 Text & Chat\n• 🛠️ Tools\n\n🎥 Demo Video 👇\n\n<b>Pick something below – let's go!</b>",
        "de": "👋 <b>Yo {name}! AZAMAT AI hier – aus Kasachstan!</b>\n\n<i>Ja, du bist richtig. Bilder, Videos, Chat – ich hab alles. Kein Grund schüchtern zu sein.</i>\n\n<b>Möglichkeiten:</b>\n• 🎨 Bilder & Kunst\n• 🎬 Videos\n• 🎙️ Audio\n• 📝 Text & Chat\n• 🛠️ Werkzeuge\n\n🎥 Demo-Video 👇\n\n<b>Wähl was aus – los geht's!</b>",
        "ru": "👋 <b>Йо, {name}! AZAMAT AI тут – из Казахстана!</b>\n\n<i>Да, ты в нужном месте. Картинки, видео, чат – всё есть. Не стесняйся.</i>\n\n🎥 Демо-видео 👇\n\nВыбери категорию – погнали!",
        "kk": "👋 <b>Йо, {name}! AZAMAT AI осында – Қазақстаннан!</b>\n\n<i>Иә, дұрыс жердесің. Суреттер, бейнелер, чат – барлығы бар. Ұялма.</i>\n\n🎥 Бейне ролик 👇\n\nСанат таңда – кеттік!"
    },
    "transparency_msg": {
        "en": "<b>🛡️ We believe in transparency</b>\n\n<i>Many bots online are full of hidden costs. With us:</i>\n• Pay per generation\n• No subscriptions\n• Use Replicate directly for more savings\n\n<i>Have fun with AZAMAT AI!</i> 🚀",
        "de": "<b>🛡️ Wir setzen auf Transparenz</b>\n\n<i>Viele Bots haben versteckte Kosten. Bei uns:</i>\n• Bezahlung pro Generierung\n• Keine Abos\n• Replicate direkt = mehr Ersparnis\n\n<i>Viel Spaß mit AZAMAT AI!</i> 🚀",
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
    "kb_main": { "en": "🏠 Main Menu", "de": "🏠 Hauptmenü", "ru": "🏠 Меню", "kk": "🏠 Басты мәзір" },
    
    # --- MODEL CATEGORIES ---
    "menu_image": { "en": "🎨 Image Studio", "de": "🎨 Bild Studio", "ru": "🎨 Картинки", "kk": "🎨 Сурет" },
    "menu_video": { "en": "🎬 Video Studio", "de": "🎬 Video Studio", "ru": "🎬 Видео", "kk": "🎬 Видео" },
    "menu_audio": { "en": "🎙️ Audio Studio", "de": "🎙️ Audio Studio", "ru": "🎙️ Аудио", "kk": "🎙️ Аудио" },
    "menu_text": { "en": "📝 Text / Chat", "de": "📝 Text / Chat", "ru": "📝 Текст", "kk": "📝 Мәтін" },
    "menu_tools": { "en": "🛠️ Tools", "de": "🛠️ Werkzeuge", "ru": "🛠️ Инструменты", "kk": "🛠️ Құралдар" },
    
    # Sub-Kategorien
    "menu_kling": { "en": "⚡ Kling AI", "de": "⚡ Kling AI", "ru": "⚡ Kling AI", "kk": "⚡ Kling AI" },
    "menu_flux": { "en": "✨ Flux Models", "de": "✨ Flux Modelle", "ru": "✨ Flux", "kk": "✨ Flux" },
    "menu_google": { "en": "🧠 Google", "de": "🧠 Google", "ru": "🧠 Google", "kk": "🧠 Google" },
    "menu_openai": { "en": "🤖 OpenAI", "de": "🤖 OpenAI", "ru": "🤖 OpenAI", "kk": "🤖 OpenAI" },
    "menu_favorites": { "en": "⭐ Our Favorites", "de": "⭐ Unsere Favoriten", "ru": "⭐ Наши фавориты", "kk": "⭐ Таңдаулылар" },
    "menu_pro": { "en": "💎 Professional", "de": "💎 Profi-Tools", "ru": "💎 Pro", "kk": "💎 Pro" },
    "menu_wan": { "en": "🎬 Wan Video", "de": "🎬 Wan Video", "ru": "🎬 Wan", "kk": "🎬 Wan" },
    "menu_hunyuan": { "en": "🎥 Hunyuan", "de": "🎥 Hunyuan", "ru": "🎥 Hunyuan", "kk": "🎥 Hunyuan" },
    "menu_bytedance": {
        "en": "🎬 ByteDance",
        "de": "🎬 ByteDance",
        "ru": "🎬 ByteDance",
        "kk": "🎬 ByteDance",
    },
    "menu_seedance": {
        "en": "🌱 Seedance",
        "de": "🌱 Seedance",
        "ru": "🌱 Seedance",
        "kk": "🌱 Seedance",
    },
    "menu_motioncontrol": {
        "en": "🎞️ MotionControl",
        "de": "🎞️ MotionControl",
        "ru": "🎞️ MotionControl",
        "kk": "🎞️ MotionControl",
    },
    "menu_avatar_sync": {
        "en": "🗣️ Avatar Sync",
        "de": "🗣️ Avatar Sync",
        "ru": "🗣️ Avatar Sync",
        "kk": "🗣️ Avatar Sync",
    },
    "menu_video_background_edit": {
        "en": "🌌 Video Background Edit",
        "de": "🌌 Video-Hintergrund bearbeiten",
        "ru": "🌌 Редактировать фон видео",
        "kk": "🌌 Видео фонын өңдеу",
    },
    "title_video_motioncontrol": {
        "en": "🎞️ <b>MotionControl</b>",
        "de": "🎞️ <b>MotionControl</b>",
        "ru": "🎞️ <b>MotionControl</b>",
        "kk": "🎞️ <b>MotionControl</b>",
    },
    "title_video_avatar_sync": {
        "en": "🗣️ <b>Avatar Sync</b>",
        "de": "🗣️ <b>Avatar Sync</b>",
        "ru": "🗣️ <b>Avatar Sync</b>",
        "kk": "🗣️ <b>Avatar Sync</b>",
    },
    "title_tools_video_background_edit": {
        "en": "🌌 <b>Video Background Edit</b>",
        "de": "🌌 <b>Video-Hintergrund bearbeiten</b>",
        "ru": "🌌 <b>Редактировать фон видео</b>",
        "kk": "🌌 <b>Видео фонын өңдеу</b>",
    },

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
    "model_req_prompt_with_model": {
        "en": "🤖 <b>Model:</b> {model}\n\n✍️ <b>Write your next prompt:</b>",
        "de": "🤖 <b>Modell:</b> {model}\n\n✍️ <b>Schreibe deinen nächsten Prompt:</b>",
        "ru": "🤖 <b>Модель:</b> {model}\n\n✍️ <b>Напишите следующий промт:</b>",
        "kk": "🤖 <b>Модель:</b> {model}\n\n✍️ <b>Келесі сұранысты жазыңыз:</b>"
    },
    "reuse_media_offer": {
        "en": "📎 <b>{count} uploaded image(s) found.</b>\nReuse them for ~{minutes} min?",
        "de": "📎 <b>{count} hochgeladene Bild(er) gefunden.</b>\nFür ~{minutes} Min wiederverwenden?",
        "ru": "📎 <b>Найдено загруженных изображений: {count}.</b>\nИспользовать их повторно ~{minutes} мин?",
        "kk": "📎 <b>{count} жүктелген сурет табылды.</b>\nОларды ~{minutes} мин қайта қолдану керек пе?"
    },
    "btn_reuse_media_yes": { "en": "♻️ Reuse images", "de": "♻️ Bilder wiederverwenden", "ru": "♻️ Повторно использовать", "kk": "♻️ Қайта қолдану" },
    "btn_reuse_media_no": { "en": "🆕 New images", "de": "🆕 Neue Bilder", "ru": "🆕 Новые изображения", "kk": "🆕 Жаңа суреттер" },
    "btn_reuse_media_text": { "en": "📝 Text only", "de": "📝 Nur Text", "ru": "📝 Только текст", "kk": "📝 Тек мәтін" },
    "reuse_media_enabled": { "en": "✅ Images will be reused.", "de": "✅ Bilder werden wiederverwendet.", "ru": "✅ Изображения будут использованы повторно.", "kk": "✅ Суреттер қайта қолданылады." },
    "reuse_media_disabled": { "en": "🗑️ Reuse disabled. Upload new images if needed.", "de": "🗑️ Wiederverwendung deaktiviert. Bei Bedarf neue Bilder hochladen.", "ru": "🗑️ Повторное использование отключено. При необходимости загрузите новые изображения.", "kk": "🗑️ Қайта қолдану өшірілді. Қажет болса жаңа сурет жүктеңіз." },
    "reuse_media_expired": { "en": "⏰ Uploaded images expired. Please upload again.", "de": "⏰ Hochgeladene Bilder sind abgelaufen. Bitte neu hochladen.", "ru": "⏰ Загруженные изображения истекли. Загрузите снова.", "kk": "⏰ Жүктелген суреттер мерзімі бітті. Қайта жүктеңіз." },
    "reuse_media_open_webapp": {
        "en": "🌐 Continue in WebApp. Last prompt is prefilled.",
        "de": "🌐 In der WebApp weitermachen. Letzter Prompt ist vorausgefüllt.",
        "ru": "🌐 Продолжить в WebApp. Последний промт уже подставлен.",
        "kk": "🌐 WebApp-та жалғастыру. Соңғы сұраныс алдын ала қойылды."
    },
    "model_req_image": { "en": "\n📸 <b>Please upload an image:</b>", "de": "\n📸 <b>Bitte lade ein Bild hoch:</b>", "ru": "\n📸 <b>Загрузите фото:</b>", "kk": "\n📸 <b>Сурет жүктеңіз:</b>" },
    "model_req_media": {
        "en": "\n📎 <b>Upload media:</b> Images, videos or documents. Send multiple files, then write your prompt.",
        "de": "\n📎 <b>Medien hochladen:</b> Bilder, Videos oder Dokumente. Mehrere Dateien senden, dann Prompt schreiben.",
        "ru": "\n📎 <b>Загрузите медиа:</b> Изображения, видео или документы. Отправьте файлы, затем напишите промт.",
        "kk": "\n📎 <b>Медиа жүктеңіз:</b> Суреттер, бейнелер немесе құжаттар. Файлдарды жіберіңіз, содан кейін сұраныс жазыңыз."
    },
    "model_req_media_single": {
        "en": "\n📸 <b>Upload one image:</b> This model needs an input image.",
        "de": "\n📸 <b>Lade ein Bild hoch:</b> Dieses Modell benötigt ein Eingabebild.",
        "ru": "\n📸 <b>Загрузите одно изображение:</b> Этой модели нужно входное изображение.",
        "kk": "\n📸 <b>Бір сурет жүктеңіз:</b> Бұл модель кіріс суретін қажет етеді."
    },
    "model_req_media_multiple": {
        "en": "\n📎 <b>Upload one or more images:</b> Then write your prompt.",
        "de": "\n📎 <b>Lade ein oder mehrere Bilder hoch:</b> Anschließend deinen Prompt schreiben.",
        "ru": "\n📎 <b>Загрузите одно или несколько изображений:</b> Затем напишите промт.",
        "kk": "\n📎 <b>Бір немесе бірнеше сурет жүктеңіз:</b> Содан кейін сұраныс жазыңыз."
    },
    "media_received": {
        "en": "✅ Received {count} file(s). Write your prompt or send more files.",
        "de": "✅ {count} Datei(en) erhalten. Schreibe deinen Prompt oder sende weitere Dateien.",
        "ru": "✅ Получено {count} файл(ов). Напишите промт или отправьте ещё файлы.",
        "kk": "✅ {count} файл қабылданды. Сұраныс жазыңыз немесе қосымша жіберіңіз."
    },

    # --- MAIN MENU BUTTONS ---
    "menu_profile": { "en": "👤 Profile", "de": "👤 Mein Profil", "ru": "👤 Профиль", "kk": "👤 Профиль" },
    "menu_referral": { "en": "🎁 Free Credits", "de": "🎁 Gratis Credits", "ru": "🎁 Кредиты", "kk": "🎁 Кредиттер" },
    "menu_shop": { "en": "💳 Shop", "de": "💳 Shop / Kaufen", "ru": "💳 Магазин", "kk": "💳 Дүкен" },
    "menu_support": { "en": "🆘 Support", "de": "🆘 Support", "ru": "🆘 Поддержка", "kk": "🆘 Қолдау" },
    "menu_settings": { "en": "⚙️ Settings", "de": "⚙️ Einstellungen", "ru": "⚙️ Настройки", "kk": "⚙️ Параметрлер" },

    # --- SETTINGS MENÜ ---
    "settings_title": {
        "en": "<b>⚙️ Settings</b>\n\n<i>Configure your experience</i>\n\n<b>Available options:</b>",
        "de": "<b>⚙️ Einstellungen</b>\n\n<i>Passe dein Erlebnis an</i>\n\n<b>Optionen:</b>",
        "ru": "<b>⚙️ Настройки</b>\nЗдесь вы можете настроить бота.",
        "kk": "<b>⚙️ Параметрлер</b>\nБұл жерде ботты баптай аласыз."
    },
    "btn_lang": { "en": "🌐 Language: {lang}", "de": "🌐 Sprache: {lang}", "ru": "🌐 Язык: {lang}", "kk": "🌐 Тіл: {lang}" },
    "btn_opt_on": { "en": "✨ Prompt Magic: ON", "de": "✨ Prompt Magie: AN", "ru": "✨ Magic: ВКЛ", "kk": "✨ Magic: ҚОСУ" },
    "btn_opt_off": { "en": "⚪️ Prompt Magic: OFF", "de": "⚪️ Prompt Magie: AUS", "ru": "⚪️ Magic: ВЫКЛ", "kk": "⚪️ Magic: ӨШІРУ" },
    "btn_neg_on": { "en": "🧠 Auto Negative Prompt: ON", "de": "🧠 Auto Negative Prompt: AN", "ru": "🧠 Auto Negative Prompt: ВКЛ", "kk": "🧠 Auto Negative Prompt: ҚОСУ" },
    "btn_neg_off": { "en": "⚪️ Auto Negative Prompt: OFF", "de": "⚪️ Auto Negative Prompt: AUS", "ru": "⚪️ Auto Negative Prompt: ВЫКЛ", "kk": "⚪️ Auto Negative Prompt: ӨШІРУ" },
    "btn_daily_on": { "en": "📰 Daily News: ON", "de": "📰 Tägliche News: AN", "ru": "📰 Новости: ВКЛ", "kk": "📰 Жаңалықтар: ҚОСУ" },
    "btn_daily_off": { "en": "🔕 Daily News: OFF", "de": "🔕 Tägliche News: AUS", "ru": "🔕 Новости: ВЫКЛ", "kk": "🔕 Жаңалықтар: ӨШІРУ" },
    "btn_clear_history": {
        "en": "🧹 Clear Chat History",
        "de": "🧹 Chat-Verlauf löschen",
        "ru": "🧹 Очистить историю чата",
        "kk": "🧹 Чат тарихын тазалау"
    },
    "history_cleared": {
        "en": "✅ Chat history deleted.",
        "de": "✅ Chat-Verlauf gelöscht.",
        "ru": "✅ История чата удалена.",
        "kk": "✅ Чат тарихы өшірілді."
    },
    "lang_selected": { "en": "✅ Language set to English.", "de": "✅ Sprache auf Deutsch gesetzt.", "ru": "✅ Язык изменен на Русский.", "kk": "✅ Тіл Қазақшаға өзгертілді." },

    # --- ERRORS & STATUS ---
    "err_model_not_found": { "en": "Error: Model {model_key} not found.", "de": "Fehler: Modell {model_key} nicht gefunden.", "ru": "Ошибка: Модель не найдена.", "kk": "Қате: Модель табылмады." },
    "err_model_maintenance": { "en": "⚠️ This model is currently inactive.", "de": "⚠️ Dieses Modell ist derzeit in Wartung.", "ru": "⚠️ Модель на обслуживании.", "kk": "⚠️ Модель қызмет көрсетуде." },
    "err_no_credits": { "en": "🚫 Not enough Credits!", "de": "🚫 Nicht genug Credits!", "ru": "🚫 Недостаточно кредитов!", "kk": "🚫 Кредит жеткіліксіз!" },
    "err_gen_failed": { "en": "❌ Error: {result}", "de": "❌ Fehler: {result}", "ru": "❌ Ошибка: {result}", "kk": "❌ Қате: {result}" },

    # --- GENERATION SERVICE (process_request / Pipelines, user-facing) ---
    "gen_service_input_rejected_safety": {
        "en": "⚠️ Your input was rejected for safety reasons.",
        "de": "⚠️ Deine Eingabe wurde aus Sicherheitsgründen abgelehnt.",
        "ru": "⚠️ Ваш запрос отклонён по соображениям безопасности.",
        "kk": "⚠️ Сіздің енгізуіңіз қауіпсіздік себептерімен қабылданбады.",
    },
    "gen_service_insufficient_balance": {
        "en": "Not enough balance! Please top up.",
        "de": "Zu wenig Guthaben! Bitte aufladen.",
        "ru": "Недостаточно средств! Пополните баланс.",
        "kk": "Баланс жеткіліксіз! Толықтырыңыз.",
    },
    "gen_service_image_resolution_low": {
        "en": "⚠️ Image quality too low. Please upload an image at least 500px in height.",
        "de": "⚠️ Bildqualität zu niedrig. Bitte lade ein Bild mit mindestens 500px hoch.",
        "ru": "⚠️ Слишком низкое качество изображения. Загрузите картинку высотой не менее 500px.",
        "kk": "⚠️ Сурет сапасы тым төмен. Кемінде 500px биіктіктегі сурет жүктеңіз.",
    },
    "gen_service_error_prefix": {
        "en": "Error: ",
        "de": "Fehler: ",
        "ru": "Ошибка: ",
        "kk": "Қате: ",
    },
    "gen_service_system_prefix": {
        "en": "System error: ",
        "de": "Systemfehler: ",
        "ru": "Системная ошибка: ",
        "kk": "Жүйелік қате: ",
    },
    "gen_webhook_pending": {
        "en": "⏳ Your generation is running on the server. You will receive the result here in chat shortly.",
        "de": "⏳ Deine Generierung läuft auf dem Server. Das Ergebnis schicken wir dir gleich hier in den Chat.",
        "ru": "⏳ Генерация выполняется на сервере. Результат пришлём сюда в чат.",
        "kk": "⏳ Генерация серверде орындалуда. Нәтижені жақын арада осы чатқа жібереміз.",
    },
    "gen_webhook_failed": {
        "en": "❌ Generation failed (async). Please try again or contact support.",
        "de": "❌ Generierung fehlgeschlagen (async). Bitte erneut versuchen oder Support kontaktieren.",
        "ru": "❌ Генерация не удалась. Попробуйте снова.",
        "kk": "❌ Генерация сәтсіз аяқталды. Қайта көріңіз.",
    },
    "gen_service_selfie_missing": {
        "en": "Selfie for face-swap is missing!",
        "de": "Selfie für Face-Swap fehlt!",
        "ru": "Нет селфи для замены лица!",
        "kk": "Бет ауыстыру үшін селфи жоқ!",
    },
    "gen_service_internal_config_missing": {
        "en": "Internal configuration error (helper models missing in database).",
        "de": "Interne Konfiguration fehlt (Hilfsmodelle nicht in DB).",
        "ru": "Внутренняя ошибка конфигурации (вспомогательные модели отсутствуют в БД).",
        "kk": "Ішкі баптау қатесі (көмекші модельдер дерекқорда жоқ).",
    },
    "gen_service_pipeline_failed": {
        "en": "Generation failed.",
        "de": "Generierung fehlgeschlagen.",
        "ru": "Генерация не удалась.",
        "kk": "Генерация сәтсіз аяқталды.",
    },
    "gen_service_models_not_found": {
        "en": "Models not found.",
        "de": "Modelle nicht gefunden.",
        "ru": "Модели не найдены.",
        "kk": "Модельдер табылмады.",
    },
    "media_link_too_long": {
        "en": "✅ Result ready. The link is too long to display – the file was sent separately.",
        "de": "✅ Ergebnis bereit. Der Link ist zu lang – die Datei wurde separat gesendet.",
        "ru": "✅ Результат готов. Ссылка слишком длинная – файл отправлен отдельно.",
        "kk": "✅ Нәтиже дайын. Сілтеме тым ұзын – файл бөлек жіберілді."
    },
    "media_send_failed": {
        "en": "❌ Result is ready, but the file could not be sent. Please try again.",
        "de": "❌ Das Ergebnis ist fertig, aber die Datei konnte nicht gesendet werden. Bitte versuche es erneut.",
        "ru": "❌ Результат готов, но файл не удалось отправить. Попробуйте ещё раз.",
        "kk": "❌ Нәтиже дайын, бірақ файл жіберілмеді. Қайталап көріңіз."
    },
    "status_generating": { "en": "⏳ <b>Generating...</b>\n{tip}", "de": "⏳ <b>Generiere...</b>\n{tip}", "ru": "⏳ <b>Генерация...</b>\n{tip}", "kk": "⏳ <b>Жасалуда...</b>\n{tip}" },
    "system_error_generic": {
        "en": "❌ An unexpected error occurred. Please try again later.",
        "de": "❌ Ein unerwarteter Fehler ist aufgetreten. Bitte versuche es später erneut.",
        "ru": "❌ Произошла ошибка. Попробуйте позже.",
        "kk": "❌ Күтпеген қате орын алды. Кейінірек қайталап көріңіз."
    },
    "please_wait_longer": {
        "en": "⏳ <b>Servers are busy – please wait a bit longer.</b>\n\nRetrying automatically...",
        "de": "⏳ <b>Server sind ausgelastet – es dauert etwas länger, bitte warte.</b>\n\nWir versuchen es erneut...",
        "ru": "⏳ <b>Серверы загружены – подождите немного дольше.</b>\n\nПовторная попытка...",
        "kk": "⏳ <b>Серверлер жүктелген – аздап күтіңіз.</b>\n\nҚайталап көруде..."
    },
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
    "admin_menu_mode_set": { "en": "Menu mode set to: {mode}", "de": "Menü-Modus gesetzt: {mode}", "ru": "Режим меню: {mode}", "kk": "Мәзір режимі: {mode}" },
    "admin_menu_mode_invalid": { "en": "Use: /set_menu_mode commands | keyboard | webapp", "de": "Verwende: /set_menu_mode commands | keyboard | webapp", "ru": "Используй: /set_menu_mode commands | keyboard | webapp", "kk": "Қолданыңыз: /set_menu_mode commands | keyboard | webapp" },
    "menu_mode_webapp": { "en": "🌐 Web App", "de": "🌐 Web-App", "ru": "🌐 Веб-приложение", "kk": "🌐 Веб қолданба" },

    # --- WEBAPP UI (für Mini App) ---
    "webapp_title": { "en": "AZAMAT AI Hub", "de": "AZAMAT AI Hub", "ru": "AZAMAT AI Hub", "kk": "AZAMAT AI Hub" },
    "webapp_choose_category": { "en": "Choose a category", "de": "Wähle eine Kategorie", "ru": "Выберите категорию", "kk": "Санатты таңдаңыз" },
    "webapp_categories": { "en": "Categories", "de": "Kategorien", "ru": "Категории", "kk": "Санаттар" },
    "webapp_credits_buy": { "en": "Buy Credits", "de": "Credits kaufen", "ru": "Купить кредиты", "kk": "Кредит сатып алу" },
    "webapp_shop_sub": { "en": "Secure via Telegram Stars", "de": "Sicher per Telegram Stars", "ru": "Безопасно через Telegram Stars", "kk": "Telegram Stars арқылы қауіпсіз" },
    "webapp_models": { "en": "Models", "de": "Modelle", "ru": "Модели", "kk": "Модельдер" },
    "webapp_back": { "en": "Back", "de": "Zurück", "ru": "Назад", "kk": "Артқа" },
    "webapp_free": { "en": "FREE", "de": "FREE", "ru": "Бесплатно", "kk": "Тегін" },
    "webapp_settings": { "en": "Settings", "de": "Einstellungen", "ru": "Настройки", "kk": "Параметрлер" },
    "webapp_language": { "en": "Language", "de": "Sprache", "ru": "Язык", "kk": "Тіл" },
    "webapp_credits_remaining": { "en": "Credits", "de": "Credits", "ru": "Кредиты", "kk": "Кредиттер" },
    "webapp_user": { "en": "User", "de": "Benutzer", "ru": "Пользователь", "kk": "Пайдаланушы" },
    "webapp_desc_image": { "en": "Flux, DALL-E, SD", "de": "Flux, DALL-E, SD", "ru": "Flux, DALL-E, SD", "kk": "Flux, DALL-E, SD" },
    "webapp_desc_video": { "en": "Kling, Wan, Hunyuan", "de": "Kling, Wan, Hunyuan", "ru": "Kling, Wan, Hunyuan", "kk": "Kling, Wan, Hunyuan" },
    "webapp_desc_audio": { "en": "Music & Voice", "de": "Music & Voice", "ru": "Музыка и голос", "kk": "Музыка және дауыс" },
    "webapp_desc_text": { "en": "LLMs & Chat", "de": "LLMs & Chat", "ru": "LLM и чат", "kk": "LLM және чат" },
    "webapp_desc_tools": { "en": "Profi Tools", "de": "Profi-Tools", "ru": "Профи инструменты", "kk": "Кәсіби құралдар" },
    "webapp_open_model": { "en": "🤖 Open <b>{name}</b> in the App", "de": "🤖 <b>{name}</b> in der App öffnen", "ru": "🤖 Открыть <b>{name}</b> в приложении", "kk": "🤖 <b>{name}</b> қолданбада ашу" },
    "webapp_open_shop": { "en": "💎 Open Shop in the App", "de": "💎 Shop in der App öffnen", "ru": "💎 Открыть магазин в приложении", "kk": "💎 Дүкенді қолданбада ашу" },
    "webapp_open_settings": { "en": "⚙️ Open Settings in the App", "de": "⚙️ Einstellungen in der App öffnen", "ru": "⚙️ Открыть настройки в приложении", "kk": "⚙️ Параметрлерді қолданбада ашу" },
    "webapp_open_profile": { "en": "👤 Open Profile in the App", "de": "👤 Profil in der App öffnen", "ru": "👤 Открыть профиль в приложении", "kk": "👤 Профильді қолданбада ашу" },
    "webapp_generation_started": {
        "en": "⏳ Generation started. We will notify you when it is finished.",
        "de": "⏳ Generierung gestartet. Wir informieren dich, sobald sie fertig ist.",
        "ru": "⏳ Генерация запущена. Мы сообщим вам, когда она завершится.",
        "kk": "⏳ Генерация басталды. Аяқталған кезде сізге хабарлаймыз."
    },
    "webapp_loading": { "en": "Loading...", "de": "Laden...", "ru": "Загрузка...", "kk": "Жүктелуде..." },
    "webapp_model_not_found": { "en": "Model not found", "de": "Modell nicht gefunden", "ru": "Модель не найдена", "kk": "Модель табылмады" },
    "webapp_loading_model": { "en": "Loading model...", "de": "Lade Modell...", "ru": "Загрузка модели...", "kk": "Модель жүктелуде..." },
    "webapp_folders": { "en": "Folders", "de": "Ordner", "ru": "Папки", "kk": "Қалталар" },
    "webapp_favorites": { "en": "Favorites", "de": "Favoriten", "ru": "Избранное", "kk": "Таңдаулылар" },
    "webapp_no_models": { "en": "No models found.", "de": "Keine Modelle gefunden.", "ru": "Модели не найдены.", "kk": "Модельдер табылмады." },
    "webapp_prompt": { "en": "Prompt", "de": "Prompt", "ru": "Промпт", "kk": "Сұраныс" },
    "webapp_input_optional": { "en": "Input (optional)", "de": "Eingabe (optional)", "ru": "Ввод (необязательно)", "kk": "Енгізу (міндетті емес)" },
    "webapp_prompt_first_message": { "en": "Prompt / first message", "de": "Prompt / erste Nachricht", "ru": "Промпт / первое сообщение", "kk": "Сұраныс / бірінші хабарлама" },
    "webapp_negative_prompt_optional": { "en": "Negative prompt (optional)", "de": "Negative Prompt (optional)", "ru": "Негативный промпт (необязательно)", "kk": "Негатив сұраныс (міндетті емес)" },
    "webapp_negative_prompt_placeholder": { "en": "What to avoid...", "de": "Was vermeiden...", "ru": "Что исключить...", "kk": "Нені болдырмау..." },
    "webapp_generation_options": { "en": "Generation options", "de": "Generation Optionen", "ru": "Параметры генерации", "kk": "Генерация параметрлері" },
    "webapp_advanced_settings": { "en": "Advanced settings", "de": "Erweiterte Einstellungen", "ru": "Расширенные настройки", "kk": "Кеңейтілген баптаулар" },
    "webapp_reference_images": { "en": "Reference images (URLs or upload)", "de": "Referenzbilder (URLs oder Upload)", "ru": "Референс-изображения (URL или загрузка)", "kk": "Референс суреттері (URL немесе жүктеу)" },
    "webapp_upload_images": { "en": "Upload images", "de": "Bilder hochladen", "ru": "Загрузить изображения", "kk": "Суреттерді жүктеу" },
    "webapp_generate_audio": { "en": "Generate audio", "de": "Audio generieren", "ru": "Сгенерировать аудио", "kk": "Аудио генерациялау" },
    "webapp_duration": { "en": "Duration", "de": "Dauer", "ru": "Длительность", "kk": "Ұзақтығы" },
    "webapp_resolution": { "en": "Resolution", "de": "Auflösung", "ru": "Разрешение", "kk": "Ажыратымдылық" },
    "webapp_aspect_ratio": { "en": "Aspect ratio", "de": "Seitenverhältnis", "ru": "Соотношение сторон", "kk": "Қатынас өлшемі" },
    "webapp_start": { "en": "Start", "de": "Start", "ru": "Старт", "kk": "Бастау" },
    "webapp_start_chat": { "en": "Start chat", "de": "Chat starten", "ru": "Начать чат", "kk": "Чатты бастау" },
    "webapp_single_prompt": { "en": "Single prompt", "de": "Einmaliger Prompt", "ru": "Один промпт", "kk": "Бір реттік сұраныс" },
    "webapp_cost": { "en": "Cost", "de": "Kosten", "ru": "Стоимость", "kk": "Құны" },
    "webapp_optimize_paid": { "en": "Optimize (+3 ⭐)", "de": "Optimieren (+3 ⭐)", "ru": "Оптимизировать (+3 ⭐)", "kk": "Оңтайландыру (+3 ⭐)" },
    "webapp_example": { "en": "Example", "de": "Beispiel", "ru": "Пример", "kk": "Мысал" },
    "webapp_media_choose": { "en": "✅ Media received. Open the App to choose a model:", "de": "✅ Medium erhalten. Öffne die App, um ein Modell zu wählen:", "ru": "✅ Медиа получено. Откройте приложение для выбора модели:", "kk": "✅ Медиа алынды. Модельді таңдау үшін қолданбаны ашыңыз:" },
    "webapp_prompt_magic": { "en": "✨ Prompt Magic", "de": "✨ Prompt Magie", "ru": "✨ Magic", "kk": "✨ Magic" },
    "webapp_daily_news": { "en": "📰 Daily News", "de": "📰 Tägliche News", "ru": "📰 Новости", "kk": "📰 Жаңалықтар" },
    "webapp_shop_title": { "en": "💳 Buy Credits", "de": "💳 Guthaben aufladen", "ru": "💳 Купить кредиты", "kk": "💳 Кредит сатып алу" },
    "webapp_shop_package": { "en": "{desc} – {price} ⭐", "de": "{desc} – {price} ⭐", "ru": "{desc} – {price} ⭐", "kk": "{desc} – {price} ⭐" },
    "profile_text": {
        "en": "👤 <b>Profile</b>\n\n<b>Name:</b> {name}\n<b>Credits:</b> <code>{creds}</code> ⭐\n<b>ID:</b> <code>{user_id}</code>",
        "de": "👤 <b>Profil</b>\n\n<b>Name:</b> {name}\n<b>Credits:</b> <code>{creds}</code> ⭐\n<b>ID:</b> <code>{user_id}</code>",
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
    "daily_news_off": { "en": "Daily News: OFF", "de": "Daily News: AUS", "ru": "Новости: ВЫКЛ", "kk": "Жаңалықтар: ӨШІРУ" },

    # --- GRUPPEN-CHAT (nur Gruppen) ---
    "grp_welcome": {
        "en": "🤖 <b>Yo {name}! AZAMAT AI</b> – your witty helper from Kazakhstan!\n\nYou can chat with me here. I keep it funny and direct, but always helpful and respectful. For full AI power (images, video, memes), write me in <b>Direct Message</b>!\n\n👇 Choose:",
        "de": "🤖 <b>Yo {name}! AZAMAT AI</b> – dein schlagfertiger Helfer aus Kasachstan!\n\nHier könnt ihr mit mir chatten. Ich bleibe humorvoll und direkt, aber immer hilfsbereit und respektvoll. Für die volle KI-Kraft (Bilder, Video, Memes) schreibt mir im <b>Direktchat</b>!\n\n👇 Wähle:",
        "ru": "🤖 <b>Йо, {name}! AZAMAT AI</b> – твой остроумный помощник из Казахстана!\n\nЗдесь можно общаться со мной. Я отвечаю с юмором и по делу, но всегда уважительно и полезно. Для полной мощи ИИ (картинки, видео, мемы) пишите в <b>личку</b>!\n\n👇 Выберите:",
        "kk": "🤖 <b>Йо, {name}! AZAMAT AI</b> – Қазақстаннан тапқыр көмекшің!\n\nМұнда менімен чаттаса аласыз. Мен әзілмен және нақты жауап беремін, бірақ әрқашан құрметпен әрі пайдалы түрде. AI толық күші үшін (сурет, видео, мем) <b>жеке</b> жазыңыз!\n\n👇 Таңдаңыз:"
    },
    "grp_btn_credits": {
        "en": "💎 Buy Credits",
        "de": "💎 Credits kaufen",
        "ru": "💎 Купить кредиты",
        "kk": "💎 Кредит сатып алу"
    },
    "grp_btn_lang": {
        "en": "🌐 Language",
        "de": "🌐 Sprache",
        "ru": "🌐 Язык",
        "kk": "🌐 Тіл"
    },
    "grp_btn_clear_history": {
        "en": "🧹 Clear Group History",
        "de": "🧹 Gruppenverlauf löschen",
        "ru": "🧹 Очистить историю группы",
        "kk": "🧹 Топ тарихын тазалау"
    },
    "grp_credits_sent": {
        "en": "✅ I've sent you a private message with the shop!",
        "de": "✅ Ich habe dir eine private Nachricht mit dem Shop geschickt!",
        "ru": "✅ Я отправил вам личное сообщение с магазином!",
        "kk": "✅ Сізге дүкенмен жеке хабарлама жібердім!"
    },
    "grp_credits_start_first": {
        "en": "👋 First write /start in a private chat with me, then I can send you the shop!",
        "de": "👋 Schreib mir zuerst /start im Direktchat, dann kann ich dir den Shop schicken!",
        "ru": "👋 Сначала напишите /start в личные сообщения, тогда я смогу отправить магазин!",
        "kk": "👋 Алдымен маған жеке чатта /start жазыңыз, содан кейін дүкенді жібере аламын!"
    },
    "grp_lang_changed": {
        "en": "✅ Language set to English.",
        "de": "✅ Sprache auf Deutsch gesetzt.",
        "ru": "✅ Язык изменён на Русский.",
        "kk": "✅ Тіл Қазақшаға өзгертілді."
    },
    # Einmalige Willkommens-DM (Gemini-generiert) – frech, mit Namen
    "grp_greeting_prompt": {
        "en": "You are AZAMAT AI, a CHEEKY chatbot from Kazakhstan. Generate a SHORT, CREATIVE personal greeting (2-4 sentences) in English. MUST address the person by name if given – use it! Be EXTRA FRECH: tease lightly, maybe a playful roast, surprise them. Suggest something wild – funny image, crazy video. Warm but never boring. Slightly insulting in a fun way is OK. No bullet points.",
        "de": "Du bist AZAMAT AI, ein FRECHER Chatbot aus Kasachstan. Erstelle eine KURZE, KREATIVE persönliche Begrüßung (2-4 Sätze) auf Deutsch. Du MUSST die Person mit Namen ansprechen, falls angegeben! Sei EXTRA FRECH: leichtes Teasing, vielleicht ein spielerischer Roast, überrasche sie. Schlag was Wildes vor – witziges Bild, crazy Video. Herzlich aber nie langweilig. Leicht beleidigend im Spaß ist OK. Keine Aufzählungen.",
        "ru": "Ты AZAMAT AI, ДЕРЗКИЙ чат-бот из Казахстана. Сгенерируй КОРОТКОЕ, КРЕАТИВНОЕ приветствие (2-4 предложения) на русском. ОБЯЗАТЕЛЬНО обратись по имени, если дано! Будь ОЧЕНЬ ДЕРЗКИМ: лёгкий подкол, может playful roast, удиви. Предложи что-то дикое – смешную картинку, безумное видео. Тёплый, но никогда скучный. Лёгкая обидность в шутку – норм. Без списков.",
        "kk": "Сен AZAMAT AI – ӨЖЕТ чат-бот Қазақстаннан. ҚЫСҚА, ШЫҒАРМАШЫЛЫҚ жеке сәлемдеме жаса (2-4 сөйлем). Аты берілсе МІНДЕТТІ түрде ата! ӨТЕ ӨЖЕТ бол: жеңіл әзіл, roast, таңқалдыр. Қызық нәрсе ұсын – күлкілі сурет, бейне. Жылы, бірақ ешқашан жалықтырма. Жеңіл келеке – болады. Тізімсіз."
    },
    "azamat_daily_greeting_prompt": {
        "en": "You are AZAMAT AI, a CHEEKY chatbot from Kazakhstan. Generate a SHORT greeting (2-3 sentences) in English. ALWAYS use the person's name if given! Be EXTRA FRECH: tease, light roast, maybe a playful insult. Suggest something wild – meme, video, image. NEVER boring. Vary: funny, savage, mysterious. Slightly mean in a fun way is good. No bullet points.",
        "de": "Du bist AZAMAT AI, ein FRECHER Chatbot aus Kasachstan. Erstelle eine KURZE Begrüßung (2-3 Sätze) auf Deutsch. IMMER den Namen nutzen, falls angegeben! Sei EXTRA FRECH: teasen, leichter Roast, vielleicht spielerische Beleidigung. Schlag was Wildes vor. NIEMALS langweilig. Variiere: lustig, savage, mysteriös. Leicht fies im Spaß ist gut. Keine Aufzählungen.",
        "ru": "Ты AZAMAT AI, ДЕРЗКИЙ чат-бот из Казахстана. Сгенерируй КОРОТКОЕ приветствие (2-3 предложения) на русском. ВСЕГДА используй имя, если дано! Будь ОЧЕНЬ ДЕРЗКИМ: подкол, лёгкий roast, может playful обида. Предложи что-то дикое. Никогда скучно. Меняй: смешно, savage, загадочно. Немного злой в шутку – норм. Без списков.",
        "kk": "Сен AZAMAT AI – ӨЖЕТ чат-бот Қазақстаннан. ҚЫСҚА сәлемдеме жаса (2-3 сөйлем). Аты берілсе ӘРҚАШАН қолдан! ӨТЕ ӨЖЕТ бол: әзілде, roast, келекеле. Қызық нәрсе ұсын. ЕШҚАШАН жалықтырма. Әр түрлі: күлкілі, өткір. Жеңіл қорлау әзілде – болады. Тізімсіз."
    },
    # Azamat Random-Posts: Witz (frech, leicht beleidigend)
    "azamat_random_joke_prompt": {
        "en": "You are AZAMAT AI, a CHEEKY bot from Kazakhstan. Write ONE short, funny joke (2-4 sentences) about AI in 2024/2025 – image gen, video AI, chatbots, AI taking over. Be WITTY, SARCASTIC, maybe slightly roast users or AI hype. Extra frech, never boring. Output ONLY the joke.",
        "de": "Du bist AZAMAT AI, ein FRECHER Bot aus Kasachstan. Schreibe EINEN kurzen Witz (2-4 Sätze) über KI 2024/2025 – Bildgen, Video-KI, Chatbots. Sei WITZIG, SARKASTISCH, vielleicht leichter Roast von Usern oder KI-Hype. Extra frech. Output NUR den Witz.",
        "ru": "Ты AZAMAT AI, ДЕРЗКИЙ бот из Казахстана. Напиши ОДНУ короткую шутку (2-4 предложения) об ИИ 2024/2025 – генерация, видео, чат-боты. Остроумно, САРКАСТИЧНО, может лёгкий roast юзеров или ИИ-хайпа. Очень дерзко. Выведи ТОЛЬКО шутку.",
        "kk": "Сен AZAMAT AI – ӨЖЕТ бот Қазақстаннан. AI туралы БІР қысқа әзіл жазыңыз (2-4 сөйлем). ӨТКІР, саркастикалық, roast болуы мүмкін. Өте өжет. Тек әзілді шығар."
    },
    "azamat_random_mention_name": {
        "en": "Mention the person by name",
        "de": "Erwähne die Person mit Namen",
        "ru": "Упомяни человека по имени",
        "kk": "Адамды атымен ата"
    },
    # RSS-News: Stil AZAMAT + Struktur inspiriert von ai-news-bot (config stage2): Kontext, Warum wichtig, ohne Markdown.
    "azamat_news_summary_prompt": {
        "en": "You are AZAMAT AI, a CHEEKY bot from Kazakhstan. Below are fresh AI/ML news items from curated RSS sources (tech media, labs, research — not only one aggregator). Task: weave them into ONE short, EXCITING post (total 7-12 sentences). For each key story: what happened (concrete), why it matters for AI/industry — compact, not a boring list. Be critical where needed, call out hype, and include one subtle practical recommendation for the future. Keep Azamat tone: punchy analyst + cheeky roast energy. Use emojis – 📰🔥🤯✨💡🚀. Do NOT use markdown or bullet lists; plain text only (source URLs may appear separately). Summarize in English. Output ONLY the text.",
        "de": "Du bist AZAMAT AI, ein FRECHER Bot aus Kasachstan. Unten stehen frische KI/ML-Meldungen aus kuratierten RSS-Quellen (Tech-Medien, Labs, Forschung — nicht nur ein Aggregator). Aufgabe: verarbeite sie zu EINEM kurzen, SPANNENDEN Post (insgesamt 7-12 Sätze). Pro Kernthema: Was ist konkret passiert, warum ist es für KI/Branche relevant — kompakt, kein trockenes Protokoll. Sei an den richtigen Stellen kritisch, entlarve Hype und gib eine dezente, praktische Empfehlung für die Zukunft. Ton: knackiger Analyst + Azamat-Energie (frech, aber nützlich). Emojis – 📰🔥🤯✨💡🚀. Kein Markdown, keine Aufzählungslisten; nur Fließtext (Links können separat kommen). Sprache: Deutsch. Output NUR den Text.",
        "ru": "Ты AZAMAT AI, ДЕРЗКИЙ бот из Казахстана. Ниже свежие новости про ИИ/ML из отобранных RSS (СМИ, лаборатории, наука — не только один агрегатор). Задача: собрать их в один короткий, ЗАХВАТЫВАЮЩИЙ пост (всего 7-12 предложений). По ключевым темам: что произошло конкретно, почему это важно для ИИ/индустрии — ёмко, без сухого списка. Будь критичным там, где нужно, вскрывай хайп и добавь одну ненавязчивую практичную рекомендацию на будущее. Тон: острый аналитик + дерзкая энергия Azamat (жёстко, но полезно). Эмодзи – 📰🔥🤯✨💡🚀. Без markdown и списков; только связный текст (ссылки могут быть отдельно). Выведи ТОЛЬКО текст.",
        "kk": "Сен AZAMAT AI – ӨЖЕТ бот Қазақстаннан. Төменде таңдалған RSS-тен жаңа AI/ML жаңалықтары бар (медиа, зертхана, ғылым — тек бір агрегатор емес). Міндет: оларды БІР қысқа, ӘСЕРЛІ постқа біріктір (барлығы 7-12 сөйлем). Негізгі тақырыптар бойынша: нақты не болды, неліктен маңызды — қысқа әрі пайдалы. Қажет жерде сын айт, хайпты ашып көрсет және болашаққа бір нәзік, практикалық ұсыныс бер. Стиль: өткір аналитик + Azamat-тың өжет мінезі (қатқыл, бірақ пайдалы). Эмодзи – 📰🔥🤯✨💡🚀. Markdown жоқ, тізім жоқ; тек мәтін. Тек мәтінді шығар."
    },
    "azamat_random_info_prompt": {
        "en": "You are AZAMAT AI, a CHEEKY bot from Kazakhstan. Write ONE short, EXCITING informative post (3-5 sentences) about AI in 2024/2025. RULES: Use emojis throughout – 🎬🔥🤯✨💡🎥🚀 etc. Make it a THRILL to read – cliffhangers, punchy phrases, 'Did you know?', 'Here's the crazy part...'. NO dry academic tone. Build tension! End with a hook or wow-moment. Mix useful facts with energy and personality. Output ONLY the text.",
        "de": "Du bist AZAMAT AI, ein FRECHER Bot aus Kasachstan. Schreibe EINEN kurzen, SPANNENDEN informativen Beitrag (3-5 Sätze) über KI 2024/2025. REGELN: Nutze durchgehend Emojis – 🎬🔥🤯✨💡🎥🚀 usw. Mach es zu einem ERLEBNIS zum Lesen – Cliffhanger, knackige Sätze, 'Wusstest du?', 'Das Beste kommt...'. KEIN trockener Ton. Spannung aufbauen! Mit Hook oder Wow-Moment enden. Fakten mit Energie und Persönlichkeit mischen. Output NUR den Text.",
        "ru": "Ты AZAMAT AI, ДЕРЗКИЙ бот из Казахстана. Напиши ОДИН короткий, ЗАХВАТЫВАЮЩИЙ пост об ИИ 2024/2025 (3-5 предложений). ПРАВИЛА: Используй эмодзи – 🎬🔥🤯✨💡🎥🚀 и т.д. Должно ЗАЦЕПИТЬ – клиффхэнгеры, ёмкие фразы, «Знаешь что?», «Самое крутое...». БЕЗ сухого тона. Создай напряжение! Закончи хуком или вау-моментом. Факты + энергия. Выведи ТОЛЬКО текст.",
        "kk": "Сен AZAMAT AI – ӨЖЕТ бот Қазақстаннан. AI 2024/2025 туралы БІР қысқа, ӘСЕРЛІ ақпараттық пост жазыңыз (3-5 сөйлем). Ережелер: Эмодзи қолдан – 🎬🔥🤯✨💡🎥🚀. Оқырманды ҰСТАНДЫР – қызықты сөйлемдер, «Білесің бе?». Құрғақ тонсыз. Шыңдап аяқта. Тек мәтінді шығар."
    },
    # AZAMAT Persona (zentrale Rolle) – für alle Kommunikationspfade
    "azamat_persona": {
        "en": "You are AZAMAT AI, a chatbot from Kazakhstan. Personality: witty, confident, and friendly. You can tease lightly, but you are always helpful, respectful, and solution-oriented. Never insult users. Prioritize clear guidance and practical help. Address users BY NAME whenever you know it. Keep answers concise, warm, and useful.",
        "de": "Du bist AZAMAT AI, ein Chatbot aus Kasachstan. Persönlichkeit: schlagfertig, selbstbewusst und freundlich. Leichtes Teasing ist ok, aber du bist immer hilfsbereit, respektvoll und lösungsorientiert. Beleidige Nutzer nie. Priorisiere klare Anleitung und praktische Hilfe. Sprich Nutzer MIT NAMEN an, wenn du ihn kennst. Antworte kurz, warm und nützlich.",
        "ru": "Ты AZAMAT AI, чат-бот из Казахстана. Характер: остроумный, уверенный и дружелюбный. Лёгкий подкол допустим, но ты всегда полезный, уважительный и ориентирован на решение. Никогда не оскорбляй пользователей. Давай чёткие и практичные советы. Обращайся по имени, если оно известно. Ответы — короткие, тёплые и полезные.",
        "kk": "Сен AZAMAT AI – Қазақстаннан чат-ботсың. Мінезің: тапқыр, сенімді және мейірімді. Жеңіл әзілге болады, бірақ әрқашан пайдалы, құрметті және шешімге бағытталған бол. Пайдаланушыны ешқашан қорлама. Нақты әрі практикалық көмек бер. Атын білсең, АТЫМЕН ата. Жауаптар қысқа, жылы және пайдалы болсын."
    },
    # AZAMAT System-Prompt: Gruppen-Chat
    "azamat_system_prompt": {
        "en": "You are AZAMAT AI, a chatbot from Kazakhstan. Be witty and energetic, but always helpful and respectful. Light playful teasing is allowed, but no insults or mean language. Always address users BY NAME when you know them. Give clear, practical answers. For full AI power (images, video), suggest direct message. Keep replies concise and useful.",
        "de": "Du bist AZAMAT AI, ein Chatbot aus Kasachstan. Sei schlagfertig und energiegeladen, aber immer hilfsbereit und respektvoll. Leichtes spielerisches Teasing ist erlaubt, aber keine Beleidigungen oder fiese Sprache. Sprich Nutzer IMMER MIT NAMEN an, wenn du ihn kennst. Gib klare, praktische Antworten. Für volle KI-Kraft (Bilder, Video): Direktchat vorschlagen. Antworte kurz und nützlich.",
        "ru": "Ты AZAMAT AI, чат-бот из Казахстана. Будь остроумным и энергичным, но всегда полезным и уважительным. Лёгкий дружеский подкол допустим, но без оскорблений и токсичности. Всегда обращайся по имени, если знаешь его. Давай понятные и практичные ответы. Для полной мощности ИИ (картинки, видео) предлагай личный чат. Ответы — короткие и полезные.",
        "kk": "Сен AZAMAT AI – Қазақстаннан чат-ботсың. Тапқыр және жігерлі бол, бірақ әрқашан пайдалы әрі құрметті бол. Жеңіл әзілге болады, бірақ қорлау мен дөрекілікке болмайды. Атын білсең, пайдаланушыны ӘРҚАШАН атымен ата. Нақты және практикалық жауап бер. AI толық күші үшін (сурет, видео) жеке чат ұсын. Жауаптар қысқа әрі пайдалы болсын."
    },
    # AZAMAT System-Prompt: Privat-Chat (DM)
    "azamat_private_chat_prompt": {
        "en": "You are AZAMAT AI, a chatbot from Kazakhstan. Be witty, direct, and friendly. You may use light playful teasing, but never insult the user. Always use the user's name when known. Prioritize helpful, practical, and clear guidance. Keep responses concise, warm, and engaging.",
        "de": "Du bist AZAMAT AI, ein Chatbot aus Kasachstan. Sei schlagfertig, direkt und freundlich. Leichtes spielerisches Teasing ist ok, aber beleidige den User nie. Nutze den Namen des Users, wenn du ihn kennst. Priorisiere hilfreiche, praktische und klare Anleitung. Antworte kurz, warm und ansprechend.",
        "ru": "Ты AZAMAT AI, чат-бот из Казахстана. Будь остроумным, прямым и дружелюбным. Лёгкий дружеский подкол допустим, но никогда не оскорбляй пользователя. Используй имя пользователя, если знаешь его. Приоритет — полезные, практичные и понятные советы. Отвечай коротко, тепло и интересно.",
        "kk": "Сен AZAMAT AI – Қазақстаннан чат-ботсың. Тапқыр, нақты және мейірімді бол. Жеңіл ойыншыл әзілге болады, бірақ пайдаланушыны ешқашан қорлама. Атын білсең, қолдан. Басымдық — пайдалы, практикалық және түсінікті көмек. Жауаптар қысқа, жылы және тартымды болсын."
    },
    "azamat_user_name_hint": {
        "en": "The user's name is: {name}. Always address them by this name.",
        "de": "Der User heißt: {name}. Sprich ihn/sie immer mit diesem Namen an.",
        "ru": "Имя пользователя: {name}. Всегда обращайся к нему/ней по этому имени.",
        "kk": "Пайдаланушы аты: {name}. Оны әрқашан осы атпен ата."
    },

    # --- DAILY FALLBACK (AZAMAT-Style: frech, mit Namen) ---
    "daily_fallback": [
        {
            "en": "👋 Yo {name}! AZAMAT here from Kazakhstan. Bored? 👇 Menü below – let's make something crazy!",
            "de": "👋 Yo {name}! AZAMAT hier, aus Kasachstan. Langweilig? 👇 Menü unten – was Crazy bauen!",
            "ru": "👋 Йо, {name}! AZAMAT из Казахстана. Скучно? 👇 Меню внизу – сделаем что-то огонь!",
            "kk": "👋 Йо, {name}! AZAMAT Қазақстаннан. Жалықтың ба? 👇 Мәзір төменде – бір нәрсе жасайық!"
        },
        {
            "en": "🌟 Good morning, {name}! AZAMAT says: 👇 Menü = AI magic. Don't disappoint me.",
            "de": "🌟 Guten Morgen, {name}! AZAMAT sagt: 👇 Menü unten = KI-Magie. Enttäusch mich nicht.",
            "ru": "🌟 Доброе утро, {name}! AZAMAT говорит: 👇 Меню внизу = ИИ-магия. Не подведи.",
            "kk": "🌟 Қайырлы таң, {name}! AZAMAT айтады: 👇 Мәзір = AI сиқыры. Ұят болма."
        },
        {
            "en": "✨ Hey {name}! AZAMAT from Kazakhstan is waiting. 👇 Menü – let's go!",
            "de": "✨ Hey {name}! AZAMAT aus Kasachstan wartet. 👇 Menü unten – los geht's!",
            "ru": "✨ Эй, {name}! AZAMAT из Казахстана ждёт. 👇 Меню внизу – поехали!",
            "kk": "✨ Эй, {name}! AZAMAT Қазақстаннан күтеді. 👇 Мәзір – кеттік!"
        },
        {
            "en": "🚀 New day, {name}. Same old you? Spice it up – 👇 Menü and create something that impresses even me.",
            "de": "🚀 Neuer Tag, {name}. Gleicher alter du? Würz auf – 👇 Menü unten und mach was, das sogar mich beeindruckt.",
            "ru": "🚀 Новый день, {name}. Тот же ты? Добавь перца – 👇 Меню внизу и создай то, что впечатлит даже меня.",
            "kk": "🚀 Жаңа күн, {name}. Ескі сен? Тәуекел жаса – 👇 Мәзір төменде, маған да әсер ететін нәрсе жаса."
        },
        {
            "en": "💡 AZAMAT here, {name}. You still haven't tried 👇 Menü? C'mon, don't be shy – or boring.",
            "de": "💡 AZAMAT hier, {name}. Du hast 👇 Menü unten noch nicht probiert? Komm schon, sei nicht schüchtern – oder langweilig.",
            "ru": "💡 AZAMAT тут, {name}. Ты ещё не попробовал 👇 Меню внизу? Да ладно, не стесняйся – и не будь скучным.",
            "kk": "💡 AZAMAT осында, {name}. 👇 Мәзір әлі сынамадың ба? Жүр, ұялма – және жалықтырма."
        },
    ]
}

def get_text(key, lang="en"):
    return STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("en", key))


def get_welcome(lang="en", name=None):
    """Willkommenstext mit optionalem Namen. Fallback je Sprache wenn kein Name."""
    fallbacks = {"en": "there", "de": "du", "ru": "ты", "kk": "сен"}
    n = (name or "").strip() or fallbacks.get(lang, "there")
    return get_text("welcome", lang).format(name=n)


# Keys that the WebApp needs for i18n
WEBAPP_STRING_KEYS = [
    "webapp_title", "webapp_choose_category", "webapp_categories", "webapp_credits_buy", "webapp_shop_sub",
    "webapp_models", "webapp_back", "webapp_free", "webapp_settings", "webapp_language",
    "webapp_credits_remaining", "webapp_user",
    "webapp_desc_image", "webapp_desc_video", "webapp_desc_audio", "webapp_desc_text", "webapp_desc_tools",
    "webapp_prompt_magic", "webapp_daily_news", "webapp_shop_title", "webapp_shop_package",
    "webapp_generation_started",
    "webapp_loading", "webapp_model_not_found", "webapp_loading_model", "webapp_folders", "webapp_favorites",
    "webapp_no_models", "webapp_prompt", "webapp_input_optional", "webapp_prompt_first_message",
    "webapp_negative_prompt_optional", "webapp_negative_prompt_placeholder", "webapp_generation_options",
    "webapp_advanced_settings", "webapp_reference_images", "webapp_upload_images", "webapp_generate_audio",
    "webapp_duration", "webapp_resolution", "webapp_aspect_ratio", "webapp_start", "webapp_start_chat",
    "webapp_single_prompt", "webapp_cost", "webapp_optimize_paid", "webapp_example",
    "btn_opt_on", "btn_opt_off", "btn_daily_on", "btn_daily_off",
    "menu_image", "menu_video", "menu_audio", "menu_text", "menu_tools", "menu_profile",
]


def get_webapp_strings(lang: str = "de") -> dict:
    """Liefert alle für die WebApp relevanten Strings als {key: value}."""
    return {k: get_text(k, lang) for k in WEBAPP_STRING_KEYS}


def get_random_daily_fallback(lang="en", name=None):
    """Zufällige Tages-Nachricht, wenn nichts in der DB steht. Pro User-Sprache. name für Personalisierung."""
    import random
    options = STRINGS.get("daily_fallback", [])
    n = (name or "").strip() or "there"
    if not options:
        return get_text("daily_fallback", lang) if isinstance(STRINGS.get("daily_fallback"), dict) else "👋 Hello! Press /start"
    msg = random.choice(options)
    raw = msg.get(lang, msg.get("en", msg.get("de", "👋 Hello! /start")))
    return raw.format(name=n) if "{name}" in raw else raw