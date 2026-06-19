import sqlite3
from datetime import datetime
from urllib.parse import urlparse, urlunparse
import feedparser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'

FEEDS = [
    {"name": "Українська Правда", "url": "https://www.pravda.com.ua/rss"},
    {"name": "Суспільне", "url": "https://suspilne.media/rss/all.rss"},
    {"name": "ТСН", "url": "https://tsn.ua/rss"},
    {"name": "МЕЖА", "url": "https://mezha.ua/feed/"},
    {"name": "r/reddit_ukr", "url": "https://www.reddit.com/r/reddit_ukr.rss"},
]

CATEGORY_SEEDS = {
    "Війна та безпека": "армія зсу фронт обстріл ракета окупація бойові нато зброя дрон мобілізація",
    "Політика": "президент парламент верховна рада уряд міністр закон вибори партія депутат",
    "Економіка": "гривня бюджет інфляція ввп банк нбу економіка ринок долар євро санкції",
    "Технології": "штучний інтелект технології стартап додаток кібер програмування цифровий",
    "Спорт": "футбол матч чемпіонат команда гравець динамо шахтар олімпіада турнір",
    "Суспільство": "освіта медицина культура церква суспільство соціальний волонтер",
}


def init_db(conn):
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS articles
                 (
                     id           INTEGER PRIMARY KEY AUTOINCREMENT,
                     title        TEXT        NOT NULL,
                     summary      TEXT,
                     url          TEXT UNIQUE NOT NULL,
                     source       TEXT,
                     published_at TEXT,
                     created_at   TEXT DEFAULT CURRENT_TIMESTAMP
                 )
                 """)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS users
                 (
                     id         INTEGER PRIMARY KEY AUTOINCREMENT,
                     username   TEXT UNIQUE NOT NULL,
                     created_at TEXT DEFAULT CURRENT_TIMESTAMP
                 )
                 """)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS article_ratings
                 (
                     id         INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id    INTEGER NOT NULL REFERENCES users (id),
                     article_id INTEGER NOT NULL REFERENCES articles (id),
                     rating     INTEGER NOT NULL CHECK (rating IN (-1, 1)),
                     rated_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                     UNIQUE (user_id, article_id)
                 )
                 """)
    conn.commit()


def fetch_articles_from_feed(feed):
    parsed = feedparser.parse(feed['url'])
    articles = []
    for entry in parsed['entries']:
        articles.append({
            'title': entry.get('title', '').strip(),
            'summary': entry.get('summary', '').strip(),
            'url': clean_url(entry.get('link', '').strip()),
            'source': entry.get('source', '').strip(),
            'published_at': entry.get('published_at', str(datetime.now())),
        })
    return articles


def save_articles(conn, articles):
    new_count = 0
    for article in articles:
        cursor = conn.execute("""
                              INSERT OR IGNORE INTO articles (title, summary, url, source, published_at)
                              VALUES (:title, :summary, :url, :source, :published_at)
                              """, article)
        if cursor.rowcount == 1:
            new_count += 1
    conn.commit()
    return new_count


def get_top_tf_idf_words(conn):
    cursor = conn.cursor()
    summaries = [row[0] for row in cursor.execute("""SELECT summary
                                                     FROM articles""").fetchall()]

    tf_idf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tf_idf_vectorizer.fit_transform(summaries)
    feature_names = tf_idf_vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray()
    for tfidf_score in tfidf_scores:
        sorted_keywords = [word for _, word in sorted(zip(tfidf_score, feature_names), reverse=True)]
        print("Keywords: ", sorted_keywords[:5])


def clean_url(url):
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))


def categorize_articles(conn):
    try:
        conn.execute("ALTER TABLE articles ADD COLUMN category TEXT")
        conn.commit()
    except Exception:
        pass

    articles = conn.execute(
        "SELECT id, title, summary FROM articles WHERE category IS NULL"
    ).fetchall()

    if not articles:
        print("Nothing to categorize.")
        return

    category_names = list(CATEGORY_SEEDS.keys())
    seed_texts = list(CATEGORY_SEEDS.values())

    article_texts = [f"{title} {summary or ''}" for _, title, summary in articles]

    vectorizer = TfidfVectorizer(max_features=5000)
    # Fit on everything, so, articles and seeds share the same vocabulary
    all_vectors = vectorizer.fit_transform(article_texts + seed_texts)

    article_vectors = all_vectors[:len(article_texts)]
    seed_vectors = all_vectors[len(article_texts):]

    # Each row = one article, each column = similarity to one category
    similarities = cosine_similarity(article_vectors, seed_vectors)
    updates = []
    for i, (article_id, _, _) in enumerate(articles):
        best_idx = similarities[i].argmax()
        best_score = similarities[i][best_idx]

        # If similarity is too low, the article fits no category well
        category = category_names[best_idx] if best_score > 0.05 else "Інше"
        updates.append((category, article_id))

    conn.executemany("UPDATE articles SET category = ? WHERE id = ?", updates)
    conn.commit()
    print(f"Categorized {len(updates)} articles.")


def print_results(conn):
    rows = conn.execute("""
                        SELECT category, COUNT(*) as n
                        FROM articles
                        GROUP BY category
                        ORDER BY n DESC
                        """).fetchall()
    print()
    for category, count in rows:
        bar = "█" * (count // 3)
        print(f"{category:<22} {count:>4}  {bar}")


def main():
    conn = sqlite3.connect('personews.db')
    init_db(conn)

    # for feed in FEEDS:
    #     articles = fetch_articles_from_feed(feed)
    #     new_count = save_articles(conn, articles)
    #     print(f"{feed['name']}: fetched {len(articles)}, saved {new_count} new")
    #
    # categorize_articles(conn)
    # print_results(conn)

    conn.close()


if __name__ == "__main__":
    main()
