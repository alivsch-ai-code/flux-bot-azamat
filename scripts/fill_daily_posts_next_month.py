import calendar
import json
from datetime import date

from src.infrastructure.database import DatabaseManager


def main() -> None:
    db = DatabaseManager()
    today = date.today()
    year = today.year + (1 if today.month == 12 else 0)
    month = 1 if today.month == 12 else today.month + 1
    days = calendar.monthrange(year, month)[1]

    themes = [
        ("Reality Check", "Most AI demos look magical until they meet messy real data."),
        ("Automation Trap", "If your process is chaos, AI just automates chaos faster."),
        ("Prompt Discipline", "Good prompts are not poetry - they are product specs."),
        ("Data Hygiene", "Garbage in, glossy garbage out. Clean data wins."),
        ("Model Hype", "Shiny benchmarks are cute; reliability in production pays bills."),
        ("Cost Radar", "Track token and inference costs early, before finance wakes up."),
        ("Security First", "Never paste secrets into random tools. Ever."),
        ("Human Loop", "The best AI teams keep a human checkpoint for risky outputs."),
        ("Workflow Fit", "Choose tools that fit your workflow, not viral threads."),
        ("Iteration Rhythm", "Small daily improvements beat one giant rewrite."),
        ("Latency Matters", "Fast enough today beats perfect and late tomorrow."),
        ("Quality Signals", "Define quality metrics before shipping AI to users."),
        ("Bias Awareness", "If your data is biased, your model confidence is theater."),
        ("Ops Reality", "Monitoring is not optional when AI touches customers."),
        ("Version Control", "Version prompts, models, and eval sets like real code."),
    ]

    recs = [
        (
            "Start a tiny eval sheet and score outputs weekly.",
            "Собери маленькую eval-таблицу и оценивай ответы каждую неделю.",
        ),
        (
            "Automate one boring task first, then scale.",
            "Сначала автоматизируй одну скучную задачу, потом масштабируй.",
        ),
        (
            "Set a monthly AI budget cap and review it.",
            "Поставь лимит бюджета на AI и проверяй его ежемесячно.",
        ),
        (
            "Document one reusable prompt template per workflow.",
            "Задокументируй по одному шаблону промпта на каждый процесс.",
        ),
        (
            "Keep a rollback plan before every model switch.",
            "Держи план отката перед каждой сменой модели.",
        ),
    ]

    rows: list[tuple[str, str]] = []
    for day in range(1, days + 1):
        topic = themes[(day - 1) % len(themes)]
        rec = recs[(day - 1) % len(recs)]
        date_to_send = f"{year:04d}-{month:02d}-{day:02d}"

        en = (
            f"AZAMAT Daily // {topic[0]}: {topic[1]} "
            f"You are not building AI magic, champ - you are building systems. "
            f"Future tip: {rec[0]}"
        )
        de = (
            f"AZAMAT Daily // {topic[0]}: {topic[1]} "
            f"Du baust keine AI-Magie, Held - du baust Systeme. "
            f"Zukunftstipp: {rec[0]}"
        )
        ru = (
            f"AZAMAT Daily // {topic[0]}: {topic[1]} "
            f"Ты строишь не магический AI, а систему. "
            f"Совет на будущее: {rec[1]}"
        )
        kk = (
            f"AZAMAT Daily // {topic[0]}: {topic[1]} "
            f"Сен AI сиқырын емес, жүйе құрып жатырсың. "
            f"Болашаққа кеңес: {rec[0]}"
        )

        payload = json.dumps({"de": de, "en": en, "ru": ru, "kk": kk}, ensure_ascii=False)
        rows.append((date_to_send, payload))

    conn = db._get_connection()
    c = conn.cursor()
    for date_to_send, message_text in rows:
        c.execute(
            """
            INSERT INTO daily_posts (date_to_send, message_text, image_path, sent_status)
            VALUES (%s, %s, NULL, 0)
            ON CONFLICT (date_to_send) DO UPDATE SET
                message_text = EXCLUDED.message_text,
                image_path = NULL,
                sent_status = 0
            """,
            (date_to_send, message_text),
        )
    conn.commit()
    c.execute(
        "SELECT COUNT(*) FROM daily_posts WHERE date_to_send >= %s AND date_to_send <= %s",
        (f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{days:02d}"),
    )
    count = c.fetchone()[0]
    conn.close()
    print(f"filled month={year}-{month:02d} days={days} rows={count}")


if __name__ == "__main__":
    main()

