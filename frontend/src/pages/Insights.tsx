import { useEffect, useState } from "react";
import { api, type DatasetStats, type LearningCurveResponse } from "../api/client";
import { LearningCurveChart } from "../components/LearningCurveChart";

interface MethodRow {
  method: string;
  cold: string;
  idea: string;
  pros: string;
  cons: string;
  ref: string;
}

const METHODS: MethodRow[] = [
  {
    method: "Popularity-based",
    cold: "New User",
    idea: "Gợi ý sản phẩm phổ biến nhất cho mọi người dùng mới.",
    pros: "Đơn giản, mạnh khi chưa có dữ liệu.",
    cons: "Không cá nhân hoá, hiệu ứng rich-get-richer.",
    ref: "Baseline phổ biến",
  },
  {
    method: "Content-based Bootstrapping",
    cold: "New User & New Item",
    idea: "Dựa trên thuộc tính (thể loại) + hồ sơ sở thích, TF-IDF + cosine.",
    pros: "Xử lý được cả item mới; không cần lịch sử cộng đồng.",
    cons: "Phụ thuộc chất lượng metadata; thiếu đa dạng.",
    ref: "Schein et al., 2002",
  },
  {
    method: "Onboarding / Active Learning",
    cold: "New User",
    idea: "Hỏi người dùng vài đánh giá ban đầu, chọn item đa dạng để khai thác nhanh.",
    pros: "Thu thập tín hiệu nhanh, nền tảng cho CF.",
    cons: "Tăng ma sát onboarding; chọn item hỏi là bài toán riêng.",
    ref: "Rashid et al., 2002",
  },
  {
    method: "DropoutNet (hybrid)",
    cold: "New User & New Item",
    idea: "Học biểu diễn lai content + collaborative, dropout để mô phỏng cold-start.",
    pros: "Chuyển tiếp mượt cold→warm; tốt nhất khi đủ tương tác.",
    cons: "Phức tạp, cần huấn luyện; ở đây đơn giản hoá.",
    ref: "Volkovs et al., 2017",
  },
  {
    method: "Meta-learning (MeLU)",
    cold: "New User",
    idea: "Học cách thích nghi nhanh với người dùng mới chỉ từ vài mẫu (few-shot).",
    pros: "Thích nghi nhanh, ít dữ liệu.",
    cons: "Khó huấn luyện, chi phí tính toán cao.",
    ref: "Lee et al., 2019",
  },
];

interface Props {
  stats: DatasetStats | null;
}

export function Insights({ stats }: Props) {
  const [curve, setCurve] = useState<LearningCurveResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getLearningCurve(60)
      .then(setCurve)
      .catch((e) => setError(e instanceof Error ? e.message : "Lỗi tải dữ liệu"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="insights">
      <header className="insights-head">
        <span className="badge">Chủ đề 7 · Nghiên cứu</span>
        <h1>Đánh giá &amp; So sánh các chiến lược Cold-Start</h1>
        <p>
          Phần này định lượng hiệu quả của từng chiến lược qua mô phỏng cold-start trên tập dữ liệu,
          và đặt chúng cạnh các hướng nghiên cứu tiêu biểu trong tài liệu.
        </p>
      </header>

      {stats && (
        <section className="stats-grid">
          <Stat label="Người dùng" value={stats.num_users} />
          <Stat label="Phim" value={stats.num_movies} />
          <Stat label="Lượt đánh giá" value={stats.num_ratings.toLocaleString()} />
          <Stat label="Thể loại" value={stats.num_genres} />
          <Stat label="Rating TB" value={stats.avg_rating.toFixed(2)} />
          <Stat label="Sparsity" value={`${(stats.sparsity * 100).toFixed(1)}%`} />
        </section>
      )}

      <section className="panel">
        <h2>Learning Curve · Recall@10</h2>
        <p className="muted">
          Trục X: số tương tác ban đầu (0 → 20). Trục Y: Recall@10 trung bình. Mô phỏng người dùng
          warm bị ẩn bớt lịch sử để tái hiện trạng thái cold-start.
        </p>
        {loading && <div className="loading">Đang tính learning curve…</div>}
        {error && <div className="error-state">{error}</div>}
        {curve && <LearningCurveChart data={curve} />}
      </section>

      <section className="panel">
        <h2>Bảng so sánh phương pháp &amp; nghiên cứu liên quan</h2>
        <div className="table-wrap">
          <table className="compare-table">
            <thead>
              <tr>
                <th>Phương pháp</th>
                <th>Loại cold-start</th>
                <th>Ý tưởng cốt lõi</th>
                <th>Ưu điểm</th>
                <th>Hạn chế</th>
                <th>Tham chiếu</th>
              </tr>
            </thead>
            <tbody>
              {METHODS.map((m) => (
                <tr key={m.method}>
                  <td><b>{m.method}</b></td>
                  <td><span className="cold-tag">{m.cold}</span></td>
                  <td>{m.idea}</td>
                  <td>{m.pros}</td>
                  <td>{m.cons}</td>
                  <td className="muted">{m.ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel findings">
        <h2>Nhận xét chính</h2>
        <ul>
          <li><b>Lúc “lạnh” (0 tương tác):</b> Popularity là baseline mạnh nhất vì không cần dữ liệu cá nhân.</li>
          <li><b>Khi có vài tương tác:</b> Onboarding + Item-CF và DropoutNet vượt dần Popularity.</li>
          <li><b>Khi đủ ấm (≥10–20):</b> DropoutNet (hybrid) đạt Recall@10 cao nhất nhờ kết hợp content và collaborative.</li>
          <li><b>Hệ quả thiết kế:</b> nên chuyển dần trọng số từ content/popularity sang collaborative theo lượng tương tác.</li>
        </ul>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
