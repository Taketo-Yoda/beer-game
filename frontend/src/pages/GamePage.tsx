import { SupplyChainStrip } from "../components/GameVisuals";
import { TurnRitual } from "../components/TurnRitual";
import { formatManYen } from "../format";
import type { GameStateView } from "../types";

export function GamePage({
  state,
  onStateUpdated,
  onFinished,
}: {
  state: GameStateView;
  onStateUpdated: (state: GameStateView) => void;
  onFinished: () => void;
}) {
  const { you } = state;
  const recentOrders = you.order_history.slice(-8);

  return (
    <section className="card">
      <h1>
        第{state.week + 1}週 / 全{state.total_weeks}週
      </h1>

      <SupplyChainStrip role={state.human_role} />

      <div className="stat-grid">
        <div className="stat-tile">
          <span className="stat-label">受注残</span>
          <span className="stat-value">{you.backlog}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">累計コスト</span>
          <span className="stat-value">{formatManYen(you.cumulative_cost)}</span>
        </div>
      </div>

      <TurnRitual state={state} onStateUpdated={onStateUpdated} onFinished={onFinished} />

      {recentOrders.length > 0 && (
        <div className="history">
          <h2>直近の発注履歴</h2>
          <p className="muted">{recentOrders.join(" → ")}</p>
        </div>
      )}
    </section>
  );
}
