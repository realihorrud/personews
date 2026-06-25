import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def get_model():
    return SentenceTransformer(MODEL_NAME)


def add_embedding_column(conn):
    try:
        conn.execute("""
                     ALTER TABLE articles
                         ADD COLUMN embedding BLOB
                     """)
        conn.commit()
    except Exception:
        pass


def embed_articles(conn):
    add_embedding_column(conn)

    articles = conn.execute("""
                            SELECT id, title, summary
                            FROM articles
                            WHERE embedding IS NULL
                            """).fetchall()

    if not articles:
        print("All articles already embedded.")
        return

    model = get_model()
    texts = [f"{title}. {summary or ''}" for _, title, summary in articles]

    print(f"Embedding {len(articles)} articles...")

    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    updates = [(emb.astype(np.float32).tobytes(), article_id) for (article_id, _, _), emb in zip(articles, embeddings)]
    conn.executemany("UPDATE articles SET embedding = ? WHERE id = ?", updates)
    conn.commit()
    print(f"Done.")


def load_embedding(blob):
    return np.frombuffer(blob, dtype=np.float32)
