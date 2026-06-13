import { Link, useLocation } from "react-router-dom";
import { BarChart3, Clapperboard, SlidersHorizontal } from "lucide-react";
import { useProfile } from "../state/profile";

interface Props {
  onOpenResearch: () => void;
}

export function Navbar({ onOpenResearch }: Props) {
  const { pathname } = useLocation();
  const { strategy } = useProfile();

  return (
    <header className="navbar">
      <div className="navbar-left">
        <Link to="/" className="brand">
          <Clapperboard size={26} />
          <span>COLD<b>FLIX</b></span>
        </Link>
        <nav className="nav-links">
          <Link to="/" className={pathname === "/" ? "active" : ""}>
            Trang chủ
          </Link>
          <Link to="/insights" className={pathname === "/insights" ? "active" : ""}>
            <BarChart3 size={15} /> Nghiên cứu
          </Link>
        </nav>
      </div>
      <div className="navbar-right">
        <button className="research-toggle" onClick={onOpenResearch}>
          <SlidersHorizontal size={15} />
          <span>Chế độ nghiên cứu</span>
          <span className="strategy-pill">{strategy}</span>
        </button>
        <div className="avatar" aria-hidden="true">7</div>
      </div>
    </header>
  );
}
