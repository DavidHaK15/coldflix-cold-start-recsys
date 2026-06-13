"""Smoke + sanity tests cho Cold-Start Recommendation API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json()["status"] == "ok"


def test_stats(client: TestClient) -> None:
    stats = client.get("/api/stats").json()
    assert stats["num_movies"] > 0
    assert stats["num_users"] > 0
    assert 0 < stats["sparsity"] < 1


def test_catalog_has_metadata(client: TestClient) -> None:
    catalog = client.get("/api/catalog").json()
    assert len(catalog) > 0
    movie = catalog[0]
    for key in ("title", "genres", "year", "overview", "avg_rating"):
        assert key in movie


@pytest.mark.parametrize("strategy", ["popularity", "content", "onboarding", "dropout"])
def test_recommend_returns_results(client: TestClient, strategy: str) -> None:
    body = {
        "strategy": strategy,
        "top_n": 10,
        "preferred_genres": ["Action", "Sci-Fi"],
        "onboarding_ratings": {},
    }
    res = client.post("/api/recommend", json=body)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10
    assert all(item["strategy"] == strategy for item in data)


def test_personalization_differs_from_popularity(client: TestClient) -> None:
    pop = [r["movie_id"] for r in client.post(
        "/api/recommend", json={"strategy": "popularity", "top_n": 10}).json()]
    content = [r["movie_id"] for r in client.post(
        "/api/recommend",
        json={"strategy": "content", "top_n": 10, "preferred_genres": ["Horror", "Mystery"]},
    ).json()]
    assert pop != content  # cá nhân hoá phải khác baseline


def test_item_cf_requires_user(client: TestClient) -> None:
    res = client.post("/api/recommend", json={"strategy": "item_cf", "top_n": 5})
    assert res.status_code == 400


def test_learning_curve_personalization_beats_popularity_when_warm(client: TestClient) -> None:
    lc = client.get("/api/evaluation/learning-curve?sample_users=40").json()
    curves = {c["strategy"]: c["points"] for c in lc["curves"]}

    def recall_at(strategy: str, interactions: int) -> float:
        return next(p["recall_at_10"] for p in curves[strategy] if p["interactions"] == interactions)

    # Khi đã có 20 tương tác, DropoutNet (hybrid) nên >= popularity baseline.
    assert recall_at("dropout", 20) >= recall_at("popularity", 20)
