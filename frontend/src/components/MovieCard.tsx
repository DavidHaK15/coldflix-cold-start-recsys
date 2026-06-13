import { Info, Play, Star } from "lucide-react";
import { Poster } from "./Poster";
import { useUI } from "../state/ui";
import { matchScore } from "../lib/poster";
import type { Movie, Recommendation } from "../api/client";

interface Props {
  movie: Movie | Recommendation;
  badge?: string;
}

export function MovieCard({ movie, badge }: Props) {
  const { openMovie } = useUI();
  const score = matchScore(movie.title);

  return (
    <button className="movie-card" onClick={() => openMovie(movie)} aria-label={movie.title}>
      <Poster movie={movie} />
      {badge && <span className="card-badge">{badge}</span>}
      <div className="card-hover">
        <div className="card-hover-actions">
          <span className="icon-btn icon-btn--play" aria-hidden="true">
            <Play size={16} fill="currentColor" />
          </span>
          <span className="icon-btn" aria-hidden="true">
            <Info size={16} />
          </span>
          <span className="match">{score}% phù hợp</span>
        </div>
        <div className="card-hover-title">{movie.title.replace(/\s*\(\d{4}\)\s*$/, "")}</div>
        <div className="card-hover-meta">
          <span className="maturity-tag">{movie.maturity || "PG"}</span>
          <span>{movie.runtime ? `${movie.runtime} phút` : ""}</span>
          {movie.avg_rating > 0 && (
            <span className="rating-inline">
              <Star size={12} fill="currentColor" /> {movie.avg_rating.toFixed(1)}
            </span>
          )}
        </div>
        <div className="card-hover-genres">{movie.genres.slice(0, 3).join(" • ")}</div>
      </div>
    </button>
  );
}
