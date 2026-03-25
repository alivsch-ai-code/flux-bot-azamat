"""
Legt für MORGEN einen daily_posts-Eintrag an (UPSERT): mehrsprachiger Text zu Amazon Alexa+.

Inhalt basiert auf öffentlichen Meldungen (u. a. Feb. 2026): Alexa+ in den USA für alle
Nutzer verfügbar, KI-Upgrade mit natürlicherem Dialog; Prime oft inklusive, sonst ca.
19,99 $/Monat; Rollout in weiteren Ländern/Europa läuft.

message_text wird als JSON gespeichert; DailyService löst pro User-Sprache auf (de/en/ru/kk).

Aufruf: python archive/legacy_tools/seed_daily_alexa_plus_tomorrow.py

Benötigt DATABASE_URL in .env (PostgreSQL).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

MESSAGES = {
    "de": """📰 <b>Daily Tech: Amazon Alexa+</b>

<b>Alexa+</b> ist in den <b>USA für alle</b> freigeschaltet worden – nach Monaten mit begrenztem Zugang. Dahinter steckt ein <b>KI-Upgrade</b>: natürlicherer Dialog, stärkere Personalisierung und mehr Hilfe im Alltag sowie fürs <b>Smart Home</b> (u. a. über Echo, Alexa-App, Fire TV).

<b>Preis:</b> Für viele <b>Prime</b>-Mitglieder ist Alexa+ <b>enthalten</b>; ohne Prime liegt das Abo bei etwa <b>19,99 $/Monat</b> (Stand Anfang 2026). In <b>Europa</b> (u. a. Deutschland) wird der Rollout schrittweise ausgebaut.

<i>Hinweis: Angebote können sich ändern – offizielle Infos bei Amazon.</i> 🎙️""",
    "en": """📰 <b>Daily Tech: Amazon Alexa+</b>

<b>Alexa+</b> is now <b>available to everyone in the U.S.</b> after a limited rollout. It’s an <b>AI-powered</b> upgrade: more natural conversation, better personalization, and smarter help at home — on <b>Echo</b>, the <b>Alexa app</b>, <b>Fire TV</b>, and more.

<b>Pricing:</b> Often <b>included with Prime</b>; without Prime, about <b>$19.99/month</b> (early 2026). <b>International</b> expansion (including Europe) is ongoing.

<i>Offers may change — check Amazon for the latest.</i> 🎙️""",
    "ru": """📰 <b>Техно-новость: Amazon Alexa+</b>

<b>Alexa+</b> стала <b>доступна всем пользователям в США</b> после ограниченного запуска. Это <b>ИИ-обновление</b>: более живой диалог, персонализация и удобнее умный дом — на <b>Echo</b>, в <b>приложении Alexa</b>, <b>Fire TV</b> и др.

<b>Оплата:</b> для многих подписчиков <b>Prime</b> — <b>включено</b>; без Prime — около <b>19,99 $/мес</b> (начало 2026). <b>Международный</b> запуск (в т. ч. Европа) продолжается.

<i>Условия могут меняться — смотрите актуальное на сайте Amazon.</i> 🎙️""",
    "kk": """📰 <b>Күндік Tech: Amazon Alexa+</b>

<b>Alexa+</b> <b>АҚШ-та барлық пайдаланушыларға</b> ашық — шектеулі іске қосудан кейін. Бұл <b>ЖИ жаңартуы</b>: табиғи диалог, жекелендіру және <b>ақылды үй</b> үшін көмек — <b>Echo</b>, <b>Alexa қолданбасы</b>, <b>Fire TV</b> және т. б.

<b>Төлем:</b> көптеген <b>Prime</b> жазылымдарында <b>қоса беріледі</b>; Prime-сіз шамамен <b>19,99 $/ай</b> (2026 басы). <b>Халықаралық</b> тарату (оның ішінде Еуропа) жалғасуда.

<i>Шарттар өзгеруі мүмкін — Amazon сайтынан растаңыз.</i> 🎙️""",
}


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL fehlt (.env).", file=sys.stderr)
        sys.exit(1)

    import psycopg2

    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    payload = json.dumps(MESSAGES, ensure_ascii=False)

    sql = """
        INSERT INTO daily_posts (date_to_send, message_text, image_path, sent_status)
        VALUES (%s, %s, NULL, 0)
        ON CONFLICT (date_to_send) DO UPDATE SET
            message_text = EXCLUDED.message_text,
            sent_status = CASE
                WHEN daily_posts.sent_status = 1 THEN daily_posts.sent_status
                ELSE 0
            END
    """

    conn = psycopg2.connect(url, sslmode="require")
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('daily_posts', 'id'),
                    COALESCE((SELECT MAX(id) FROM daily_posts), 0)
                )
                """
            )
            cur.execute(sql, (tomorrow, payload))
        conn.commit()
        print("OK: daily_posts für", tomorrow, "(Alexa+, 4 Sprachen als JSON)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
