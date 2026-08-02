import { ROLE_ICONS, ROLE_LABELS, downstreamOf, upstreamOf, type Role } from "../types";

const MAX_BEER_ICONS = 20;

export function BeerStock({ count }: { count: number }) {
  const shown = Math.min(count, MAX_BEER_ICONS);
  const overflow = count - shown;

  return (
    <div className="beer-stock" aria-label={`在庫 ${count}個`}>
      {count === 0 ? (
        <span className="muted">在庫なし</span>
      ) : (
        <>
          {Array.from({ length: shown }, (_, i) => (
            <span key={i} className="beer-icon">
              🍺
            </span>
          ))}
          {overflow > 0 && <span className="beer-overflow">+{overflow}</span>}
        </>
      )}
    </div>
  );
}

function RoleNode({
  icon,
  label,
  highlight,
}: {
  icon: string;
  label: string;
  highlight?: boolean;
}) {
  return (
    <div className={highlight ? "role-node highlight" : "role-node"}>
      <span className="role-node-icon">{icon}</span>
      <span className="role-node-label">{label}</span>
    </div>
  );
}

export function SupplyChainStrip({ role }: { role: Role }) {
  const up = upstreamOf(role);
  const down = downstreamOf(role);

  return (
    <div className="supply-chain-strip">
      <RoleNode icon={up ? ROLE_ICONS[up] : "🌾"} label={up ? ROLE_LABELS[up] : "原材料"} />
      <span className="chain-arrow">→</span>
      <RoleNode icon={ROLE_ICONS[role]} label={`${ROLE_LABELS[role]}（あなた）`} highlight />
      <span className="chain-arrow">→</span>
      <RoleNode icon={down ? ROLE_ICONS[down] : "🧑"} label={down ? ROLE_LABELS[down] : "顧客"} />
    </div>
  );
}
