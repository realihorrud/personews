import sqlite3


def get_or_create_user(conn, username):
    user = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if user:
        return user[0]
    conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()

    return conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()[0]


def get_unrelated_articles(conn, user_id, limit=2):
    return conn.execute("""
                        WITH ranked AS (SELECT a.id,
                                               a.title,
                                               a.source,
                                               a.category,
                                               ROW_NUMBER() OVER (
                                                   PARTITION BY a.source
                                                   ORDER BY a.published_at DESC
                                                   ) AS rn
                                        FROM articles a
                                                 LEFT JOIN article_ratings r
                                                           ON a.id = r.article_id AND r.user_id = ?
                                        WHERE r.id IS NULL)
                        SELECT id, title, source, category
                        FROM ranked
                        WHERE rn <= ?
                        ORDER BY source, rn
                        """, (user_id, limit)).fetchall()


def save_rating(conn, user_id, article_id, rating):
    conn.execute("""
            INSERT OR REPLACE INTO article_ratings (user_id, article_id, rating)
            VALUES (?, ?, ?)
        """, (user_id, article_id, rating))
    conn.commit()


def browse(conn, username):
    user_id = get_or_create_user(conn, username)
    articles = get_unrelated_articles(conn, user_id)

    if not articles:
        print("No new articles to rate. Run the fetcher first.")
        return

    print(f"\n{len(articles)} articles to rate. Commands: [u]pvote  [d]ownvote  [s]kip  [q]uit\n")

    for article_id, title, source, category in articles:
        print(f"  [{category or '—'}]  {source}")
        print(f"  {title}")

        while True:
            cmd = input("  > ").strip().lower()
            if cmd == "u":
                save_rating(conn, user_id, article_id, 1)
                print("  ✓\n")
                break
            elif cmd == "d":
                save_rating(conn, user_id, article_id, -1)
                print("  ✗\n")
                break
            elif cmd == "s":
                print("  —\n")
                break
            elif cmd == "q":
                return
            else:
                print("  u / d / s / q")


if __name__ == "__main__":
    conn = sqlite3.connect("personews.db")
    browse(conn, username="ihorrud")
    conn.close()
