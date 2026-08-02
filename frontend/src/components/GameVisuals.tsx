import { ROLE_ICONS, ROLE_LABELS, downstreamOf, upstreamOf, type Role } from "../types";

const UNITS_PER_PACK = 10;
const MAX_PACK_ICONS = 12;

export function BeerStock({ count }: { count: number }) {
  if (count === 0) {
    return (
      <div className="beer-stock" aria-label="在庫 0個">
        <span className="muted">在庫なし</span>
      </div>
    );
  }

  const totalPacks = Math.floor(count / UNITS_PER_PACK);
  const shownPacks = Math.min(totalPacks, MAX_PACK_ICONS);
  const looseUnits = count - totalPacks * UNITS_PER_PACK;
  const overflow = (totalPacks - shownPacks) * UNITS_PER_PACK;

  return (
    <div className="beer-stock" aria-label={`在庫 ${count}個`}>
      {Array.from({ length: shownPacks }, (_, i) => (
        <span key={`pack-${i}`} className="beer-pack" title={`${UNITS_PER_PACK}個パック`}>
          🍺<span className="beer-pack-count">×{UNITS_PER_PACK}</span>
        </span>
      ))}
      {Array.from({ length: looseUnits }, (_, i) => (
        <span key={`unit-${i}`} className="beer-icon">
          🍺
        </span>
      ))}
      {overflow > 0 && <span className="beer-overflow">+{overflow}</span>}
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
