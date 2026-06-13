#!/usr/bin/env python3
"""Sinh bộ dữ liệu phim synthetic "kiểu Netflix" cho demo Cold-Start.

Khác với dữ liệu ngẫu nhiên, script này sinh ratings từ *sở thích tiềm ẩn* của
người dùng theo thể loại. Nhờ đó các chiến lược cá nhân hoá (content-based,
item-CF, DropoutNet) thực sự tốt hơn baseline popularity — learning curve mới
dốc lên và minh hoạ đúng giá trị của việc xử lý cold-start.

Sinh ra:
  data/sample/movies.csv   movieId,title,genres,year,runtime,maturity,tagline,overview
  data/sample/ratings.csv  userId,movieId,rating

Chạy:  python scripts/generate_synthetic.py
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sample"

SEED = 7  # Chủ đề 7
NUM_MOVIES = 280
NUM_USERS = 500
RNG = random.Random(SEED)

GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Fantasy", "Horror", "Mystery", "Romance", "Sci-Fi",
    "Thriller", "Western", "Family", "Musical",
]

# Mỗi thể loại có một "maturity" thiên lệch để phần độ tuổi trông hợp lý.
MATURITY = ["G", "PG", "PG-13", "R", "TV-MA"]

# Ngân hàng từ để ghép tên phim theo cảm giác từng thể loại.
TITLE_PARTS = {
    "Action": (["Last", "Iron", "Final", "Rogue", "Crimson", "Steel", "Silent"],
               ["Strike", "Protocol", "Vengeance", "Legacy", "Front", "Pursuit"]),
    "Adventure": (["Lost", "Hidden", "Golden", "Forgotten", "Ancient", "Wild"],
                  ["Horizon", "Expedition", "Kingdom", "Voyage", "Frontier", "Trail"]),
    "Animation": (["Tiny", "Brave", "Happy", "Magic", "Sunny", "Little"],
                  ["Tales", "Friends", "Dreamland", "Adventure", "Heroes", "Party"]),
    "Comedy": (["Awkward", "Crazy", "Perfect", "Wild", "Lucky", "Messy"],
               ["Weekend", "Roommates", "Vacation", "Wedding", "Holidays", "Plan"]),
    "Crime": (["Cold", "Dirty", "Broken", "Dark", "Bad", "Blood"],
              ["City", "Money", "Empire", "Streets", "Heist", "Justice"]),
    "Documentary": (["The Truth About", "Inside", "Beyond", "Voices of", "Planet", "Story of"],
                    ["Earth", "the Deep", "Tomorrow", "the Mind", "Silence", "Wonders"]),
    "Drama": (["Quiet", "Distant", "Tender", "Fragile", "Endless", "After"],
              ["Light", "Promise", "Letters", "Seasons", "Shores", "Hours"]),
    "Fantasy": (["Eternal", "Shadow", "Crystal", "Mystic", "Dragon", "Moonlit"],
                ["Realm", "Crown", "Prophecy", "Spell", "Throne", "Gate"]),
    "Horror": (["Dead", "Whispering", "Cursed", "Hollow", "Midnight", "Pale"],
               ["House", "Woods", "Asylum", "Ritual", "Hour", "Visitor"]),
    "Mystery": (["The Vanishing", "Silent", "Hidden", "Missing", "Secret", "Twelve"],
                ["Witness", "Room", "Cipher", "Case", "Letter", "Echo"]),
    "Romance": (["Love in", "Summer of", "Two Hearts", "Always", "Letters to", "Before"],
                ["Paris", "Autumn", "You", "Sunrise", "Her", "Forever"]),
    "Sci-Fi": (["Neon", "Orbit", "Quantum", "Beyond", "Echo", "Nova"],
               ["Protocol", "Horizon", "Singularity", "Drift", "Station", "Genesis"]),
    "Thriller": (["The Last", "Edge of", "Cold", "Final", "No", "Dead"],
                 ["Witness", "Night", "Signal", "Exit", "Run", "Hostage"]),
    "Western": (["Dust", "Iron", "Red", "Lonesome", "High", "Outlaw"],
                ["Ridge", "Canyon", "Saloon", "Trail", "Noon", "Country"]),
    "Family": (["Our", "The Big", "Home for", "A Very", "Three", "Sunny"],
               ["Holidays", "Family", "Summer", "Reunion", "Dog", "Garden"]),
    "Musical": (["Sing", "Encore", "Spotlight", "Rhythm", "Velvet", "Golden"],
                ["Stage", "Nights", "Anthem", "Symphony", "Stars", "Beat"]),
}

OVERVIEW_TEMPLATES = [
    "Khi mọi thứ tưởng như sụp đổ, một {role} buộc phải đối mặt với {stake} để cứu lấy điều quan trọng nhất.",
    "Một câu chuyện {tone} về {role} trên hành trình tìm lại {stake} giữa những lựa chọn không thể quay đầu.",
    "Bị cuốn vào {stake}, {role} dần khám phá sự thật làm thay đổi tất cả.",
    "Trong một thế giới đầy {tone}, {role} phải trả giá để bảo vệ {stake}.",
    "Số phận đưa đẩy {role} vào cuộc đối đầu định mệnh, nơi {stake} là thứ duy nhất còn lại.",
]
ROLES = ["thám tử cô độc", "gia đình nhỏ", "cô gái trẻ", "người lính trở về",
         "nhóm bạn thân", "nhà khoa học", "kẻ ngoài vòng pháp luật", "phi hành đoàn"]
STAKES = ["lòng tin", "quê hương", "tự do", "ký ức đã mất", "tương lai nhân loại",
          "một lời hứa", "danh dự gia đình", "tình yêu đầu đời"]
TONES = ["lãng mạn", "căng thẳng", "kỳ ảo", "u tối", "ấm áp", "gay cấn", "hài hước"]

TAGLINES = [
    "Sự thật luôn có cái giá của nó.",
    "Một hành trình không lối quay về.",
    "Đôi khi, dũng cảm là điều duy nhất ta có.",
    "Mọi bí mật rồi sẽ lộ sáng.",
    "Khi tất cả sụp đổ, tình yêu vẫn còn.",
    "Cuộc chiến cuối cùng bắt đầu.",
    "Không ai thoát khỏi quá khứ.",
]


def make_title(genres: list[str], used: set[str]) -> str:
    primary = genres[0]
    heads, tails = TITLE_PARTS[primary]
    for _ in range(40):
        title = f"{RNG.choice(heads)} {RNG.choice(tails)}"
        if title not in used:
            used.add(title)
            return title
    # fallback đảm bảo duy nhất
    title = f"{RNG.choice(heads)} {RNG.choice(tails)} {len(used)}"
    used.add(title)
    return title


def generate_movies() -> list[dict]:
    movies: list[dict] = []
    used_titles: set[str] = set()
    for movie_id in range(1, NUM_MOVIES + 1):
        n_genres = RNG.choices([1, 2, 3], weights=[3, 5, 2])[0]
        genres = RNG.sample(GENRES, n_genres)
        title = make_title(genres, used_titles)
        year = RNG.randint(1992, 2024)
        runtime = RNG.randint(82, 168)
        maturity = RNG.choices(MATURITY, weights=[1, 3, 4, 3, 2])[0]
        role = RNG.choice(ROLES)
        stake = RNG.choice(STAKES)
        tone = RNG.choice(TONES)
        overview = RNG.choice(OVERVIEW_TEMPLATES).format(role=role, stake=stake, tone=tone)
        movies.append(
            {
                "movieId": movie_id,
                "title": f"{title} ({year})",
                "genres": "|".join(genres),
                "year": year,
                "runtime": runtime,
                "maturity": maturity,
                "tagline": RNG.choice(TAGLINES),
                "overview": overview,
            }
        )
    return movies


def genre_vector(genres: list[str]) -> dict[str, float]:
    return {g: 1.0 for g in genres}


def generate_ratings(movies: list[dict]) -> list[dict]:
    """Sinh ratings từ sở thích tiềm ẩn: rating ~ affinity(user, movie) + chất lượng phim."""
    movie_genres = {m["movieId"]: m["genres"].split("|") for m in movies}
    # "chất lượng" nội tại của mỗi phim (một số phim hay với mọi người -> popularity có ý nghĩa)
    movie_quality = {m["movieId"]: RNG.gauss(0.0, 0.6) for m in movies}
    # độ phổ biến (số người tiếp cận) lệch theo phân phối đuôi dài
    movie_exposure = {m["movieId"]: RNG.random() ** 2 for m in movies}

    ratings: list[dict] = []
    for user_id in range(1, NUM_USERS + 1):
        # mỗi user thích 2-4 thể loại
        fav = RNG.sample(GENRES, RNG.randint(2, 4))
        pref = {g: RNG.uniform(0.6, 1.0) for g in fav}
        n_ratings = RNG.choices([8, 15, 25, 40, 60], weights=[3, 5, 5, 4, 2])[0]

        # chọn phim theo exposure + chút thiên lệch về thể loại yêu thích
        candidates = list(movie_genres.keys())
        weights = []
        for mid in candidates:
            g = movie_genres[mid]
            aff = sum(pref.get(x, 0.0) for x in g) / len(g)
            weights.append(movie_exposure[mid] + 0.8 * aff + 0.05)
        chosen = _weighted_sample(candidates, weights, min(n_ratings, len(candidates)))

        for mid in chosen:
            g = movie_genres[mid]
            aff = sum(pref.get(x, 0.0) for x in g) / len(g)  # 0..1
            base = 2.6 + 2.2 * aff + 0.6 * movie_quality[mid] + RNG.gauss(0, 0.45)
            rating = max(0.5, min(5.0, round(base * 2) / 2))
            ratings.append({"userId": user_id, "movieId": mid, "rating": rating})
    return ratings


def _weighted_sample(items: list[int], weights: list[float], k: int) -> list[int]:
    pool = list(zip(items, weights))
    chosen: list[int] = []
    for _ in range(k):
        total = sum(w for _, w in pool)
        if total <= 0 or not pool:
            break
        r = RNG.uniform(0, total)
        acc = 0.0
        for idx, (item, w) in enumerate(pool):
            acc += w
            if acc >= r:
                chosen.append(item)
                pool.pop(idx)
                break
    return chosen


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    movies = generate_movies()
    ratings = generate_ratings(movies)

    with open(DATA_DIR / "movies.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["movieId", "title", "genres", "year", "runtime", "maturity", "tagline", "overview"]
        )
        writer.writeheader()
        writer.writerows(movies)

    with open(DATA_DIR / "ratings.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["userId", "movieId", "rating"])
        writer.writeheader()
        writer.writerows(ratings)

    print(f"✓ {len(movies)} phim  →  {DATA_DIR / 'movies.csv'}")
    print(f"✓ {len(ratings)} ratings  →  {DATA_DIR / 'ratings.csv'}")
    warm = sum(1 for u in range(1, NUM_USERS + 1)
               if sum(1 for r in ratings if r['userId'] == u) >= 20)
    print(f"✓ ~{warm} người dùng warm (>=20 tương tác)")


if __name__ == "__main__":
    main()
