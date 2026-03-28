import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.application.daily_services import DailyService


def _text_model():
    return SimpleNamespace(type=["text"], is_active=True, key="google-gemini-2-5-flash")


def _image_model():
    return SimpleNamespace(type=["image_generation"], is_active=True, key="nano-banana")


def test_dispatch_dedupes_same_chat_id_across_group_and_user(monkeypatch):
    bot = MagicMock()
    bot.send_photo_sync = MagicMock()
    bot.send_message_sync = MagicMock()
    db = MagicMock()
    generation_service = MagicMock()
    service = DailyService(bot, db, generation_service)

    # Same chat id appears in groups and users (real-world overlap).
    overlap_chat_id = -1002474336372
    db.get_all_tracked_groups.return_value = [overlap_chat_id]
    db.get_group_language.return_value = "ru"
    db.get_subscribed_users.return_value = [overlap_chat_id, 123456]
    db.get_user_settings.side_effect = lambda uid: {"lang": "en" if uid == 123456 else "ru"}
    db.get_model_by_key.side_effect = lambda key: _text_model() if key == "google-gemini-2-5-flash" else _image_model()
    db.get_azamat_random_count_today.return_value = 0
    db.increment_azamat_random_count_today.return_value = None

    # Ensure direct links in news and enough entries.
    monkeypatch.setattr(
        service,
        "_fetch_ai_news_from_rss",
        lambda max_items=2: [
            {"title": "A", "snippet": "S1", "link": "https://example.com/a", "source": "SrcA"},
            {"title": "B", "snippet": "S2", "link": "https://example.com/b", "source": "SrcB"},
        ],
    )

    def fake_process_request(_uid, model, _prompt, media_files=None, no_charge=True, **kwargs):
        if "image" in ",".join(model.type):
            return True, "https://img.example.com/news.png"
        return True, "Localized summary text"

    generation_service.process_request.side_effect = fake_process_request

    result = service._dispatch_ai_news_post(force=True, broadcast_all=True)

    assert result["ok"] is True
    # Should send exactly once to overlap group id + once to distinct user id.
    assert bot.send_photo_sync.call_count == 2
    sent_chat_ids = [c.args[0] for c in bot.send_photo_sync.call_args_list]
    assert overlap_chat_id in sent_chat_ids
    assert 123456 in sent_chat_ids
    # No extra plain-text fallback send for successful photo path.
    assert bot.send_message_sync.call_count == 0


def test_generate_news_image_url_retries_until_valid_url(monkeypatch):
    bot = MagicMock()
    db = MagicMock()
    generation_service = MagicMock()
    service = DailyService(bot, db, generation_service)
    monkeypatch.setattr("src.application.daily_services.time.sleep", lambda _s: None)

    image_model = _image_model()
    recipients = [("user", 1, "en")]
    news_block = "News 1: Something happened"

    # 1st attempt has no URL, 2nd returns valid URL.
    generation_service.process_request.side_effect = [
        (True, []),
        (True, "https://img.example.com/final.png"),
    ]

    url = service._generate_news_image_url_with_retry(
        recipients=recipients,
        news_block=news_block,
        image_model=image_model,
        retries=3,
        delay_s=0,
    )

    assert url == "https://img.example.com/final.png"
    assert generation_service.process_request.call_count == 2


def test_dispatch_concurrent_second_call_skipped(monkeypatch):
    """Zweiter paralleler Aufruf ohne wait_if_busy soll concurrent_dispatch liefern."""
    bot = MagicMock()
    db = MagicMock()
    generation_service = MagicMock()
    service = DailyService(bot, db, generation_service)

    started = threading.Event()
    proceed = threading.Event()

    def slow_fetch(*_a, **_kw):
        started.set()
        proceed.wait(timeout=5.0)
        return [
            {"title": "A", "snippet": "S1", "link": "https://example.com/a", "source": "SrcA"},
            {"title": "B", "snippet": "S2", "link": "https://example.com/b", "source": "SrcB"},
        ]

    monkeypatch.setattr(service, "_fetch_ai_news_from_rss", slow_fetch)
    db.get_all_tracked_groups.return_value = []
    db.get_subscribed_users.return_value = [1]
    db.get_user_settings.return_value = {"lang": "en"}
    db.get_model_by_key.side_effect = lambda key: (
        _text_model() if key == "google-gemini-2-5-flash" else _image_model()
    )
    db.get_azamat_random_count_today.return_value = 0

    def _pr(*args, **kwargs):
        model = args[1]
        mt = ",".join(getattr(model, "type", []) or [])
        if "image" in mt:
            return True, "https://img.example.com/x.png"
        return True, "Summary text"

    generation_service.process_request.side_effect = _pr

    out = {}

    def run_a():
        out["a"] = service._dispatch_ai_news_post(force=True, broadcast_all=True)

    t1 = threading.Thread(target=run_a)
    t1.start()
    assert started.wait(timeout=3.0)
    out["b"] = service._dispatch_ai_news_post(force=True, broadcast_all=True, wait_if_busy=False)
    assert out["b"]["ok"] is False
    assert out["b"]["reason"] == "concurrent_dispatch"
    proceed.set()
    t1.join(timeout=10.0)
    assert out["a"]["ok"] is True

