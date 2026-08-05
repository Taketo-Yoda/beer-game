export type Role = "factory" | "distributor" | "wholesaler" | "retailer";

export const ROLE_CHAIN: Role[] = ["factory", "distributor", "wholesaler", "retailer"];

export const ROLE_LABELS: Record<Role, string> = {
  factory: "工場",
  distributor: "一次卸",
  wholesaler: "二次卸",
  retailer: "小売",
};

export const ROLE_ICONS: Record<Role, string> = {
  factory: "🏭",
  distributor: "🚚",
  wholesaler: "📦",
  retailer: "🏪",
};

export function upstreamOf(role: Role): Role | null {
  const index = ROLE_CHAIN.indexOf(role);
  return index > 0 ? ROLE_CHAIN[index - 1] : null;
}

export function downstreamOf(role: Role): Role | null {
  const index = ROLE_CHAIN.indexOf(role);
  return index < ROLE_CHAIN.length - 1 ? ROLE_CHAIN[index + 1] : null;
}

export interface TurnPreview {
  shipment_received: number;
  shipment_sent: number;
  holding_cost: number;
  backorder_cost: number;
}

export interface RoleView {
  role: Role;
  inventory: number;
  backlog: number;
  cumulative_cost: number;
  last_order_placed: number;
  order_history: number[];
  inventory_history: number[];
  backlog_history: number[];
  // 輸送中トークンの生データ。先頭が今週到着する分。
  pending_shipments: number[];
  // まだ発注していない今週の入荷・出荷・コストのプレビュー
  turn_preview: TurnPreview;
}

export interface GameStateView {
  game_id: string;
  week: number;
  total_weeks: number;
  is_finished: boolean;
  human_role: Role;
  you: RoleView;
  demand_to_decide: number;
  order_delay_weeks: number;
}

export interface DebriefRoleView {
  role: Role;
  inventory_history: number[];
  backlog_history: number[];
  order_history: number[];
  cumulative_cost: number;
}

export interface DebriefView {
  game_id: string;
  weeks_played: number;
  customer_demand: number[];
  roles: DebriefRoleView[];
}
