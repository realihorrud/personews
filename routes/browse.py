# routes/browse.py
from fastapi import APIRouter, Depends, Query
from auth import get_current_user
from database import get_conn
from routes.users import sync_user
from models import Article

router = APIRouter(prefix="/browse", tags=["browse"])


@router.get("/categories")
async def get_browse_categories(user=Depends(get_current_user)):
    conn = get_conn()
    user_id = sync_user(conn, user["sub"])

    rows = conn.execute("""
                        SELECT a.category, COUNT(*) as count
                        FROM articles a
                                 LEFT JOIN article_ratings r
                                           ON a.id = r.article_id AND r.user_id = ?
                                 LEFT JOIN article_reads rd
                                           ON a.id = rd.article_id AND rd.user_id = ?
                        WHERE r.id IS NULL
                          AND rd.id IS NULL
                          AND a.category IS NOT NULL
                        GROUP BY a.category
                        ORDER BY count DESC
                        """, (user_id, user_id)).fetchall()

    return {
        "categories": [
            {"name": row["category"], "count": row["count"]}
            for row in rows
        ]
    }


@router.get("")
async def browse_articles(
        category: str = Query(..., description="Category name to browse"),
        per_source: int = Query(4, description="Max articles per source"),
        user=Depends(get_current_user),
):
    conn = get_conn()
    user_id = sync_user(conn, user["sub"])

    rows = conn.execute("""
                        WITH ranked AS (SELECT a.id,
                                               a.title,
                                               a.summary,
                                               a.url,
                                               a.source,
                                               a.category,
                                               a.published_at,
                                               ROW_NUMBER() OVER (
                                                   PARTITION BY a.source
                                                   ORDER BY a.published_at DESC
                                                   ) AS rn
                                        FROM articles a
                                                 LEFT JOIN article_ratings r
                                                           ON a.id = r.article_id AND r.user_id = ?
                                                 LEFT JOIN article_reads rd
                                                           ON a.id = rd.article_id AND rd.user_id = ?
                                        WHERE r.id IS NULL
                                          AND rd.id IS NULL
                                          AND a.category = ?)
                        SELECT id, title, summary, url, source, category, published_at
                        FROM ranked
                        WHERE rn <= ?
                        ORDER BY RANDOM()
                        """, (user_id, user_id, category, per_source)).fetchall()

    return {
        "category": category,
        "articles": [
            Article(
                id=row["id"],
                title=row["title"],
                summary=row["summary"],
                url=row["url"],
                source=row["source"],
                category=row["category"],
                published_at=row["published_at"],
                match_score=None,
            ).model_dump()
            for row in rows
        ]
    }
