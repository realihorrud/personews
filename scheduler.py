from fetcher import fetch_all_feeds
from ml.categorizer import categorize_articles
from ml.embeddings import embed_articles
from database import get_conn

def run_pipeline():
    print("Pipeline started...")
    fetch_all_feeds()

    conn = get_conn()
    categorize_articles(conn)
    embed_articles(conn)
    conn.close()
    print("Pipeline complete.")