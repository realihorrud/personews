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


def get_unrelated_articles(conn, user_id, limit=15):
    return conn.execute("""
                        SELECT a.id, a.title, a.source, a.category
                        FROM articles a
                                 LEFT JOIN article_ratings r
                                           ON a.id = r.article_id AND r.user_id = ?
                        WHERE r.id IS NULL
                        ORDER BY a.published_at DESC
                        LIMIT ?
                        """, (user_id, limit)).fetchall()


def save_rating(conn, user_id, article_id, rating):
    conn.execute("""
            INSERT OR REPLACE INTO article_ratings (user_id, article_id, rating)
            VALUES (?, ?, ?)
        """, (user_id, article_id, rating))
    conn.commit()


def browse(conn, username):
    pass


if __name__ == "__main__":
    conn = sqlite3.connect("personews.db")
    browse(conn, username="ihorrud")
    conn.close()
