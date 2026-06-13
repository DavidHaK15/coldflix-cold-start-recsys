import { useEffect, useState } from "react";
import { Check, Sparkles, Star } from "lucide-react";
import { api, type Movie } from "../api/client";
import { useProfile } from "../state/profile";
import { Poster } from "./Poster";

interface Props {
  genres: string[];
  onClose: () => void;
}

export function OnboardingModal({ genres, onClose }: Props) {
  const { genres: chosenGenres, ratings, toggleGenre, rate, completeOnboarding } = useProfile();
  const [step, setStep] = useState(0);
  const [items, setItems] = useState<Movie[]>([]);

  useEffect(() => {
    api.getOnboardingItems().then(setItems).catch(() => setItems([]));
  }, []);

  function finish() {
    completeOnboarding();
    onClose();
  }

  const ratedCount = Object.keys(ratings).length;

  return (
    <div className="modal-backdrop">
      <div className="onboarding" role="dialog" aria-label="Thiết lập sở thích">
        <div className="onboarding-head">
          <Sparkles size={22} className="onboarding-spark" />
          <h2>Chào mừng tới ColdFlix</h2>
          <p>
            Bạn là <b>người dùng mới</b> — đây chính là bài toán <b>cold-start</b>. Hãy cho chúng tôi
            biết gu của bạn để khởi tạo gợi ý ngay từ con số 0.
          </p>
        </div>

        <div className="onboarding-steps">
          <span className={step === 0 ? "active" : ""}>1 · Thể loại yêu thích</span>
          <span className={step === 1 ? "active" : ""}>2 · Chấm vài phim</span>
        </div>

        {step === 0 ? (
          <>
            <div className="genre-grid">
              {genres.map((genre) => (
                <button
                  key={genre}
                  className={`chip ${chosenGenres.includes(genre) ? "selected" : ""}`}
                  onClick={() => toggleGenre(genre)}
                >
                  {chosenGenres.includes(genre) && <Check size={14} />} {genre}
                </button>
              ))}
            </div>
            <div className="onboarding-foot">
              <button className="btn btn--ghost" onClick={finish}>
                Bỏ qua
              </button>
              <button
                className="btn btn--play"
                disabled={chosenGenres.length === 0}
                onClick={() => setStep(1)}
              >
                Tiếp tục ({chosenGenres.length})
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="onboarding-hint">
              Chấm điểm vài phim đa dạng — đây là bước <b>active learning / onboarding</b> để hệ thống
              hiểu bạn nhanh hơn.
            </p>
            <div className="onboarding-movies">
              {items.map((movie) => (
                <div className="onboarding-movie" key={movie.movie_id}>
                  <Poster movie={movie} className="onboarding-poster" />
                  <div className="onboarding-stars">
                    {[1, 2, 3, 4, 5].map((value) => (
                      <button
                        key={value}
                        className={`star ${value <= (ratings[movie.movie_id] ?? 0) ? "filled" : ""}`}
                        onClick={() => rate(movie.movie_id, value)}
                        aria-label={`${movie.title} ${value} sao`}
                      >
                        <Star size={16} fill={value <= (ratings[movie.movie_id] ?? 0) ? "currentColor" : "none"} />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="onboarding-foot">
              <button className="btn btn--ghost" onClick={() => setStep(0)}>
                Quay lại
              </button>
              <button className="btn btn--play" onClick={finish}>
                Vào ColdFlix {ratedCount > 0 ? `(${ratedCount} phim)` : ""}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
