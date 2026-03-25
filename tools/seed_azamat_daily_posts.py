"""
Einmalig / wiederholbar: Füllt daily_posts für die nächsten 7 Tage mit AZAMAT-Tipps.

Nutzt DATABASE_URL aus .env. UPSERT auf date_to_send; bereits gesendete Posts (sent_status=1)
bleiben markiert und erhalten nur optional neue Texte nicht erzwungen – wir überschreiben
message_text aber setzen sent_status nur auf 0, wenn noch nicht gesendet.

Aufruf: python tools/seed_azamat_daily_posts.py
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()

# Projektroot
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


MESSAGES: list[tuple[int, str]] = [
    (
        0,
        """🤖 <b>AZAMAT AI – dein Hub in Telegram</b>

AZAMAT bündelt Bild-, Video-, Audio-, Text- und Tool-Modelle hinter einem Bot.

<b>So startest du:</b>
• Tippe <code>/start</code> – dann siehst du Menü, Kategorien und Modelle.
• Im <b>WebApp-Modus</b> öffnet das 🌐-Symbol neben dem Eingabefeld die <b>Mini App</b>: dort wählst du Modelle, trägst <b>Prompt</b> und <b>Optionen</b> (Dauer, Format, Referenzbilder …) ein und startest mit einem Klick.

Viel Spaß beim Erkunden! 💙""",
    ),
    (
        1,
        """💎 <b>Credits & Stars</b>

AZAMAT arbeitet mit <b>Credits ⭐</b>. Ohne Guthaben starten manche Modelle nicht.

<b>So lädst du auf:</b>
• Im Bot: Shop / Credits kaufen (Telegram <b>Stars</b>).
• In der WebApp: Karte „Credits kaufen“.

Tipp: Vor großen Video-Jobs kurz prüfen, ob genug Credits da sind – dann läuft’s ohne Überraschung.""",
    ),
    (
        2,
        """🎬 <b>Video & Referenzbilder (z. B. Kling)</b>

Viele Video-Modelle brauchen ein <b>Referenzbild</b> oder klare Vorgaben.

<b>In der WebApp:</b>
• Unter „Generation Optionen“: <b>Dauer</b>, <b>Seitenverhältnis</b> usw. je nach Modell.
• <b>Referenzbilder:</b> URLs eintragen <i>oder</i> direkt <b>hochladen</b> – die Links landen automatisch im Feld.

Ohne passendes Bild kann Image-to-Video scheitern – einmal Bild wählen, Prompt schreiben, Start – fertig.""",
    ),
    (
        3,
        """💬 <b>Chat-Modus vs. einmaliger Prompt</b>

Bei <b>Text-Modellen</b> fragt AZAMAT oft:
• <b>Chat starten</b> – Dialog mit Verlauf (sinnvoll für Rückfragen und Follow-ups).
• <b>Einmaliger Prompt</b> – eine Antwort, dann wieder regulärer Menü-Flow.

In der WebApp kannst du optional schon einen <b>ersten Prompt</b> eintragen – der wird mitgeschickt.

Tipp: Für schnelle Einzelantworten „einmalig“, für längere Projekte „Chat“.""",
    ),
    (
        4,
        """⚙️ <b>Einstellungen, die sich lohnen</b>

Unter <b>Einstellungen</b> (Bot oder WebApp):

• <b>Sprache</b> – Oberfläche und Texte passen sich an.
• <b>Prompt-Magie</b> – optional Verbesserungsvorschlag vor der Generierung (an/aus).
• <b>Tägliche News</b> – diese Infos-Posts und Updates (an/aus).

Wer weniger Nachrichten möchte, schaltet Daily News aus – der Bot bleibt sonst normal nutzbar.""",
    ),
    (
        5,
        """🎨 <b>Bild-Studio & Workflow</b>

<b>Bild-Modelle</b> (Flux, DALL·E, SD …): Prompt eingeben, ggf. Stil im Text beschreiben, Start.

Nach einem Bild bleibt AZAMAT oft im <b>gleichen Modell</b> und fragt nach dem <b>nächsten Prompt</b> – ideal für Varianten.

WebApp: Modell öffnen, Prompt + Optionen setzen, generieren; oder klassisch im Chat nach Modellwahl den Prompt schicken.""",
    ),
    (
        6,
        """🛡️ <b>Tipps für Gruppen & gute Ergebnisse</b>

• In <b>Gruppen</b> gilt: Commands und Menü wie gewohnt – Credits können gruppenbezogen mitlaufen (je nach Setup).
• <b>Lange oder sensible Themen</b> oft klarer im <b>Privatchat</b> mit dem Bot.
• <b>Konkrete Prompts</b> (Motiv, Stil, Licht, Kamera) liefern bessere Outputs als ein einzelnes Wort.

Du nutzt AZAMAT schon richtig, wenn du: Modell wählen → Eingaben prüfen → <b>Start</b> – und bei Fragen einfach <code>/start</code> oder die WebApp öffnen.

Bis morgen! 💙""",
    ),
]


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL fehlt (.env).", file=sys.stderr)
        sys.exit(1)

    import psycopg2

    today = date.today()
    rows = []
    for offset, (_, text) in enumerate(MESSAGES):
        d = today + timedelta(days=offset)
        rows.append((d.strftime("%Y-%m-%d"), text))

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
            # SERIAL-Sequence kann hinter MAX(id) liegen → UniqueViolation auf pkey
            cur.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('daily_posts', 'id'),
                    COALESCE((SELECT MAX(id) FROM daily_posts), 0)
                )
                """
            )
            for date_str, msg in rows:
                cur.execute(sql, (date_str, msg))
        conn.commit()
        print("OK: daily_posts für 7 Tage ab", rows[0][0], "–", rows[-1][0])
    finally:
        conn.close()


if __name__ == "__main__":
    main()
