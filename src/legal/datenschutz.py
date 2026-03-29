"""
Datenschutzerklärung / Privacy policy — je Sprache (ohne strings.py).

Platzhalter: {service_name} — Anzeigename des Dienstes (z. B. AZAMAT AI).
"""

from __future__ import annotations

_PRIVACY_DE = """DATENSCHUTZERKLÄRUNG ({service_name})

1. Verantwortlicher
Verantwortlich für die Datenverarbeitung im Sinne der DSGVO ist der im Impressum genannte Anbieter.

2. Allgemeines
Mit diesem Bot und der optionalen Web-App (Telegram Mini App) können Sie KI-gestützte Funktionen nutzen (z. B. Bild-, Video-, Textgenerierung). Der Schutz Ihrer personenbezogenen Daten ist uns wichtig.

3. Welche Daten verarbeiten wir?
• Telegram: Telegram User-ID, ggf. Nutzername und Profildaten, die Telegram uns im Rahmen des Chats übergibt (Verarbeitung erfolgt auch durch Telegram gemäß deren Datenschutzrichtlinie).
• Nutzungs- und Vertragsdaten: z. B. gewählte Sprache, Einstellungen, Credit-Stand und Transaktionsdaten, soweit zur Abrechnung und zum Betrieb nötig.
• Inhalte Ihrer Anfragen: Texteingaben (Prompts) und ggf. Medien, die Sie zur Generierung bereitstellen.
• Chat-Modus: Wenn Sie den fortlaufenden Chat-Modus nutzen, speichern wir die Konversationshistorie in unserer Datenbank, damit der Dialog fortgeführt werden kann (ggf. mit automatischer Zusammenfassung älterer Teile).

4. Keine Zweckentfremdung / kein „Tracking“ zu Werbezwecken
Wir nutzen Ihre Daten nicht, um Sie werblich zu profilieren oder für unkaufliche Marketing-Profile. Es findet kein übliches werbliches Cross-Site-Tracking über den Bot hinweg statt.

5. Hochgeladene Fotos und Medien
Referenzbilder oder andere Medien, die Sie für eine Generierung bereitstellen, werden verarbeitet, um die angeforderte Ausgabe zu erzeugen. Eine dauerhafte Archivierung als Medienbibliothek auf unseren Servern erfolgt nicht. Technisch können Daten vorübergehend im Betrieb anfallen (z. B. Puffer/Logs); eine Weiterverarbeitung zu anderen Zwecken als der Durchführung Ihres Auftrags erfolgt nicht.

6. Auftragsverarbeitung durch Drittanbieter (Replicate u. a.)
Die eigentliche Modell-Inferenz erfolgt über den Dienst Replicate (und ggf. weitere Modellanbieter über diese Pipeline). Dabei werden die für die Generierung erforderlichen Eingaben (Prompt, Parameter, ggf. Bild-URLs) an Replicate übermittelt. Es handelt sich um eine Auftragsverarbeitung im Rahmen der Dienstleistung. Replicate hat eigene Datenschutzbedingungen; Daten können in Drittländern (z. B. USA) verarbeitet werden, soweit dies für die Erbringung der Leistung erforderlich ist.

7. Zahlungen
Wenn Sie Credits über Telegram Stars oder vergleichbare Mechanismen erwerben, gelten zusätzlich die Datenschutzbestimmungen von Telegram bzw. des jeweiligen Zahlungswegs.

8. Speicherdauer und Löschung
Wir speichern personenbezogene Daten nur so lange, wie es für den Betrieb, die Vertragsabwicklung und gesetzliche Pflichten erforderlich ist. Daten auf unseren Servern werden gelöscht, sobald sie für diese Zwecke nicht mehr benötigt werden, sofern keine gesetzlichen Aufbewahrungsfristen entgegenstehen. Transaktions- und Abrechnungsdaten können wir zur Nachweisführung entsprechend den gesetzlichen Fristen aufbewahren.

9. Ihre Rechte (DSGVO)
Sie haben nach Maßgabe der DSGVO Rechte auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Widerspruch sowie Datenübertragbarkeit. Außerdem haben Sie das Recht, sich bei einer Datenschutzaufsichtsbehörde zu beschweren.

10. Kontakt
Für Datenschutzanfragen nutzen Sie bitte die im Impressum angegebene Kontaktadresse.

Hinweis: Diese Erklärung ersetzt keine individuelle Rechtsberatung. Bitte passen Sie die Angaben zu Impressum und ggf. Auftragsverarbeitungsverträgen an Ihr Unternehmen an.
"""

_PRIVACY_EN = """PRIVACY POLICY ({service_name})

1. Controller
The provider named in our legal notice (Impressum) is responsible for processing personal data under the GDPR, where applicable.

2. Overview
This Telegram bot and optional web mini app let you use AI features (e.g. image, video, text generation). We take privacy seriously.

3. Data we process
• Telegram: Telegram user ID and profile fields Telegram provides in the chat (Telegram also processes data under its own policies).
• Service data: language, settings, credit balance and transaction records as needed for billing and operations.
• Your inputs: prompts and media you submit for generation.
• Chat mode: if you use continuous chat, we store conversation history in our database to continue the thread (older parts may be summarized automatically).

4. No unrelated repurposing / no ad profiling
We do not use your data to build advertising profiles or for marketing tracking in the usual sense.

5. Photos and uploads
Reference images and other media are processed to produce the output you request. We do not keep them as a permanent media archive on our servers. Temporary technical data (e.g. buffers/logs) may occur during operation; we do not further process your content for unrelated purposes.

6. Sub-processors (Replicate and model providers)
Model inference is performed via Replicate (and possibly underlying model providers). Required inputs (prompt, parameters, image URLs, etc.) are transmitted to Replicate as part of the service. Replicate has its own privacy terms; processing may occur in third countries (e.g. the USA) where necessary to deliver the service.

7. Payments
If you purchase credits via Telegram Stars or similar, Telegram’s (or the payment provider’s) privacy terms also apply.

8. Retention and deletion
We retain personal data only as long as needed for operations, contract performance, and legal obligations. Data on our servers is deleted when no longer required for those purposes, unless statutory retention applies. Billing records may be kept as required by law.

9. Your rights (GDPR)
Where the GDPR applies, you may have rights of access, rectification, erasure, restriction, objection, and data portability, and the right to lodge a complaint with a supervisory authority.

10. Contact
For privacy requests, please use the contact details in our legal notice.

Note: This text is not legal advice. Align Impressum and processor agreements with your organisation.
"""

_PRIVACY_RU = """ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ ({service_name})

1. Оператор данных
Оператором является поставщик услуг, указанный в правовых сведениях (Impressum), в пределах применимости GDPR.

2. Общие положения
Бот в Telegram и веб-приложение (Mini App) предоставляют функции на базе ИИ. Мы обрабатываем данные в объёме, необходимом для услуги.

3. Какие данные обрабатываются
• Telegram: идентификатор пользователя и данные профиля, которые передаёт Telegram (отдельно действует политика Telegram).
• Служебные данные: язык, настройки, баланс кредитов и транзакции для расчётов и работы сервиса.
• Ваши запросы: текст (промпты) и медиа для генерации.
• Режим чата: при непрерывном чате история диалога хранится в нашей базе для продолжения беседы (старые части могут суммироваться).

4. Без перепрофилирования под рекламу
Мы не используем ваши данные для рекламного профилирования и «трекинга» в маркетинговом смысле.

5. Фотографии и загрузки
Загруженные изображения обрабатываются для выполнения запроса на генерацию. Постоянного медиаархива на наших серверах мы не ведём. Кратковременные технические данные возможны; обработка в иных целях не производится.

6. Субподряд (Replicate и др.)
Инференс моделей выполняется через Replicate (и связанных поставщиков). На Replicate передаются необходимые входные данные. Применяются отдельные условия Replicate; обработка может происходить в третьих странах (например, США).

7. Платежи
При покупке через Telegram Stars действуют также условия Telegram/платёжного провайдера.

8. Хранение и удаление
Данные хранятся только столько, сколько нужно для работы сервиса, договора и закона. После этого удаляются, если нет законных сроков хранения (например, для учёта платежей).

9. Права субъекта данных
Применимо к GDPR: доступ, исправление, удаление, ограничение, возражение, переносимость, жалоба в надзорный орган.

10. Контакт
Запросы по данным — через контакты в правовых сведениях (Impressum).

Примечание: текст не является юридической консультацией.
"""

_PRIVACY_KK = """ҚҰПИЯЛЫЛЫҚ САЯСАТЫ ({service_name})

1. Деректерді өңдеуші
Қолданылатын заңнама шегінде деректерді өңдеуге жауапты тұлға заңды мәліметтерде (Impressum) көрсетіледі.

2. Жалпы
Telegram боты және веб-қосымша (Mini App) ЖИ функцияларын ұсынады.

3. Қандай деректер
• Telegram: пайдаланушы идентификаторы және Telegram беретін профиль деректері (Telegramның өз саясаты бар).
• Қызмет деректері: тіл, баптаулар, кредиттер және транзакциялар.
• Сұраулар: мәтін (промпт) және генерацияға берілген медиа.
• Чат режимі: сұхбат тарихы қызметті жалғастыру үшін базада сақталуы мүмкін (ескі бөліктер қысқартылуы мүмкін).

4. Жарнама профилі жоқ
Деректерді жарнамалық бақылау/профильдеу үшін пайдаланбаймыз.

5. Фото және жүктеулер
Суреттер тек сұралған генерацияны орындау үшін өңделеді. Біздің серверлерде тұрақты медиа мұрағаты жоқ. Уақытша техникалық деректер болуы мүмкін; басқа мақсатта өңделмейді.

6. Үшінші тарап (Replicate)
Модель инференсі Replicate арқылы жүргізіледі; қажетті кіріс деректер жіберіледі. Replicateтың өз шарттары бар; деректер үшінші елдерде (мысалы, АҚШ) өңделуі мүмкін.

7. Төлемдер
Telegram Stars арқылы сатып алуда Telegram/төлем провайдерінің шарттары қолданылады.

8. Сақтау және жою
Деректер қызмет, шарт және заң талаптары үшін қажетті мерзімде сақталады; содан кейін жойылады (есепке алу үшін заңды мерзімдер болмаса).

9. Құқықтар (GDPR қолданылса)
Қолжетімділік, түзету, жою, шектеу, қарсылық, тасымалдау, шағым.

10. Байланыс
Сұраулар үшін Impressumдағы контактті пайдаланыңыз.

Ескерту: бұл заң кеңесі емес.
"""


def privacy_body(lang: str) -> str:
    m = {
        "de": _PRIVACY_DE,
        "en": _PRIVACY_EN,
        "ru": _PRIVACY_RU,
        "kk": _PRIVACY_KK,
    }
    return m.get(lang, _PRIVACY_EN)
