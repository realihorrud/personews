import sqlite3

DB_PATH = 'personews.db'


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS articles
                 (
                     id           INTEGER PRIMARY KEY AUTOINCREMENT,
                     title        TEXT        NOT NULL,
                     summary      TEXT,
                     url          TEXT UNIQUE NOT NULL,
                     source       TEXT,
                     category     TEXT,
                     embedding    BLOB,
                     published_at TEXT,
                     created_at   TEXT DEFAULT CURRENT_TIMESTAMP
                 )
                 """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            clerk_id   TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_ratings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            article_id INTEGER NOT NULL REFERENCES articles(id),
            rating     INTEGER NOT NULL CHECK(rating IN (-1, 1)),
            rated_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, article_id)
        )
    """)
    conn.execute("""
                 CREATE TABLE IF NOT EXISTS article_reads
                 (
                     id         INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id    INTEGER NOT NULL REFERENCES users (id),
                     article_id INTEGER NOT NULL REFERENCES articles (id),
                     read_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                     UNIQUE (user_id, article_id)
                 )
                 """)
    conn.commit()
    conn.close()