from fastapi import APIRouter, Depends
from auth import get_current_user
from database import get_conn

router = APIRouter(prefix="/users", tags=["users"])

def sync_user(conn, clerk_id: str) -> int:
    user = conn.execute(
        "SELECT id FROM users WHERE clerk_id = ?", (clerk_id,)
    ).fetchone()
    if user:
        return user["id"]
    conn.execute(
        "INSERT INTO users (clerk_id) VALUES (?)", (clerk_id,)
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM users WHERE clerk_id = ?", (clerk_id,)
    ).fetchone()["id"]

@router.post("/sync")
async def sync(user=Depends(get_current_user)):
    conn = get_conn()
    user_id = sync_user(conn, user["sub"])
    return {"user_id": user_id}