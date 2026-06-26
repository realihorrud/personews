from fastapi import APIRouter, Depends
from auth import get_current_user
from database import get_conn
from routes.users import sync_user

router = APIRouter(tags=["categories"])


@router.get("/categories")
async def get_categories(user=Depends(get_current_user)):
    conn = get_conn()
    rows = conn.execute("""
                        SELECT category, COUNT(*) as count
                        FROM articles
                        WHERE category IS NOT NULL
                        GROUP BY category
                        ORDER BY count DESC
                        """).fetchall()
    return {
        "categories": [
            {"name": row["category"], "count": row["count"]}
            for row in rows
        ]
    }


@router.get("/stats")
async def get_user_stats(user=Depends(get_current_user)):
    conn = get_conn()
    user_id = sync_user(conn, user["sub"])

    total_rated = conn.execute("""
                               SELECT COUNT(*)
                               FROM article_ratings
                               WHERE user_id = ?
                               """, (user_id,)).fetchone()[0]

    top_categories = conn.execute("""
                                  SELECT a.category, COUNT(*) as count
                                  FROM article_ratings r
                                           JOIN articles a ON a.id = r.article_id
                                  WHERE r.user_id = ?
                                    AND r.rating = 1
                                    AND a.category IS NOT NULL
                                  GROUP BY a.category
                                  ORDER BY count DESC
                                  LIMIT 3
                                  """, (user_id,)).fetchall()

    return {
        "total_rated": total_rated,
        "top_categories": [
            {"name": row["category"], "count": row["count"]}
            for row in top_categories
        ]
    }
