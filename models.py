from pydantic import BaseModel
from typing import Optional

class Article(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    url: str
    source: str
    category: Optional[str]
    published_at: Optional[str]
    match_score: Optional[float] = None

class RatingRequest(BaseModel):
    article_id: int
    rating: int  # 1 or -1

class CategoryStat(BaseModel):
    name: str
    count: int