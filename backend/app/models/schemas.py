from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StrategyName = Literal["popularity", "content", "onboarding", "dropout", "item_cf"]


class MovieOut(BaseModel):
    movie_id: int
    title: str
    genres: list[str]
    year: int = 0
    runtime: int = 0
    maturity: str = ""
    tagline: str = ""
    overview: str = ""
    popularity_score: float = 0.0
    avg_rating: float = 0.0
    rating_count: int = 0


class RecommendationOut(BaseModel):
    movie_id: int
    title: str
    genres: list[str]
    score: float
    strategy: str
    year: int = 0
    runtime: int = 0
    maturity: str = ""
    tagline: str = ""
    overview: str = ""
    avg_rating: float = 0.0
    rating_count: int = 0


class RecommendRequest(BaseModel):
    strategy: StrategyName = "popularity"
    top_n: int = Field(default=10, ge=1, le=50)
    user_id: int | None = None
    preferred_genres: list[str] = Field(default_factory=list)
    onboarding_ratings: dict[int, float] = Field(default_factory=dict)


class LearningCurvePoint(BaseModel):
    interactions: int
    recall_at_10: float


class StrategyCurve(BaseModel):
    strategy: str
    label: str
    points: list[LearningCurvePoint]


class LearningCurveResponse(BaseModel):
    curves: list[StrategyCurve]
    sample_users: int
    note: str


class DatasetStats(BaseModel):
    num_users: int
    num_movies: int
    num_ratings: int
    num_genres: int
    avg_rating: float
    sparsity: float


class StrategyInfo(BaseModel):
    id: StrategyName
    name: str
    description: str
    cold_start_type: str
