from fetcher import fetch_all_feeds
from ml.categorizer import categorize_articles
from ml.embeddings import embed_articles
from database import get_conn

def run_pipeline():
    print("Pipeline started...")
    fetch_all_feeds()

    conn = get_conn()

    try:
        print("Categorizing and embedding articles...")
        categorize_articles(conn)
        embed_articles(conn)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

    conn.close()
    print("Pipeline complete.")