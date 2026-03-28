import json

from src.application.daily_services import _resolve_daily_message_text


def test_resolve_plain_string_unchanged():
    s = "<b>Hi</b>"
    assert _resolve_daily_message_text(s, "de") == s


def test_resolve_json_picks_language():
    raw = json.dumps({"de": "Hallo", "en": "Hello", "ru": "Привет", "kk": "Сәлем"})
    assert _resolve_daily_message_text(raw, "ru") == "Привет"
    assert _resolve_daily_message_text(raw, "kk") == "Сәлем"


def test_resolve_json_fallback_en_then_de():
    raw = json.dumps({"en": "EN only"})
    assert _resolve_daily_message_text(raw, "ru") == "EN only"


def test_resolve_invalid_json_returns_raw():
    raw = "{not json"
    assert _resolve_daily_message_text(raw, "de") == raw


def test_daily_fallback_sent_date_key_stable():
    """Regression: Key für bot_settings muss stabil bleiben (Deploy-sichere 1×/Tag-Logik)."""
    from src.application.daily_services import BOT_SETTING_DAILY_FALLBACK_SENT_DATE

    assert BOT_SETTING_DAILY_FALLBACK_SENT_DATE == "daily_fallback_sent_date"


def test_rss_urls_for_fetch_respects_cap(monkeypatch):
    from src.application.daily_services import _rss_urls_for_fetch

    urls = [f"https://example.com/{i}" for i in range(20)]
    monkeypatch.setenv("AI_NEWS_RSS_MAX_FEEDS_PER_FETCH", "0")
    assert len(_rss_urls_for_fetch(urls)) == 20
    monkeypatch.setenv("AI_NEWS_RSS_MAX_FEEDS_PER_FETCH", "5")
    got = _rss_urls_for_fetch(urls)
    assert len(got) == 5
    assert set(got).issubset(set(urls))


def test_resolve_ai_news_rss_urls_env_over_db(monkeypatch):
    from src.application.daily_services import resolve_ai_news_rss_urls
    from src.application.ai_news_rss_defaults import AI_NEWS_RSS_DEFAULT_URLS

    monkeypatch.delenv("AI_NEWS_RSS_URLS", raising=False)
    monkeypatch.delenv("AI_NEWS_RSS_URL", raising=False)

    class _Db:
        def get_ai_news_rss_feed_urls(self):
            return ["https://from.neon.example/feed"]

    assert resolve_ai_news_rss_urls(_Db()) == ["https://from.neon.example/feed"]
    assert resolve_ai_news_rss_urls(None) == list(AI_NEWS_RSS_DEFAULT_URLS)

    monkeypatch.setenv("AI_NEWS_RSS_URLS", "https://a.com/1,https://a.com/2")
    assert resolve_ai_news_rss_urls(_Db()) == ["https://a.com/1", "https://a.com/2"]
