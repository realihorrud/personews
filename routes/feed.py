from fastapi import APIRouter, Depends
from auth import get_current_user
from database import get_conn
from routes.users import sync_user
from ml.recommender import get_recommendations
from models import Article

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=dict)
async def get_feed(limit: int = 20, user=Depends(get_current_user)):
    conn = get_conn()
    user_id = sync_user(conn, user["sub"])
    recs = get_recommendations(conn, user_id, limit=limit)
    articles = [
        Article(
            id=r[1],
            title=r[2],
            summary=None,
            url=r[5],
            source=r[3],
            category=r[4],
            published_at=r[6],
            match_score=round(float(r[0]), 3),
        )
        for r in recs
    ]
    return {"articles": [a.model_dump() for a in articles]}
