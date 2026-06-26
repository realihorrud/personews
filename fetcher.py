from datetime import datetime
import feedparser
from database import get_conn

FEEDS = [
    {"name": "Українська Правда", "url": "https://www.pravda.com.ua/rss"},
    {"name": "Економічна Правда", "url": "https://epravda.com.ua/rss/"},
    {"name": "Суспільне", "url": "https://suspilne.media/rss/all.rss"},
    {"name": "МЕЖА", "url": "https://mezha.ua/feed/"},
    {"name": "ЧЕМПІОН", "url": "https://champion.com.ua/ukr/rss/"}
]

def fetch_all_feeds():
    conn = get_conn()
    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        new_count = 0
        for entry in parsed.entries:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO articles (title, summary, url, source, published_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entry.get("title", "").strip(),
                entry.get("summary", "").strip(),
                entry.get("link", ""),
                parsed["href"],
                entry.get("published", str(datetime.now())),
            ))
            if cursor.rowcount == 1:
                new_count += 1
        conn.commit()
        print(f"{feed['name']}: {new_count} new articles")
    conn.close()