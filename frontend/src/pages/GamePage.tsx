import { useState } from "react";
import { submitOrder } from "../api/client";
import { BeerStock, SupplyChainStrip } from "../components/GameVisuals";
import { formatYen } from "../format";
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
  const [order, setOrder] = useState(String(state.you.last_order_placed));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const orderQty = Number(order);
    if (!Number.isInteger(orderQty) || orderQty < 0) {
      setError("発注量は0以上の整数で入力してください");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const updated = await submitOrder(state.game_id, orderQty);
      if (updated.is_finished) {
        onFinished();
      } else {
        onStateUpdated(updated);
        setOrder(String(updated.you.last_order_placed));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  const { you } = state;
  const recentOrders = you.order_history.slice(-8);

  return (
    <section className="card">
      <h1>
        第{state.week + 1}週 / 全{state.total_weeks}週
      </h1>

      <SupplyChainStrip role={state.human_role} />

      <div className="inventory-panel">
        <span className="stat-label">在庫</span>
        <span className="stat-value">{you.inventory}</span>
        <BeerStock count={you.inventory} />
      </div>

      <div className="stat-grid">
        <div className="stat-tile">
          <span className="stat-label">受注残</span>
          <span className="stat-value">{you.backlog}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">今週の入荷</span>
          <span className="stat-value">{you.last_shipment_received}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">今週の受注</span>
          <span className="stat-value">{state.demand_to_decide}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">今週のコスト</span>
          <span className="stat-value">{formatYen(you.last_week_cost)}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">累計コスト</span>
          <span className="stat-value">{formatYen(you.cumulative_cost)}</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="order-form">
        <label htmlFor="order-input">上流への発注量</label>
        <input
          id="order-input"
          type="number"
          min={0}
          step={1}
          value={order}
          onChange={(event) => setOrder(event.target.value)}
        />
        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? "処理中..." : "発注して次の週へ"}
        </button>
      </form>

      {error && <p className="error">エラー: {error}</p>}

      {recentOrders.length > 0 && (
        <div className="history">
          <h2>直近の発注履歴</h2>
          <p className="muted">{recentOrders.join(" → ")}</p>
        </div>
      )}
    </section>
  );
}
