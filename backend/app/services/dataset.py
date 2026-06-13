from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field

import numpy as np

# numpy 2.x phát cảnh báo matmul dương-tính-giả trên một số nền BLAS; kết quả vẫn đúng.
for _msg in ("divide by zero encountered in matmul",
             "overflow encountered in matmul",
             "invalid value encountered in matmul"):
    warnings.filterwarnings("ignore", message=_msg, category=RuntimeWarning)
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import DATA_DIR, MF_FACTORS, MIN_USER_INTERACTIONS

# Cột metadata tuỳ chọn — dữ liệu thật (MovieLens) có thể không có, nên đều có giá trị mặc định.
META_COLUMNS = ["year", "runtime", "maturity", "tagline", "overview"]


@dataclass
class DatasetBundle:
    ratings: pd.DataFrame
    movies: pd.DataFrame
    user_histories: dict[int, dict[int, float]] = field(default_factory=dict)
    movie_popularity: dict[int, float] = field(default_factory=dict)
    movie_rating_count: dict[int, int] = field(default_factory=dict)
    movie_avg_rating: dict[int, float] = field(default_factory=dict)
    genre_list: list[str] = field(default_factory=list)
    movie_ids: list[int] = field(default_factory=list)
    tfidf_vectorizer: TfidfVectorizer | None = None
    tfidf_matrix: object | None = None
    item_similarity: np.ndarray | None = None
    user_factors: dict[int, np.ndarray] = field(default_factory=dict)
    item_factors: dict[int, np.ndarray] = field(default_factory=dict)
    global_mean: float = 0.0


class DatasetService:
    def __init__(self) -> None:
        self._bundle: DatasetBundle | None = None
        self._lookup: dict[int, dict] | None = None

    @property
    def bundle(self) -> DatasetBundle:
        if self._bundle is None:
            self._bundle = self._load()
        return self._bundle

    def reload(self) -> DatasetBundle:
        self._lookup = None
        self._bundle = self._load()
        return self._bundle

    def _load(self) -> DatasetBundle:
        ratings = pd.read_csv(DATA_DIR / "ratings.csv")
        movies = pd.read_csv(DATA_DIR / "movies.csv")

        movies["genres_list"] = movies["genres"].fillna("").apply(
            lambda value: [g for g in str(value).split("|") if g and g != "(no genres listed)"]
        )
        genre_list = sorted({genre for genres in movies["genres_list"] for genre in genres})

        for column in META_COLUMNS:
            if column not in movies.columns:
                movies[column] = "" if column in {"maturity", "tagline", "overview"} else 0

        user_histories: dict[int, dict[int, float]] = {}
        for row in ratings.itertuples(index=False):
            user_histories.setdefault(int(row.userId), {})[int(row.movieId)] = float(row.rating)

        popularity_counts = ratings.groupby("movieId")["userId"].nunique()
        movie_popularity = {
            int(movie_id): math.log(count + 1) for movie_id, count in popularity_counts.items()
        }
        movie_rating_count = {int(mid): int(c) for mid, c in popularity_counts.items()}
        avg_by_movie = ratings.groupby("movieId")["rating"].mean()
        movie_avg_rating = {int(mid): float(v) for mid, v in avg_by_movie.items()}

        # --- Content model: TF-IDF trên thể loại ---
        movies["genre_text"] = movies["genres_list"].apply(lambda genres: " ".join(genres))
        vectorizer = TfidfVectorizer(token_pattern=r"[^ ]+")
        tfidf_matrix = vectorizer.fit_transform(movies["genre_text"].tolist())
        all_movie_ids = movies["movieId"].astype(int).tolist()

        # --- Item-based CF: cosine similarity trên ma trận item x user ---
        pivot = ratings.pivot_table(
            index="userId", columns="movieId", values="rating", fill_value=0.0
        )
        rated_movie_ids = [int(movie_id) for movie_id in pivot.columns]
        item_vectors = pivot.values.T.astype(np.float64)  # item x user
        norms = np.linalg.norm(item_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = item_vectors / norms
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            item_similarity = normalized @ normalized.T
        item_similarity = np.nan_to_num(item_similarity, nan=0.0, posinf=0.0, neginf=0.0)
        movie_ids = rated_movie_ids

        # --- Matrix Factorization (TruncatedSVD) cho thành phần collaborative của DropoutNet ---
        global_mean = float(ratings["rating"].mean())
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            user_factors, item_factors = self._train_mf_factors(pivot, n_factors=MF_FACTORS)

        return DatasetBundle(
            ratings=ratings,
            movies=movies,
            user_histories=user_histories,
            movie_popularity=movie_popularity,
            movie_rating_count=movie_rating_count,
            movie_avg_rating=movie_avg_rating,
            genre_list=genre_list,
            movie_ids=all_movie_ids,
            tfidf_vectorizer=vectorizer,
            tfidf_matrix=tfidf_matrix,
            item_similarity=item_similarity,
            user_factors=user_factors,
            item_factors=item_factors,
            global_mean=global_mean,
        )

    def _train_mf_factors(
        self, pivot: pd.DataFrame, n_factors: int = 16
    ) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
        """Phân rã ma trận rating bằng TruncatedSVD (nhanh, ổn định khi khởi động)."""
        matrix = pivot.values.astype(np.float64)  # user x item
        k = min(n_factors, min(matrix.shape) - 1)
        # arpack ổn định hơn solver randomized mặc định trên ma trận thưa cỡ này.
        svd = TruncatedSVD(n_components=max(k, 2), algorithm="arpack", random_state=42)
        user_embeddings = svd.fit_transform(matrix)  # user x k
        item_embeddings = svd.components_.T  # item x k

        user_ids = [int(u) for u in pivot.index]
        item_ids = [int(i) for i in pivot.columns]
        user_map = {user_ids[idx]: user_embeddings[idx] for idx in range(len(user_ids))}
        item_map = {item_ids[idx]: item_embeddings[idx] for idx in range(len(item_ids))}
        return user_map, item_map

    # ------------------------------------------------------------------ stats
    def get_stats(self) -> dict:
        bundle = self.bundle
        num_users = bundle.ratings["userId"].nunique()
        num_movies = bundle.ratings["movieId"].nunique()
        num_ratings = len(bundle.ratings)
        density = num_ratings / (num_users * num_movies)
        return {
            "num_users": int(num_users),
            "num_movies": int(num_movies),
            "num_ratings": int(num_ratings),
            "num_genres": len(bundle.genre_list),
            "avg_rating": float(bundle.ratings["rating"].mean()),
            "sparsity": float(1 - density),
        }

    def _movie_payload(self, row) -> dict:
        bundle = self.bundle
        mid = int(row.movieId)
        return {
            "movie_id": mid,
            "title": str(row.title),
            "genres": list(row.genres_list),
            "year": int(getattr(row, "year", 0) or 0),
            "runtime": int(getattr(row, "runtime", 0) or 0),
            "maturity": str(getattr(row, "maturity", "") or ""),
            "tagline": str(getattr(row, "tagline", "") or ""),
            "overview": str(getattr(row, "overview", "") or ""),
            "popularity_score": float(bundle.movie_popularity.get(mid, 0.0)),
            "avg_rating": round(bundle.movie_avg_rating.get(mid, 0.0), 2),
            "rating_count": int(bundle.movie_rating_count.get(mid, 0)),
        }

    def get_movies(self, limit: int | None = None) -> list[dict]:
        bundle = self.bundle
        frame = bundle.movies if limit is None else bundle.movies.head(limit)
        return [self._movie_payload(row) for row in frame.itertuples(index=False)]

    def get_genres(self) -> list[str]:
        return self.bundle.genre_list

    def get_warm_users(self, min_interactions: int = MIN_USER_INTERACTIONS) -> list[int]:
        bundle = self.bundle
        return [
            user_id
            for user_id, history in bundle.user_histories.items()
            if len(history) >= min_interactions
        ]

    def movie_lookup(self) -> dict[int, dict]:
        if self._lookup is None:
            bundle = self.bundle
            self._lookup = {
                payload["movie_id"]: payload
                for payload in (self._movie_payload(r) for r in bundle.movies.itertuples(index=False))
            }
        return self._lookup

    # --------------------------------------------------------------- content
    def content_vector_for_genres(self, genres: list[str]) -> np.ndarray:
        bundle = self.bundle
        assert bundle.tfidf_vectorizer is not None
        text = " ".join(genres) if genres else "Unknown"
        return np.asarray(bundle.tfidf_vectorizer.transform([text]).toarray(), dtype=np.float64)

    def content_vector_for_items(self, item_ids: list[int], ratings_map: dict[int, float]) -> np.ndarray:
        bundle = self.bundle
        assert bundle.tfidf_matrix is not None
        index = {mid: idx for idx, mid in enumerate(bundle.movie_ids)}
        vectors, weights = [], []
        for item_id, rating in ratings_map.items():
            if item_id not in index:
                continue
            vectors.append(bundle.tfidf_matrix[index[item_id]].toarray()[0].astype(np.float64))
            weights.append(max(rating, 1.0))
        if not vectors:
            return self.content_vector_for_genres([])
        profile = np.average(np.array(vectors), axis=0, weights=np.array(weights))
        return np.asarray(profile, dtype=np.float64).reshape(1, -1)

    def cosine_scores_from_profile(self, profile: np.ndarray, exclude: set[int]) -> list[tuple[int, float]]:
        bundle = self.bundle
        assert bundle.tfidf_matrix is not None
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            scores = cosine_similarity(profile, bundle.tfidf_matrix).flatten()
        ranked = [
            (bundle.movie_ids[idx], float(score))
            for idx, score in enumerate(scores)
            if bundle.movie_ids[idx] not in exclude
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    # -------------------------------------------------------------- item-CF
    def item_cf_scores(
        self, history: dict[int, float], exclude: set[int], top_neighbors: int = 20
    ) -> list[tuple[int, float]]:
        bundle = self.bundle
        assert bundle.item_similarity is not None
        movie_index = {movie_id: idx for idx, movie_id in enumerate(bundle.movie_ids)}
        scores: dict[int, float] = {}
        sim_sums: dict[int, float] = {}

        for rated_item, rating in history.items():
            if rated_item not in movie_index:
                continue
            sims = bundle.item_similarity[movie_index[rated_item]]
            neighbor_indices = np.argsort(sims)[::-1][1 : top_neighbors + 1]
            for neighbor_idx in neighbor_indices:
                neighbor_id = bundle.movie_ids[int(neighbor_idx)]
                if neighbor_id in exclude:
                    continue
                sim = float(sims[int(neighbor_idx)])
                if sim <= 0:
                    continue
                scores[neighbor_id] = scores.get(neighbor_id, 0.0) + sim * rating
                sim_sums[neighbor_id] = sim_sums.get(neighbor_id, 0.0) + abs(sim)

        ranked = [
            (item_id, score / sim_sums[item_id])
            for item_id, score in scores.items()
            if sim_sums.get(item_id, 0) > 0
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    def similar_items(self, movie_id: int, top_n: int = 12) -> list[tuple[int, float]]:
        bundle = self.bundle
        assert bundle.item_similarity is not None
        index = {mid: idx for idx, mid in enumerate(bundle.movie_ids)}
        if movie_id not in index:
            return []
        sims = bundle.item_similarity[index[movie_id]]
        order = np.argsort(sims)[::-1]
        results: list[tuple[int, float]] = []
        for idx in order:
            mid = bundle.movie_ids[int(idx)]
            if mid == movie_id:
                continue
            score = float(sims[int(idx)])
            if score <= 0:
                break
            results.append((mid, score))
            if len(results) >= top_n:
                break
        return results

    # ------------------------------------------------------------------- MF
    def mf_scores(self, user_id: int | None, history: dict[int, float], exclude: set[int]) -> list[tuple[int, float]]:
        bundle = self.bundle
        dim = MF_FACTORS
        if bundle.item_factors:
            dim = len(next(iter(bundle.item_factors.values())))
        if user_id is not None and user_id in bundle.user_factors:
            user_vec = bundle.user_factors[user_id]
        else:
            vectors = [bundle.item_factors[i] for i in history if i in bundle.item_factors]
            user_vec = np.mean(vectors, axis=0) if vectors else np.zeros(dim)

        ranked = [
            (item_id, float(user_vec @ item_vec))
            for item_id, item_vec in bundle.item_factors.items()
            if item_id not in exclude
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    # -------------------------------------------------------------- DropoutNet
    def dropout_scores(
        self, history: dict[int, float], preferred_genres: list[str], exclude: set[int]
    ) -> list[tuple[int, float]]:
        content_profile = self.content_vector_for_items(list(history.keys()), history)
        if preferred_genres:
            genre_profile = self.content_vector_for_genres(preferred_genres)
            content_profile = 0.6 * content_profile + 0.4 * genre_profile

        content_ranked = dict(self.cosine_scores_from_profile(content_profile, exclude))
        mf_ranked = dict(self.mf_scores(None, history, exclude))

        # chuẩn hoá điểm MF về [0,1] để cộng tuyến tính có nghĩa
        if mf_ranked:
            values = np.array(list(mf_ranked.values()))
            lo, hi = float(values.min()), float(values.max())
            span = (hi - lo) or 1.0
            mf_ranked = {k: (v - lo) / span for k, v in mf_ranked.items()}

        if not history:
            alpha = 1.0
        elif len(history) < 5:
            alpha = 0.75
        elif len(history) < 10:
            alpha = 0.5
        else:
            alpha = 0.25

        all_items = set(content_ranked) | set(mf_ranked)
        combined = [
            (item_id, alpha * content_ranked.get(item_id, 0.0) + (1 - alpha) * mf_ranked.get(item_id, 0.0))
            for item_id in all_items
        ]
        combined.sort(key=lambda item: item[1], reverse=True)
        return combined

    # ----------------------------------------------------------- onboarding
    def diverse_onboarding_items(self, count: int = 12) -> list[dict]:
        bundle = self.bundle
        selected: list[dict] = []
        used_genres: set[str] = set()
        candidates = bundle.movies.copy()
        candidates["popularity"] = candidates["movieId"].map(bundle.movie_popularity).fillna(0.0)
        candidates = candidates.sort_values("popularity", ascending=False)

        for row in candidates.itertuples(index=False):
            genres = set(row.genres_list)
            if genres & used_genres and len(selected) >= 3:
                continue
            selected.append(self._movie_payload(row))
            used_genres |= genres
            if len(selected) >= count:
                break
        return selected
