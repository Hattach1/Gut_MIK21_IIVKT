from pydantic import BaseModel
from typing import Optional, List

class GameBase(BaseModel):
    steam_app_id: Optional[int] = None
    name: str
    genres: Optional[str] = None
    tags: Optional[str] = None
    short_description: Optional[str] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None
    image_url: Optional[str] = None


class GameCreate(GameBase):
    pass


class GameResponse(GameBase):
    id: int

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    liked_titles: List[str]
    top_k: int = 5


class SimilarGamesRequest(BaseModel):
    title: str
    top_k: int = 5


class EvaluationRequest(BaseModel):
    liked_titles: List[str]
    top_k: int = 5
    test_ratio: float = 0.4