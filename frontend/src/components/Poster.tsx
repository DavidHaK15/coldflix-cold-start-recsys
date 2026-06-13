import { useState } from "react";
import { posterStyle } from "../lib/poster";
import type { Movie } from "../api/client";

interface Props {
  movie: Movie;
  className?: string;
}

/** Poster phim: ưu tiên ảnh thật (poster_url); nếu thiếu/lỗi → fallback gradient CSS. */
export function Poster({ movie, className }: Props) {
  const { background, accent, initials } = posterStyle(movie.title, movie.genres);
  const cleanTitle = movie.title.replace(/\s*\(\d{4}\)\s*$/, "");
  const [failed, setFailed] = useState(false);
  const showImage = Boolean(movie.poster_url) && !failed;

  return (
    <div className={`poster ${className ?? ""}`} style={{ background }} aria-hidden="true">
      {showImage ? (
        <img
          className="poster-img"
          src={movie.poster_url}
          alt={cleanTitle}
          loading="lazy"
          onError={() => setFailed(true)}
        />
      ) : (
        <>
          <span className="poster-initials" style={{ color: accent }}>
            {initials}
          </span>
          <div className="poster-content">
            <span className="poster-genre" style={{ color: accent }}>
              {movie.genres[0] ?? "Phim"}
            </span>
            <span className="poster-title">{cleanTitle}</span>
            <span className="poster-year">{movie.year || ""}</span>
          </div>
        </>
      )}
    </div>
  );
}
