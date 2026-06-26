from fetcher import fetch_all_feeds
from ml.categorizer import categorize_articles
from ml.embeddings import embed_articles
from database import get_conn


def run_pipeline():
    try:
        print("Pipeline started...")
        fetch_all_feeds()
        conn = get_conn()
        print("Categorizing and embedding articles...")
        categorize_articles(conn)
        embed_articles(conn)
        conn.close()
        print("Pipeline complete.")
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
