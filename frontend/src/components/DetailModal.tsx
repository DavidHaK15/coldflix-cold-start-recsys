import { useEffect, useState } from "react";
import { Play, Plus, Star, X } from "lucide-react";
import { api, type Movie } from "../api/client";
import { useUI } from "../state/ui";
import { useProfile } from "../state/profile";
import { Poster } from "./Poster";
import { MovieCard } from "./MovieCard";

export function DetailModal() {
  const { selectedMovie, closeMovie, openMovie } = useUI();
  const { ratings, rate } = useProfile();
  const [similar, setSimilar] = useState<Movie[]>([]);

  useEffect(() => {
    if (!selectedMovie) return;
    setSimilar([]);
    api.getSimilar(selectedMovie.movie_id).then(setSimilar).catch(() => setSimilar([]));
  }, [selectedMovie]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") closeMovie();
    }
    if (selectedMovie) {
      document.addEventListener("keydown", onKey);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [selectedMovie, closeMovie]);

  if (!selectedMovie) return null;
  const movie = selectedMovie;
  const userRating = ratings[movie.movie_id] ?? 0;
  const cleanTitle = movie.title.replace(/\s*\(\d{4}\)\s*$/, "");

  return (
    <div className="modal-backdrop" onClick={closeMovie}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={movie.title}>
        <button className="modal-close" onClick={closeMovie} aria-label="Đóng">
          <X size={20} />
        </button>
        <div className="modal-hero">
          <Poster movie={movie} className="modal-poster" />
          <div className="modal-hero-scrim" />
          <div className="modal-hero-body">
            <h2>{cleanTitle}</h2>
            <p className="modal-tagline">{movie.tagline}</p>
            <div className="modal-actions">
              <button className="btn btn--play">
                <Play size={18} fill="currentColor" /> Phát
              </button>
              <button className="btn btn--circle" aria-label="Thêm vào danh sách">
                <Plus size={18} />
              </button>
            </div>
          </div>
        </div>

        <div className="modal-content">
          <div className="modal-meta">
            <span className="match-strong" style={{ color: "#5ad17a" }}>
              {Math.round(movie.avg_rating * 20)}% phù hợp
            </span>
            <span>{movie.year}</span>
            <span className="maturity-tag">{movie.maturity || "PG"}</span>
            <span>{movie.runtime} phút</span>
            <span className="rating-inline">
              <Star size={13} fill="currentColor" /> {movie.avg_rating.toFixed(1)} ({movie.rating_count})
            </span>
          </div>
          <p className="modal-overview">{movie.overview}</p>
          <p className="modal-genres">
            <span>Thể loại: </span>
            {movie.genres.join(", ")}
          </p>

          <div className="rate-box">
            <span>Đánh giá của bạn (huấn luyện gợi ý):</span>
            <div className="rate-stars">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  className={`star ${value <= userRating ? "filled" : ""}`}
                  onClick={() => rate(movie.movie_id, value)}
                  aria-label={`Chấm ${value} sao`}
                >
                  <Star size={26} fill={value <= userRating ? "currentColor" : "none"} />
                </button>
              ))}
              {userRating > 0 && <span className="rate-value">{userRating}/5 ★</span>}
            </div>
          </div>

          {similar.length > 0 && (
            <div className="modal-similar">
              <h3>Phim tương tự (Item-based CF)</h3>
              <div className="modal-similar-grid">
                {similar.slice(0, 8).map((item) => (
                  <div key={item.movie_id} onClick={() => openMovie(item)}>
                    <MovieCard movie={item} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
