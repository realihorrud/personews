from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import get_conn
from routes.users import sync_user
from models import RatingRequest

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.post("")
async def submit_rating(body: RatingRequest, user=Depends(get_current_user)):
    if body.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 or -1")
    conn    = get_conn()
    user_id = sync_user(conn, user["sub"])
    conn.execute("""
        INSERT OR REPLACE INTO article_ratings (user_id, article_id, rating)
        VALUES (?, ?, ?)
    """, (user_id, body.article_id, body.rating))
    conn.commit()
    return {"status": "ok"}