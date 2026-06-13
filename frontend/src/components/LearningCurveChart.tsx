import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LearningCurveResponse } from "../api/client";

const COLORS = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f87171"];

interface Props {
  data: LearningCurveResponse;
}

export function LearningCurveChart({ data }: Props) {
  const chartData = data.curves[0]?.points.map((point) => {
    const row: Record<string, number | string> = { interactions: point.interactions };
    for (const curve of data.curves) {
      const match = curve.points.find((p) => p.interactions === point.interactions);
      row[curve.strategy] = match?.recall_at_10 ?? 0;
    }
    return row;
  });

  return (
    <div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis
              dataKey="interactions"
              stroke="#94a3b8"
              label={{ value: "Số tương tác ban đầu", position: "insideBottom", offset: -4, fill: "#94a3b8" }}
            />
            <YAxis
              stroke="#94a3b8"
              domain={[0, "auto"]}
              label={{ value: "Recall@10", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
            />
            <Tooltip
              contentStyle={{
                background: "#161f3d",
                border: "1px solid rgba(148,163,184,0.18)",
                borderRadius: 12,
              }}
            />
            <Legend />
            {data.curves.map((curve, index) => (
              <Line
                key={curve.strategy}
                type="monotone"
                dataKey={curve.strategy}
                name={curve.label}
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={3}
                dot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p style={{ color: "var(--muted)", marginTop: 12 }}>{data.note}</p>
      <div className="legend">
        {data.curves.map((curve, index) => (
          <div className="legend-item" key={curve.strategy}>
            <span
              className="legend-dot"
              style={{ background: COLORS[index % COLORS.length] }}
            />
            {curve.label}
          </div>
        ))}
      </div>
    </div>
  );
}
