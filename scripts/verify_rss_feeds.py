#!/usr/bin/env python3
"""
Prüft RSS-URLs aus ai_news_rss_defaults (HTTP + feedparser).
Nutzen: python scripts/verify_rss_feeds.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import feedparser  # noqa: E402

from src.application.ai_news_rss_defaults import AI_NEWS_RSS_DEFAULT_URLS  # noqa: E402


def check(url: str) -> tuple[bool, str, int]:
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        return False, f"parse_exc:{e}", 0
    entries = getattr(feed, "entries", None) or []
    n = len(entries)
    if n > 0:
        return True, "ok", n
    if getattr(feed, "bozo", 0):
        err = getattr(feed, "bozo_exception", None)
        return False, f"bozo:{err}", n
    return False, "no_entries", n


def main() -> None:
    ok_urls: list[str] = []
    for u in AI_NEWS_RSS_DEFAULT_URLS:
        good, reason, n = check(u)
        if good:
            ok_urls.append(u)
            print(f"OK  ({n} items) {u}")
        else:
            print(f"BAD ({reason}) {u}")
    print(f"\nOK {len(ok_urls)} / {len(AI_NEWS_RSS_DEFAULT_URLS)}")


if __name__ == "__main__":
    main()
