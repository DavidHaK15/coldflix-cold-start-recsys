import { Link } from "react-router-dom";
import { RotateCcw, X } from "lucide-react";
import { useProfile } from "../state/profile";
import type { StrategyInfo } from "../api/client";

interface Props {
  open: boolean;
  onClose: () => void;
  strategies: StrategyInfo[];
  warmUsers: number[];
}

export function ResearchPanel({ open, onClose, strategies, warmUsers }: Props) {
  const {
    strategy,
    setStrategy,
    simulatedUserId,
    setSimulatedUser,
    genres,
    interactionCount,
    reset,
  } = useProfile();

  const active = strategies.find((s) => s.id === strategy);

  return (
    <>
      <div className={`drawer-scrim ${open ? "show" : ""}`} onClick={onClose} />
      <aside className={`drawer ${open ? "open" : ""}`} aria-hidden={!open}>
        <div className="drawer-head">
          <h3>Chế độ nghiên cứu</h3>
          <button className="modal-close static" onClick={onClose} aria-label="Đóng">
            <X size={18} />
          </button>
        </div>
        <p className="drawer-sub">
          Đổi chiến lược & hồ sơ người dùng để thấy hàng <b>“Gợi ý cho bạn”</b> thay đổi tức thì.
        </p>

        <div className="drawer-section">
          <label>Chiến lược xử lý cold-start</label>
          <div className="strategy-list">
            {strategies.map((item) => (
              <button
                key={item.id}
                className={`strategy-btn ${strategy === item.id ? "active" : ""}`}
                onClick={() => setStrategy(item.id)}
              >
                <span className="strategy-name">
                  {item.name}
                  <span className="cold-tag">{item.cold_start_type}</span>
                </span>
                <small>{item.description}</small>
              </button>
            ))}
          </div>
        </div>

        <div className="drawer-section">
          <label>Hồ sơ người dùng mô phỏng</label>
          <select
            value={simulatedUserId ?? ""}
            onChange={(e) => setSimulatedUser(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">🆕 Người dùng MỚI (chính là bạn)</option>
            {warmUsers.map((id) => (
              <option key={id} value={id}>
                Người dùng warm #{id} (đã có lịch sử)
              </option>
            ))}
          </select>
          <p className="drawer-note">
            {simulatedUserId
              ? "Dùng lịch sử thật của user này — minh hoạ trạng thái 'warm' (hết cold-start)."
              : `Bạn đang là người dùng mới: ${genres.length} thể loại, ${interactionCount} lượt chấm điểm.`}
          </p>
        </div>

        {active && (
          <div className="drawer-explain">
            <h4>Đang áp dụng: {active.name}</h4>
            <p>{active.description}</p>
          </div>
        )}

        <div className="drawer-foot">
          <Link to="/insights" className="btn btn--ghost" onClick={onClose}>
            Xem kết quả nghiên cứu →
          </Link>
          <button className="btn btn--circle" onClick={reset} aria-label="Đặt lại hồ sơ" title="Đặt lại hồ sơ">
            <RotateCcw size={16} />
          </button>
        </div>
      </aside>
    </>
  );
}
