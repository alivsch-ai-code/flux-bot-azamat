"""
Standard-RSS-URLs für AI-Daily-News.

Quellen: awesome_ML_AI_RSS_feed, ai-news-bot; geprüft mit scripts/verify_rss_feeds.py.
Tote/fehlende Parser entfernt; Fast.ai → index.xml; Engadget → Haupt-RSS; Meta → engineering.fb.com.
(Hinweis: ArXiv-RSS liefert zeitweise leere Channels / feedparser 0 entries — bei Bedarf per
AI_NEWS_RSS_URLS oder Eintrag in Neon ai_news_rss_feeds nachziehen.)
"""

AI_NEWS_RSS_DEFAULT_URLS: list[str] = [
    "https://machinelearningmastery.com/blog/feed",
    "https://aws.amazon.com/blogs/machine-learning/feed",
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://mlinproduction.com/feed",
    "https://jalammar.github.io/feed.xml",
    "https://proceedings.mlr.press/feed.xml",
    "https://distill.pub/rss.xml",
    "https://www.inference.vc/rss",
    "https://www.aitrends.com/feed",
    "https://aiweirdness.com/rss",
    "https://bair.berkeley.edu/blog/feed.xml",
    "https://becominghuman.ai/feed",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://feeds.feedburner.com/nvidiablog",
    "https://davidstutz.de/feed",
    "https://www.reddit.com/r/artificial/.rss",
    "https://www.reddit.com/r/neuralnetworks/.rss?format=xml",
    "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
    "https://danieltakeshi.github.io/feed.xml",
    "https://vitalab.github.io/feed.xml",
    "https://medium.com/feed/@karpathy",
    "https://openai.com/blog/rss.xml",
    "https://www.microsoft.com/en-us/research/feed",
    "https://feeds.feedburner.com/blogspot/gJZg",
    "https://www.fast.ai/index.xml",
    "https://www.reddit.com/r/reinforcementlearning/.rss?format=xml",
    "https://dtransposed.github.io/feed.xml",
    "https://www.johndcook.com/blog/feed",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.technologyreview.com/feed/",
    "https://arstechnica.com/tag/ai/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://thenextweb.com/feed",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.engadget.com/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://deepmind.google/blog/rss.xml",
    "https://engineering.fb.com/feed/",
    "https://blogs.microsoft.com/ai/feed/",
    "https://www.roboticsbusinessreview.com/feed/",
    "https://www.autonomousvehicleinternational.com/feed",
    "https://www.heise.de/rss/heise-atom.xml",
    "https://rss.golem.de/rss.php?feed=RSS2.0",
    "https://news.google.com/rss/search?q=k%C3%BCnstliche+intelligenz&hl=de&gl=DE&ceid=DE:de",
    "https://habr.com/ru/rss/all/",
    "https://www.cnews.ru/inc/rss/news.xml",
    "https://vc.ru/rss/all",
    "https://news.google.com/rss/search?q=%D0%B8%D1%81%D0%BA%D1%83%D1%81%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B9+%D0%B8%D0%BD%D1%82%D0%B5%D0%BB%D0%BB%D0%B5%D0%BA%D1%82&hl=ru&gl=RU&ceid=RU:ru",
]
