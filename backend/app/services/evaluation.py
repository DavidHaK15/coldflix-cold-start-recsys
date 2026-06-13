from __future__ import annotations

import random

from app.config import LEARNING_CURVE_POINTS
from app.models.schemas import LearningCurvePoint, LearningCurveResponse, RecommendRequest, StrategyCurve
from app.services.dataset import DatasetService
from app.services.recommender import RecommenderService


class EvaluationService:
    STRATEGY_LABELS = {
        "popularity": "Popularity-based",
        "content": "Content-based Bootstrapping",
        "onboarding": "Onboarding + Item-CF",
        "dropout": "DropoutNet (đơn giản hóa)",
    }

    def __init__(self, dataset: DatasetService, recommender: RecommenderService) -> None:
        self.dataset = dataset
        self.recommender = recommender

    def recall_at_k(self, recommended: list[int], relevant: set[int], k: int = 10) -> float:
        if not relevant:
            return 0.0
        hits = len(set(recommended[:k]) & relevant)
        return hits / min(k, len(relevant))

    def _preferred_genres_from_history(self, history: dict[int, float], lookup: dict[int, dict]) -> list[str]:
        genre_weights: dict[str, float] = {}
        for item_id, rating in history.items():
            info = lookup.get(item_id)
            if not info:
                continue
            for genre in info["genres"]:
                genre_weights[genre] = genre_weights.get(genre, 0.0) + rating
        if not genre_weights:
            return []
        top_genres = sorted(genre_weights.items(), key=lambda item: item[1], reverse=True)
        return [genre for genre, _ in top_genres[:3]]

    def learning_curve(self, sample_users: int = 40, seed: int = 42) -> LearningCurveResponse:
        bundle = self.dataset.bundle
        lookup = self.dataset.movie_lookup()
        warm_users = self.dataset.get_warm_users(min_interactions=max(LEARNING_CURVE_POINTS) + 5)
        rng = random.Random(seed)
        selected_users = rng.sample(warm_users, min(sample_users, len(warm_users)))

        curves: list[StrategyCurve] = []
        for strategy, label in self.STRATEGY_LABELS.items():
            points: list[LearningCurvePoint] = []
            for interaction_count in LEARNING_CURVE_POINTS:
                recalls: list[float] = []
                for user_id in selected_users:
                    full_history = bundle.user_histories[user_id]
                    items = list(full_history.items())
                    user_rng = random.Random(f"{seed}-{user_id}")
                    user_rng.shuffle(items)
                    holdout = {item_id for item_id, _ in items[: max(5, len(items) // 5)]}
                    train_items = {
                        item_id: rating
                        for item_id, rating in items
                        if item_id not in holdout
                    }
                    if interaction_count == 0:
                        visible_history: dict[int, float] = {}
                    else:
                        visible_history = dict(list(train_items.items())[:interaction_count])

                    preferred_genres = self._preferred_genres_from_history(visible_history, lookup)
                    # Mô phỏng cold-start: coi như người dùng MỚI (user_id=None) để recommender
                    # không loại trừ phần holdout, chỉ thấy `visible_history` qua onboarding_ratings.
                    request = RecommendRequest(
                        strategy=strategy,
                        top_n=10,
                        user_id=None,
                        preferred_genres=preferred_genres,
                        onboarding_ratings=visible_history,
                    )
                    recs = self.recommender.recommend(request)
                    recall = self.recall_at_k([rec.movie_id for rec in recs], holdout, k=10)
                    recalls.append(recall)

                avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
                points.append(
                    LearningCurvePoint(
                        interactions=interaction_count,
                        recall_at_10=round(avg_recall, 4),
                    )
                )

            curves.append(StrategyCurve(strategy=strategy, label=label, points=points))

        return LearningCurveResponse(
            curves=curves,
            sample_users=len(selected_users),
            note=(
                "Mô phỏng cold-start: ẩn một phần lịch sử người dùng warm, "
                "chỉ cung cấp N tương tác ban đầu cho từng chiến lược."
            ),
        )
