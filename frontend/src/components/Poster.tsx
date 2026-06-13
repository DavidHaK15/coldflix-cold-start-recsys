import { posterStyle } from "../lib/poster";
import type { Movie } from "../api/client";

interface Props {
  movie: Movie;
  className?: string;
}

/** Poster sinh bằng CSS gradient — màu ổn định theo tên + thể loại của phim. */
export function Poster({ movie, className }: Props) {
  const { background, accent, initials } = posterStyle(movie.title, movie.genres);
  const cleanTitle = movie.title.replace(/\s*\(\d{4}\)\s*$/, "");

  return (
    <div className={`poster ${className ?? ""}`} style={{ background }} aria-hidden="true">
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
    </div>
  );
}
