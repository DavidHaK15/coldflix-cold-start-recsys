import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { api, type DatasetStats, type Movie, type StrategyInfo } from "./api/client";
import { useProfile } from "./state/profile";
import { Navbar } from "./components/Navbar";
import { DetailModal } from "./components/DetailModal";
import { OnboardingModal } from "./components/OnboardingModal";
import { ResearchPanel } from "./components/ResearchPanel";
import { Home } from "./pages/Home";
import { Insights } from "./pages/Insights";

export default function App() {
  const { onboarded } = useProfile();
  const [catalog, setCatalog] = useState<Movie[]>([]);
  const [genres, setGenres] = useState<string[]>([]);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [warmUsers, setWarmUsers] = useState<number[]>([]);
  const [stats, setStats] = useState<DatasetStats | null>(null);
  const [researchOpen, setResearchOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        const [catalogData, genreData, strategyData, warmData, statsData] = await Promise.all([
          api.getCatalog(),
          api.getGenres(),
          api.getStrategies(),
          api.getWarmUsers(),
          api.getStats(),
        ]);
        setCatalog(catalogData);
        setGenres(genreData.genres);
        setStrategies(strategyData);
        setWarmUsers(warmData.users.slice(0, 24));
        setStats(statsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Không thể kết nối backend");
      }
    }
    bootstrap();
  }, []);

  if (error) {
    return (
      <div className="splash">
        <h1>COLD<b>FLIX</b></h1>
        <p className="error-state">{error}</p>
        <p className="muted">Hãy chắc chắn backend đang chạy ở cổng 8000.</p>
      </div>
    );
  }

  if (catalog.length === 0) {
    return (
      <div className="splash">
        <h1 className="splash-logo">COLD<b>FLIX</b></h1>
        <div className="splash-bar"><span /></div>
      </div>
    );
  }

  return (
    <div className="app">
      <Navbar onOpenResearch={() => setResearchOpen(true)} />
      <main>
        <Routes>
          <Route path="/" element={<Home catalog={catalog} genres={genres} />} />
          <Route path="/insights" element={<Insights stats={stats} />} />
        </Routes>
      </main>
      <footer className="footer">
        <span>ColdFlix · Đồ án Chủ đề 7 — Xử lý Cold-Start trong Hệ thống Khuyến nghị</span>
        <span className="muted">Môn Xu hướng mới trong ICT · CHKHMT15A1</span>
      </footer>

      <ResearchPanel
        open={researchOpen}
        onClose={() => setResearchOpen(false)}
        strategies={strategies}
        warmUsers={warmUsers}
      />
      <DetailModal />
      {!onboarded && <OnboardingModal genres={genres} onClose={() => undefined} />}
    </div>
  );
}
