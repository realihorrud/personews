from datetime import datetime
import feedparser
from database import get_conn

FEEDS = [
    {"name": "Українська Правда", "url": "https://www.pravda.com.ua/rss"},
    {"name": "Економічна Правда", "url": "https://epravda.com.ua/rss/"},
    {"name": "Суспільне", "url": "https://suspilne.media/rss/all.rss"},
    {"name": "МЕЖА", "url": "https://mezha.ua/feed/"},
    {"name": "ЧЕМПІОН", "url": "https://champion.com.ua/ukr/rss/"},
    {"name": "DEV UA", "url": "https://dev.ua/rss"}
]

def extract_category(entry) -> str | None:
    try:
        tags = entry.get("tags")
        if tags and len(tags) > 0:
            term = tags[0].get("term")
            return term.strip() if term else None
    except (KeyError, TypeError, AttributeError):
        pass
    return None

def fetch_all_feeds():
    conn = get_conn()
    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        new_count = 0
        for entry in parsed.entries:
            category = extract_category(entry)
            cursor = conn.execute("""
                INSERT OR IGNORE INTO articles (title, summary, url, source, published_at, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry.get("title", "").strip(),
                entry.get("summary", "").strip(),
                entry.get("link", ""),
                parsed["href"],
                entry.get("published", str(datetime.now())),
                category
            ))
            if cursor.rowcount == 1:
                new_count += 1
        conn.commit()
        print(f"{feed['name']}: {new_count} new articles")
    conn.close()