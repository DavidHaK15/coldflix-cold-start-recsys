import { Info, Play } from "lucide-react";
import { posterStyle } from "../lib/poster";
import { useUI } from "../state/ui";
import type { Movie } from "../api/client";

interface Props {
  movie: Movie;
  reason?: string;
}

export function Hero({ movie, reason }: Props) {
  const { openMovie } = useUI();
  const { background, accent } = posterStyle(movie.title, movie.genres);
  const cleanTitle = movie.title.replace(/\s*\(\d{4}\)\s*$/, "");
  const heroStyle = movie.poster_url
    ? { backgroundImage: `url(${movie.poster_url})`, backgroundSize: "cover", backgroundPosition: "center 20%" }
    : { background };

  return (
    <section className="hero" style={heroStyle}>
      <div className="hero-scrim" />
      <div className="hero-inner">
        {reason && (
          <span className="hero-reason" style={{ color: accent }}>
            {reason}
          </span>
        )}
        <h1 className="hero-title">{cleanTitle}</h1>
        <div className="hero-meta">
          <span className="match-strong" style={{ color: "#5ad17a" }}>
            {Math.round(movie.avg_rating * 20)}% phù hợp
          </span>
          <span>{movie.year}</span>
          <span className="maturity-tag">{movie.maturity || "PG"}</span>
          <span>{movie.runtime ? `${movie.runtime} phút` : ""}</span>
        </div>
        <p className="hero-overview">{movie.overview}</p>
        <div className="hero-actions">
          <button className="btn btn--play" onClick={() => openMovie(movie)}>
            <Play size={20} fill="currentColor" /> Phát
          </button>
          <button className="btn btn--ghost" onClick={() => openMovie(movie)}>
            <Info size={20} /> Thông tin
          </button>
        </div>
        <div className="hero-genres">{movie.genres.join(" • ")}</div>
      </div>
    </section>
  );
}
