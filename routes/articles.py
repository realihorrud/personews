from fastapi import APIRouter, Depends
from auth import get_current_user
from database import get_conn
from routes.users import sync_user

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("/{article_id}/read")
async def mark_as_read(article_id: int, user=Depends(get_current_user)):
    conn = get_conn()
    user_id = sync_user(conn, user["sub"])
    rating = 1
    conn.execute("""
                 INSERT OR IGNORE INTO article_reads (user_id, article_id)
                 VALUES (?, ?)
                 """, (user_id, article_id))
    conn.execute("""
                 INSERT OR IGNORE INTO article_ratings (user_id, article_id, rating)
                 VALUES (?, ?, ?)
                 """, (user_id, article_id, rating))
    conn.commit()
    return {"status": "ok"}
