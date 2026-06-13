import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { MovieCard } from "./MovieCard";
import type { Movie, Recommendation } from "../api/client";

interface Props {
  title: string;
  subtitle?: string;
  movies: (Movie | Recommendation)[];
  badge?: string;
  highlight?: boolean;
}

export function Row({ title, subtitle, movies, badge, highlight }: Props) {
  const trackRef = useRef<HTMLDivElement>(null);

  function scroll(direction: 1 | -1) {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({ left: direction * track.clientWidth * 0.85, behavior: "smooth" });
  }

  if (movies.length === 0) return null;

  return (
    <section className={`row ${highlight ? "row--highlight" : ""}`}>
      <div className="row-head">
        <h2>{title}</h2>
        {subtitle && <span className="row-subtitle">{subtitle}</span>}
      </div>
      <div className="row-viewport">
        <button className="row-arrow row-arrow--left" onClick={() => scroll(-1)} aria-label="Cuộn trái">
          <ChevronLeft size={28} />
        </button>
        <div className="row-track" ref={trackRef}>
          {movies.map((movie) => (
            <MovieCard key={movie.movie_id} movie={movie} badge={badge} />
          ))}
        </div>
        <button className="row-arrow row-arrow--right" onClick={() => scroll(1)} aria-label="Cuộn phải">
          <ChevronRight size={28} />
        </button>
      </div>
    </section>
  );
}
