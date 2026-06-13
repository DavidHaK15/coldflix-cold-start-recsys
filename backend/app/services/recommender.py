from __future__ import annotations

from app.models.schemas import RecommendRequest, RecommendationOut
from app.services.dataset import DatasetService


class RecommenderService:
    def __init__(self, dataset: DatasetService) -> None:
        self.dataset = dataset

    def recommend(self, request: RecommendRequest) -> list[RecommendationOut]:
        bundle = self.dataset.bundle
        lookup = self.dataset.movie_lookup()
        exclude: set[int] = set()

        if request.user_id is not None:
            exclude.update(bundle.user_histories.get(request.user_id, {}).keys())

        if request.strategy == "popularity":
            ranked = sorted(
                bundle.movie_popularity.items(),
                key=lambda item: item[1],
                reverse=True,
            )
            ranked = [(mid, score) for mid, score in ranked if mid not in exclude]
        elif request.strategy == "content":
            profile = self.dataset.content_vector_for_genres(request.preferred_genres)
            ranked = self.dataset.cosine_scores_from_profile(profile, exclude)
        elif request.strategy == "onboarding":
            history = {int(k): float(v) for k, v in request.onboarding_ratings.items()}
            exclude.update(history.keys())
            if history:
                ranked = self.dataset.item_cf_scores(history, exclude)
            else:
                ranked = sorted(
                    bundle.movie_popularity.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
                ranked = [(mid, score) for mid, score in ranked if mid not in exclude]
        elif request.strategy == "dropout":
            history: dict[int, float] = {}
            if request.user_id is not None:
                history = dict(bundle.user_histories.get(request.user_id, {}))
            history.update({int(k): float(v) for k, v in request.onboarding_ratings.items()})
            exclude.update(history.keys())
            ranked = self.dataset.dropout_scores(history, request.preferred_genres, exclude)
        elif request.strategy == "item_cf":
            if request.user_id is None:
                raise ValueError("item_cf requires user_id")
            history = bundle.user_histories.get(request.user_id, {})
            ranked = self.dataset.item_cf_scores(history, exclude)
        else:
            raise ValueError(f"Unknown strategy: {request.strategy}")

        results: list[RecommendationOut] = []
        for movie_id, score in ranked:
            info = lookup.get(movie_id)
            if info is None:
                continue
            results.append(
                RecommendationOut(
                    movie_id=movie_id,
                    title=info["title"],
                    genres=info["genres"],
                    score=float(score),
                    strategy=request.strategy,
                    year=info["year"],
                    runtime=info["runtime"],
                    maturity=info["maturity"],
                    tagline=info["tagline"],
                    overview=info["overview"],
                    avg_rating=info["avg_rating"],
                    rating_count=info["rating_count"],
                )
            )
            if len(results) >= request.top_n:
                break
        return results

    def onboarding_items(self) -> list[dict]:
        return self.dataset.diverse_onboarding_items()
