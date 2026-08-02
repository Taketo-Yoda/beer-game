import { useState } from "react";
import { createGame } from "../api/client";
import { ROLE_ICONS, ROLE_LABELS, type GameStateView, type Role } from "../types";

const ROLES: Role[] = ["retailer", "wholesaler", "distributor", "factory"];

export function GameSetupPage({ onStarted }: { onStarted: (state: GameStateView) => void }) {
  const [selectedRole, setSelectedRole] = useState<Role>("retailer");
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleStart() {
    setIsStarting(true);
    setError(null);
    try {
      const state = await createGame(selectedRole);
      onStarted(state);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsStarting(false);
    }
  }

  return (
    <section className="card">
      <h1>ビールゲーム</h1>
      <p className="muted">
        サプライチェーンの4つの役割のうち1つを担当し、残り3役はAIが自動でプレイします。
        毎週、下流からの受注を確認して上流への発注量を決め、在庫と欠品のコストを最小化しましょう。
      </p>

      <h2>担当する役割を選んでください</h2>
      <div className="role-grid">
        {ROLES.map((role) => (
          <button
            key={role}
            type="button"
            className={role === selectedRole ? "role-button selected" : "role-button"}
            onClick={() => setSelectedRole(role)}
          >
            <span className="role-button-icon">{ROLE_ICONS[role]}</span>
            {ROLE_LABELS[role]}
          </button>
        ))}
      </div>

      <button type="button" className="primary-button" onClick={handleStart} disabled={isStarting}>
        {isStarting ? "開始しています..." : "ゲーム開始"}
      </button>

      {error && <p className="error">エラー: {error}</p>}
    </section>
  );
}
