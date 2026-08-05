import { useEffect, useState } from "react";
import { submitOrder } from "../api/client";
import { formatManYen } from "../format";
import { ROLE_ICONS, ROLE_LABELS, downstreamOf, type GameStateView } from "../types";
import { BeerStock } from "./GameVisuals";

type Step = "card" | "tokens" | "order";
type ShipmentAnimPhase = "idle" | "receiving" | "shipping";

export function TurnRitual({
  state,
  onStateUpdated,
  onFinished,
}: {
  state: GameStateView;
  onStateUpdated: (state: GameStateView) => void;
  onFinished: () => void;
}) {
  const [step, setStep] = useState<Step>("card");
  const [shipmentAnim, setShipmentAnim] = useState<ShipmentAnimPhase>("idle");
  const [displayInventory, setDisplayInventory] = useState(state.you.inventory);
  const [order, setOrder] = useState(String(state.you.last_order_placed));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 新しい週に入るたびに、儀式をカードめくりからやり直す
  useEffect(() => {
    setStep("card");
    setShipmentAnim("idle");
    setDisplayInventory(state.you.inventory);
    setOrder(String(state.you.last_order_placed));
  }, [state.game_id, state.week, state.you.inventory, state.you.last_order_placed]);

  function handleFlipCard() {
    setStep("tokens");
  }

  function handleAdvanceTokens() {
    const { shipment_received, shipment_sent } = state.you.turn_preview;
    setShipmentAnim("receiving");
    setDisplayInventory(state.you.inventory + shipment_received);

    window.setTimeout(() => {
      setShipmentAnim("shipping");
      setDisplayInventory(state.you.inventory + shipment_received - shipment_sent);

      window.setTimeout(() => {
        setStep("order");
      }, 500);
    }, 700);
  }

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
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  const down = downstreamOf(state.human_role);
  const backCardCount = Math.max(state.order_delay_weeks - 1, 0);

  return (
    <div className="turn-ritual">
      <div className="ritual-step">
        <h2>① 受注カードをめくる</h2>
        <div className="order-card-row">
          {Array.from({ length: backCardCount }, (_, i) => (
            <div key={`back-${i}`} className="order-card-back" aria-hidden="true" />
          ))}
          <button
            type="button"
            className={step === "card" ? "flip-card" : "flip-card revealed"}
            onClick={handleFlipCard}
            disabled={step !== "card"}
            aria-label="受注カードをめくる"
          >
            <div className="flip-card-inner">
              <div className="flip-card-face flip-card-back">?</div>
              <div className="flip-card-face flip-card-front">{state.demand_to_decide}</div>
            </div>
          </button>
        </div>
        {step === "card" && <p className="muted">カードをクリックして今週の受注を確認してください</p>}
        {step !== "card" && (
          <div className="stat-tile">
            <span className="stat-label">今週の受注</span>
            <span className="stat-value">{state.demand_to_decide}</span>
          </div>
        )}
      </div>

      <div className={step === "card" ? "ritual-step disabled" : "ritual-step"}>
        <h2>② トークンを進める</h2>

        <div className="inventory-panel">
          <span className="stat-label">在庫</span>
          <span className="stat-value">{displayInventory}</span>
          <BeerStock count={displayInventory} />
          {shipmentAnim === "shipping" && down && (
            <span className="shipment-badge">
              {ROLE_ICONS[down]} {ROLE_LABELS[down]}へ{state.you.turn_preview.shipment_sent}個出荷 →
            </span>
          )}
        </div>

        <div className="shipment-lane">
          {state.you.pending_shipments.map((qty, i) => (
            <div key={i} className={i === 0 ? "shipment-slot next" : "shipment-slot"}>
              <span className="shipment-slot-label">{i === 0 ? "今週到着" : `輸送中（あと${i + 1}週）`}</span>
              <span className="shipment-slot-value">📦{qty}</span>
            </div>
          ))}
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={handleAdvanceTokens}
          disabled={step !== "tokens"}
        >
          トークンを進める
        </button>

        {step === "order" && (
          <div className="stat-grid">
            <div className="stat-tile">
              <span className="stat-label">今週の入荷</span>
              <span className="stat-value">{state.you.turn_preview.shipment_received}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-label">今週の出荷</span>
              <span className="stat-value">{state.you.turn_preview.shipment_sent}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-label">今週のコスト</span>
              <span className="stat-value">
                {formatManYen(state.you.turn_preview.holding_cost + state.you.turn_preview.backorder_cost)}
              </span>
              <span className="stat-breakdown">
                在庫 {formatManYen(state.you.turn_preview.holding_cost)} / 受注残{" "}
                {formatManYen(state.you.turn_preview.backorder_cost)}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className={step === "order" ? "ritual-step" : "ritual-step disabled"}>
        <h2>③ 発注カードに記入して伏せる</h2>
        <form onSubmit={handleSubmit} className="order-form">
          <label htmlFor="order-input">上流への発注量</label>
          <input
            id="order-input"
            type="number"
            min={0}
            step={1}
            value={order}
            onChange={(event) => setOrder(event.target.value)}
            disabled={step !== "order"}
          />
          <button type="submit" className="primary-button" disabled={step !== "order" || isSubmitting}>
            {isSubmitting ? "処理中..." : "カードを伏せて次の週へ"}
          </button>
        </form>
      </div>

      {error && <p className="error">エラー: {error}</p>}
    </div>
  );
}
