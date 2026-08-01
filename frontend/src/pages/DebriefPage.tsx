import { useEffect, useState } from "react";
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
import { getDebrief } from "../api/client";
import { GRIDLINE, MUTED_INK, roleColor, useIsDarkMode } from "../theme/palette";
import { ROLE_LABELS, type DebriefView, type Role } from "../types";

const ROLE_CHAIN: Role[] = ["factory", "distributor", "wholesaler", "retailer"];

function buildSeries(debrief: DebriefView, metric: "order_history" | "inventory_history" | "backlog_history") {
  const weeks = debrief.weeks_played;
  return Array.from({ length: weeks }, (_, i) => {
    const point: Record<string, number> = { week: i + 1 };
    for (const role of debrief.roles) {
      point[role.role] = role[metric][i] ?? 0;
    }
    if (metric === "order_history") {
      point.customer_demand = debrief.customer_demand[i] ?? 0;
    }
    return point;
  });
}

function MetricChart({
  title,
  data,
  isDark,
  showCustomerDemand,
}: {
  title: string;
  data: Record<string, number>[];
  isDark: boolean;
  showCustomerDemand?: boolean;
}) {
  const gridline = isDark ? GRIDLINE.dark : GRIDLINE.light;
  const mutedInk = isDark ? MUTED_INK.dark : MUTED_INK.light;

  return (
    <div className="chart-card">
      <h2>{title}</h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke={gridline} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="week" stroke={mutedInk} tick={{ fill: mutedInk, fontSize: 12 }} />
          <YAxis stroke={mutedInk} tick={{ fill: mutedInk, fontSize: 12 }} />
          <Tooltip contentStyle={{ fontSize: 13 }} />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          {showCustomerDemand && (
            <Line
              type="monotone"
              dataKey="customer_demand"
              name="顧客需要"
              stroke={mutedInk}
              strokeDasharray="4 4"
              strokeWidth={2}
              dot={false}
            />
          )}
          {ROLE_CHAIN.map((role) => (
            <Line
              key={role}
              type="monotone"
              dataKey={role}
              name={ROLE_LABELS[role]}
              stroke={roleColor(role, isDark)}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DebriefPage({ gameId }: { gameId: string }) {
  const [debrief, setDebrief] = useState<DebriefView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isDark = useIsDarkMode();

  useEffect(() => {
    getDebrief(gameId)
      .then(setDebrief)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [gameId]);

  if (error) {
    return (
      <section className="card">
        <p className="error">振り返りデータの取得に失敗しました: {error}</p>
      </section>
    );
  }

  if (!debrief) {
    return (
      <section className="card">
        <p className="muted">読み込み中...</p>
      </section>
    );
  }

  const totalCost = debrief.roles.reduce((sum, role) => sum + role.cumulative_cost, 0);

  return (
    <section className="card">
      <h1>ゲーム終了 - 振り返り</h1>
      <p className="muted">
        全{debrief.weeks_played}週を完了しました。サプライチェーン全体の累計コストは
        ${totalCost.toFixed(1)} でした。上流（工場）ほど発注量の振れ幅が大きくなる
        「ブルウィップ効果」がグラフから確認できるはずです。
      </p>

      <MetricChart title="発注量の推移" data={buildSeries(debrief, "order_history")} isDark={isDark} showCustomerDemand />
      <MetricChart title="在庫の推移" data={buildSeries(debrief, "inventory_history")} isDark={isDark} />
      <MetricChart title="受注残の推移" data={buildSeries(debrief, "backlog_history")} isDark={isDark} />

      <table className="cost-table">
        <thead>
          <tr>
            <th>役割</th>
            <th>累計コスト</th>
          </tr>
        </thead>
        <tbody>
          {debrief.roles.map((role) => (
            <tr key={role.role}>
              <td>{ROLE_LABELS[role.role]}</td>
              <td>${role.cumulative_cost.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
