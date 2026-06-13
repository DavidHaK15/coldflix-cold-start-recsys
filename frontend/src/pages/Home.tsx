import { useEffect, useMemo, useState } from "react";
import { api, type Movie, type Recommendation } from "../api/client";
import { useProfile } from "../state/profile";
import { Hero } from "../components/Hero";
import { Row } from "../components/Row";

const STRATEGY_REASON: Record<string, string> = {
  popularity: "Vì bạn là người dùng mới — phim phổ biến nhất",
  content: "Dựa trên thể loại bạn yêu thích (Content-based)",
  onboarding: "Dựa trên các phim bạn vừa chấm điểm (Onboarding + Item-CF)",
  dropout: "Gợi ý lai content + collaborative (DropoutNet)",
  item_cf: "Dựa trên lịch sử xem của bạn (Item-based CF)",
};

interface Props {
  catalog: Movie[];
  genres: string[];
}

export function Home({ catalog, genres }: Props) {
  const { strategy, genres: favGenres, ratings, simulatedUserId } = useProfile();
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [becauseYouWatched, setBecauseYouWatched] = useState<{ seed: Movie; items: Movie[] } | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const result = await api.recommend({
          strategy,
          top_n: 18,
          user_id: simulatedUserId,
          preferred_genres: favGenres,
          onboarding_ratings: ratings,
        });
        if (!cancelled) setRecs(result);
      } catch {
        if (!cancelled) setRecs([]);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [strategy, favGenres, ratings, simulatedUserId]);

  useEffect(() => {
    const ratedIds = Object.keys(ratings).map(Number);
    if (ratedIds.length === 0) {
      setBecauseYouWatched(null);
      return;
    }
    const topRatedId = ratedIds.sort((a, b) => (ratings[b] ?? 0) - (ratings[a] ?? 0))[0];
    const seed = catalog.find((m) => m.movie_id === topRatedId);
    if (!seed) return;
    api.getSimilar(topRatedId).then((items) => setBecauseYouWatched({ seed, items })).catch(() => {});
  }, [ratings, catalog]);

  const trending = useMemo(
    () => [...catalog].sort((a, b) => b.popularity_score - a.popularity_score).slice(0, 18),
    [catalog],
  );

  const topRated = useMemo(
    () => [...catalog].filter((m) => m.rating_count >= 8).sort((a, b) => b.avg_rating - a.avg_rating).slice(0, 18),
    [catalog],
  );

  const genreRows = useMemo(() => {
    const ordered = [...favGenres, ...genres.filter((g) => !favGenres.includes(g))];
    return ordered
      .map((genre) => ({
        genre,
        movies: catalog
          .filter((m) => m.genres.includes(genre))
          .sort((a, b) => b.popularity_score - a.popularity_score)
          .slice(0, 16),
      }))
      .filter((row) => row.movies.length >= 4)
      .slice(0, 6);
  }, [catalog, genres, favGenres]);

  const heroMovie = recs[0] ?? trending[0];

  return (
    <div className="home">
      {heroMovie && <Hero movie={heroMovie} reason={STRATEGY_REASON[strategy]} />}

      <div className="rows">
        {recs.length > 0 && (
          <Row
            title="Gợi ý cho bạn"
            subtitle={STRATEGY_REASON[strategy]}
            movies={recs}
            highlight
          />
        )}

        {becauseYouWatched && becauseYouWatched.items.length > 0 && (
          <Row
            title={`Vì bạn đã xem “${becauseYouWatched.seed.title.replace(/\s*\(\d{4}\)\s*$/, "")}”`}
            subtitle="Item-based Collaborative Filtering"
            movies={becauseYouWatched.items}
          />
        )}

        <Row title="Thịnh hành" subtitle="Popularity baseline — log(|U_i|+1)" movies={trending} />
        <Row title="Đánh giá cao nhất" movies={topRated} />

        {genreRows.map((row) => (
          <Row key={row.genre} title={row.genre} movies={row.movies} />
        ))}
      </div>
    </div>
  );
}
