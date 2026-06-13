from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.models.schemas import (
    DatasetStats,
    LearningCurveResponse,
    MovieOut,
    RecommendRequest,
    RecommendationOut,
    StrategyInfo,
)
from app.services.dataset import DatasetService
from app.services.evaluation import EvaluationService
from app.services.recommender import RecommenderService

app = FastAPI(
    title="Cold-Start Recommendation System",
    description="Chủ đề 7: Xử lý vấn đề Cold-Start trong Hệ Thống Khuyến Nghị",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dataset_service = DatasetService()
recommender_service = RecommenderService(dataset_service)
evaluation_service = EvaluationService(dataset_service, recommender_service)

STRATEGIES: list[StrategyInfo] = [
    StrategyInfo(
        id="popularity",
        name="Popularity-based",
        description="Khuyến nghị sản phẩm phổ biến nhất: score(i) = log(|U_i| + 1). Baseline cho người dùng mới.",
        cold_start_type="New User",
    ),
    StrategyInfo(
        id="content",
        name="Content-based Bootstrapping",
        description="Dùng thể loại yêu thích + TF-IDF cosine similarity. Hoạt động ngay cả khi 0 tương tác.",
        cold_start_type="New User / New Item",
    ),
    StrategyInfo(
        id="onboarding",
        name="Onboarding + Item-CF",
        description="Người dùng xếp hạng vài sản phẩm đa dạng, sau đó chạy Item-based Collaborative Filtering.",
        cold_start_type="New User",
    ),
    StrategyInfo(
        id="dropout",
        name="DropoutNet (đơn giản hóa)",
        description="Kết hợp content embedding và MF embedding. Trọng số content cao khi ít tương tác.",
        cold_start_type="New User",
    ),
    StrategyInfo(
        id="item_cf",
        name="Item-CF (Warm User)",
        description="Item-based CF cho người dùng đã có lịch sử — dùng để so sánh khi không còn cold-start.",
        cold_start_type="Warm User",
    ),
]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "topic": "Chủ đề 7 - Cold Start Problem"}


@app.get("/api/stats", response_model=DatasetStats)
def stats() -> DatasetStats:
    return DatasetStats(**dataset_service.get_stats())


@app.get("/api/strategies", response_model=list[StrategyInfo])
def strategies() -> list[StrategyInfo]:
    return STRATEGIES


@app.get("/api/genres")
def genres() -> dict[str, list[str]]:
    return {"genres": dataset_service.get_genres()}


@app.get("/api/catalog", response_model=list[MovieOut])
def catalog() -> list[MovieOut]:
    return [MovieOut(**movie) for movie in dataset_service.get_movies()]


@app.get("/api/movies", response_model=list[MovieOut])
def movies(limit: int = 100) -> list[MovieOut]:
    return [MovieOut(**movie) for movie in dataset_service.get_movies(limit=limit)]


@app.get("/api/users/warm")
def warm_users(min_interactions: int = 20) -> dict:
    users = dataset_service.get_warm_users(min_interactions=min_interactions)
    return {"users": users[:100], "total": len(users)}


@app.get("/api/users/{user_id}/history")
def user_history(user_id: int) -> dict:
    history = dataset_service.bundle.user_histories.get(user_id)
    if history is None:
        raise HTTPException(status_code=404, detail="User not found")
    lookup = dataset_service.movie_lookup()
    items = []
    for movie_id, rating in sorted(history.items(), key=lambda item: item[1], reverse=True):
        info = lookup.get(movie_id)
        if info is None:
            continue
        items.append({**info, "rating": rating})
    return {"user_id": user_id, "history": items, "count": len(items)}


@app.get("/api/onboarding/items", response_model=list[MovieOut])
def onboarding_items() -> list[MovieOut]:
    return [MovieOut(**item) for item in recommender_service.onboarding_items()]


@app.get("/api/similar/{movie_id}", response_model=list[MovieOut])
def similar(movie_id: int, top_n: int = 12) -> list[MovieOut]:
    lookup = dataset_service.movie_lookup()
    if movie_id not in lookup:
        raise HTTPException(status_code=404, detail="Movie not found")
    pairs = dataset_service.similar_items(movie_id, top_n=top_n)
    return [MovieOut(**lookup[mid]) for mid, _ in pairs if mid in lookup]


@app.post("/api/recommend", response_model=list[RecommendationOut])
def recommend(request: RecommendRequest) -> list[RecommendationOut]:
    try:
        return recommender_service.recommend(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/evaluation/learning-curve", response_model=LearningCurveResponse)
def learning_curve(sample_users: int = 40) -> LearningCurveResponse:
    return evaluation_service.learning_curve(sample_users=min(max(sample_users, 5), 100))


# --- Phục vụ frontend đã build (tùy chọn) --------------------------------------
# Chỉ bật khi tồn tại thư mục static (vd trong Docker all-in-one). Dev không ảnh hưởng.
import os
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_STATIC_DIR = Path(os.getenv("STATIC_DIR", "/app/static"))
if _STATIC_DIR.is_dir():
    _assets = _STATIC_DIR / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        candidate = _STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC_DIR / "index.html")  # SPA: mọi route khác → index.html
