#!/usr/bin/env python3
"""Tạo catalog từ PHIM THẬT (nổi tiếng) + poster THẬT lấy keyless từ Wikipedia.

- Poster & overview: Wikipedia REST API (ảnh infobox = poster rạp), không cần API key.
- Genres/year: gán sẵn trong danh sách curate (kiểm soát để CF/content chạy tốt).
- Ratings: sinh từ sở thích tiềm ẩn theo thể loại (để cá nhân hoá có ý nghĩa).

Chạy:  python scripts/generate_real.py
Xuất:  data/sample/movies.csv (có cột poster_url), data/sample/ratings.csv
"""
from __future__ import annotations

import csv
import json
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sample"
WIKI = "https://en.wikipedia.org/api/rest_v1/page/summary/"
UA = "ColdFlix-Coursework/1.0 (academic demo; contact: student@example.com)"

SEED = 7
NUM_USERS = 500
RNG = random.Random(SEED)

# (Tựa hiển thị, trang Wikipedia, [thể loại], nhãn tuổi)
FILMS: list[tuple[str, str, list[str], str]] = [
    ("The Matrix (1999)", "The_Matrix", ["Sci-Fi", "Action"], "R"),
    ("Inception (2010)", "Inception", ["Sci-Fi", "Thriller", "Action"], "PG-13"),
    ("Interstellar (2014)", "Interstellar_(film)", ["Sci-Fi", "Drama", "Adventure"], "PG-13"),
    ("The Dark Knight (2008)", "The_Dark_Knight", ["Action", "Crime", "Thriller"], "PG-13"),
    ("Avatar (2009)", "Avatar_(2009_film)", ["Sci-Fi", "Adventure", "Action"], "PG-13"),
    ("Mad Max: Fury Road (2015)", "Mad_Max:_Fury_Road", ["Action", "Adventure", "Sci-Fi"], "R"),
    ("Gladiator (2000)", "Gladiator_(2000_film)", ["Action", "Drama", "Adventure"], "R"),
    ("Jurassic Park (1993)", "Jurassic_Park_(film)", ["Adventure", "Sci-Fi"], "PG-13"),
    ("Top Gun: Maverick (2022)", "Top_Gun:_Maverick", ["Action", "Drama"], "PG-13"),
    ("Dune (2021)", "Dune_(2021_film)", ["Sci-Fi", "Adventure"], "PG-13"),
    ("Blade Runner 2049 (2017)", "Blade_Runner_2049", ["Sci-Fi", "Drama", "Mystery"], "R"),
    ("Guardians of the Galaxy (2014)", "Guardians_of_the_Galaxy_(film)", ["Action", "Adventure", "Comedy"], "PG-13"),
    ("Avengers: Endgame (2019)", "Avengers:_Endgame", ["Action", "Adventure", "Sci-Fi"], "PG-13"),
    ("Star Wars (1977)", "Star_Wars_(film)", ["Sci-Fi", "Adventure", "Fantasy"], "PG"),
    ("The Fellowship of the Ring (2001)", "The_Lord_of_the_Rings:_The_Fellowship_of_the_Ring", ["Fantasy", "Adventure"], "PG-13"),
    ("Into the Spider-Verse (2018)", "Spider-Man:_Into_the_Spider-Verse", ["Animation", "Action", "Adventure"], "PG"),
    ("John Wick (2014)", "John_Wick", ["Action", "Thriller", "Crime"], "R"),
    ("Terminator 2 (1991)", "Terminator_2:_Judgment_Day", ["Action", "Sci-Fi"], "R"),
    ("Edge of Tomorrow (2014)", "Edge_of_Tomorrow", ["Sci-Fi", "Action"], "PG-13"),
    ("Mission: Impossible – Fallout (2018)", "Mission:_Impossible_–_Fallout", ["Action", "Thriller", "Adventure"], "PG-13"),
    ("Forrest Gump (1994)", "Forrest_Gump", ["Drama", "Romance"], "PG-13"),
    ("The Shawshank Redemption (1994)", "The_Shawshank_Redemption", ["Drama", "Crime"], "R"),
    ("Fight Club (1999)", "Fight_Club", ["Drama", "Thriller"], "R"),
    ("The Godfather (1972)", "The_Godfather", ["Crime", "Drama"], "R"),
    ("Parasite (2019)", "Parasite_(2019_film)", ["Drama", "Thriller", "Comedy"], "R"),
    ("Whiplash (2014)", "Whiplash_(2014_film)", ["Drama", "Musical"], "R"),
    ("The Social Network (2010)", "The_Social_Network", ["Drama"], "PG-13"),
    ("12 Years a Slave (2013)", "12_Years_a_Slave_(film)", ["Drama"], "R"),
    ("La La Land (2016)", "La_La_Land", ["Musical", "Romance", "Drama"], "PG-13"),
    ("Joker (2019)", "Joker_(2019_film)", ["Drama", "Crime", "Thriller"], "R"),
    ("Oppenheimer (2023)", "Oppenheimer_(film)", ["Drama"], "R"),
    ("Schindler's List (1993)", "Schindler's_List", ["Drama"], "R"),
    ("The Pursuit of Happyness (2006)", "The_Pursuit_of_Happyness", ["Drama"], "PG-13"),
    ("Marriage Story (2019)", "Marriage_Story", ["Drama", "Romance"], "R"),
    ("The Grand Budapest Hotel (2014)", "The_Grand_Budapest_Hotel", ["Comedy", "Adventure"], "R"),
    ("Superbad (2007)", "Superbad_(film)", ["Comedy"], "R"),
    ("The Hangover (2009)", "The_Hangover", ["Comedy"], "R"),
    ("Knives Out (2019)", "Knives_Out", ["Mystery", "Comedy", "Crime"], "PG-13"),
    ("Jojo Rabbit (2019)", "Jojo_Rabbit", ["Comedy", "Drama"], "PG-13"),
    ("Deadpool (2016)", "Deadpool_(film)", ["Action", "Comedy"], "R"),
    ("Pulp Fiction (1994)", "Pulp_Fiction", ["Crime", "Drama"], "R"),
    ("Se7en (1995)", "Seven_(1995_film)", ["Crime", "Thriller", "Mystery"], "R"),
    ("The Departed (2006)", "The_Departed", ["Crime", "Thriller", "Drama"], "R"),
    ("Gone Girl (2014)", "Gone_Girl_(film)", ["Thriller", "Mystery", "Drama"], "R"),
    ("No Country for Old Men (2007)", "No_Country_for_Old_Men_(film)", ["Crime", "Thriller", "Drama"], "R"),
    ("Heat (1995)", "Heat_(1995_film)", ["Crime", "Action", "Thriller"], "R"),
    ("Prisoners (2013)", "Prisoners_(2013_film)", ["Thriller", "Mystery", "Crime"], "R"),
    ("Zodiac (2007)", "Zodiac_(film)", ["Crime", "Mystery", "Thriller"], "R"),
    ("Get Out (2017)", "Get_Out", ["Horror", "Thriller", "Mystery"], "R"),
    ("A Quiet Place (2018)", "A_Quiet_Place", ["Horror", "Thriller", "Sci-Fi"], "PG-13"),
    ("Hereditary (2018)", "Hereditary_(film)", ["Horror", "Drama", "Mystery"], "R"),
    ("The Conjuring (2013)", "The_Conjuring", ["Horror", "Thriller"], "R"),
    ("It (2017)", "It_(2017_film)", ["Horror"], "R"),
    ("The Shining (1980)", "The_Shining_(film)", ["Horror", "Drama"], "R"),
    ("Toy Story (1995)", "Toy_Story", ["Animation", "Family", "Comedy"], "G"),
    ("Spirited Away (2001)", "Spirited_Away", ["Animation", "Fantasy", "Family"], "PG"),
    ("Coco (2017)", "Coco_(2017_film)", ["Animation", "Family", "Musical"], "PG"),
    ("Up (2009)", "Up_(2009_film)", ["Animation", "Family", "Adventure"], "PG"),
    ("Inside Out (2015)", "Inside_Out_(2015_film)", ["Animation", "Family", "Comedy"], "PG"),
    ("The Lion King (1994)", "The_Lion_King", ["Animation", "Family", "Drama"], "G"),
    ("Frozen (2013)", "Frozen_(2013_film)", ["Animation", "Family", "Musical"], "PG"),
    ("Shrek (2001)", "Shrek", ["Animation", "Comedy", "Family"], "PG"),
    ("WALL-E (2008)", "WALL-E", ["Animation", "Family", "Sci-Fi"], "G"),
    ("Finding Nemo (2003)", "Finding_Nemo", ["Animation", "Family", "Adventure"], "G"),
    ("Ratatouille (2007)", "Ratatouille_(film)", ["Animation", "Family", "Comedy"], "G"),
    ("Titanic (1997)", "Titanic_(1997_film)", ["Romance", "Drama"], "PG-13"),
    ("The Notebook (2004)", "The_Notebook", ["Romance", "Drama"], "PG-13"),
    ("Pride & Prejudice (2005)", "Pride_&_Prejudice_(2005_film)", ["Romance", "Drama"], "PG"),
    ("Call Me by Your Name (2017)", "Call_Me_by_Your_Name_(film)", ["Romance", "Drama"], "R"),
    ("Eternal Sunshine (2004)", "Eternal_Sunshine_of_the_Spotless_Mind", ["Romance", "Sci-Fi", "Drama"], "R"),
    ("Harry Potter (2001)", "Harry_Potter_and_the_Philosopher's_Stone_(film)", ["Fantasy", "Adventure", "Family"], "PG"),
    ("Pan's Labyrinth (2006)", "Pan's_Labyrinth", ["Fantasy", "Drama"], "R"),
    ("The Shape of Water (2017)", "The_Shape_of_Water", ["Fantasy", "Romance", "Drama"], "R"),
    ("Shutter Island (2010)", "Shutter_Island_(film)", ["Mystery", "Thriller"], "R"),
    ("Memento (2000)", "Memento_(film)", ["Mystery", "Thriller"], "R"),
    ("Tenet (2020)", "Tenet_(film)", ["Sci-Fi", "Action", "Thriller"], "PG-13"),
]


def fetch_wiki(title: str) -> tuple[str, str]:
    """Trả (poster_url, overview) từ Wikipedia. Rỗng nếu lỗi."""
    url = WIKI + urllib.parse.quote(title, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! {title}: {exc}")
        return "", ""
    img = (data.get("originalimage") or data.get("thumbnail") or {}).get("source", "")
    overview = (data.get("extract") or "").strip()
    return img, overview


def parse_year(display: str) -> int:
    import re
    m = re.search(r"\((\d{4})\)", display)
    return int(m.group(1)) if m else 0


def build_movies() -> list[dict]:
    movies: list[dict] = []
    for idx, (display, wiki, genres, maturity) in enumerate(FILMS, start=1):
        poster, overview = fetch_wiki(wiki)
        if not overview:
            overview = f"{display.split(' (')[0]} — một tác phẩm {genres[0].lower()} nổi bật."
        movies.append({
            "movieId": idx,
            "title": display,
            "genres": "|".join(genres),
            "year": parse_year(display),
            "runtime": RNG.randint(95, 175),
            "maturity": maturity,
            "tagline": "",
            "overview": overview[:400],
            "poster_url": poster,
        })
        status = "✓" if poster else "—(no poster)"
        print(f"  {status} {display}")
        time.sleep(0.15)
    return movies


def generate_ratings(movies: list[dict]) -> list[dict]:
    GENRES = sorted({g for m in movies for g in m["genres"].split("|")})
    movie_genres = {m["movieId"]: m["genres"].split("|") for m in movies}
    quality = {m["movieId"]: RNG.gauss(0.3, 0.5) for m in movies}  # phim nổi tiếng hơi lệch dương
    exposure = {m["movieId"]: RNG.random() ** 1.5 + 0.2 for m in movies}
    ratings: list[dict] = []
    for user_id in range(1, NUM_USERS + 1):
        fav = RNG.sample(GENRES, RNG.randint(2, 4))
        pref = {g: RNG.uniform(0.6, 1.0) for g in fav}
        n = RNG.choices([8, 15, 25, 40, 55], weights=[3, 5, 5, 4, 2])[0]
        ids = list(movie_genres.keys())
        weights = []
        for mid in ids:
            g = movie_genres[mid]
            aff = sum(pref.get(x, 0.0) for x in g) / len(g)
            weights.append(exposure[mid] + 0.8 * aff + 0.05)
        chosen = _wsample(ids, weights, min(n, len(ids)))
        for mid in chosen:
            g = movie_genres[mid]
            aff = sum(pref.get(x, 0.0) for x in g) / len(g)
            base = 2.6 + 2.2 * aff + 0.6 * quality[mid] + RNG.gauss(0, 0.45)
            ratings.append({"userId": user_id, "movieId": mid, "rating": max(0.5, min(5.0, round(base * 2) / 2))})
    return ratings


def _wsample(items, weights, k):
    pool = list(zip(items, weights))
    out = []
    for _ in range(k):
        total = sum(w for _, w in pool)
        if total <= 0 or not pool:
            break
        r = RNG.uniform(0, total)
        acc = 0.0
        for i, (it, w) in enumerate(pool):
            acc += w
            if acc >= r:
                out.append(it)
                pool.pop(i)
                break
    return out


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Lấy poster + overview thật từ Wikipedia…")
    movies = build_movies()
    ratings = generate_ratings(movies)
    with open(DATA_DIR / "movies.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["movieId", "title", "genres", "year", "runtime", "maturity", "tagline", "overview", "poster_url"])
        w.writeheader(); w.writerows(movies)
    with open(DATA_DIR / "ratings.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["userId", "movieId", "rating"])
        w.writeheader(); w.writerows(ratings)
    have = sum(1 for m in movies if m["poster_url"])
    print(f"\n✓ {len(movies)} phim ({have} có poster) · {len(ratings)} ratings")


if __name__ == "__main__":
    main()
