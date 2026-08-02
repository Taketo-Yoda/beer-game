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

export interface RoleView {
  role: Role;
  inventory: number;
  backlog: number;
  last_shipment_received: number;
  last_shipment_sent: number;
  last_holding_cost: number;
  last_backorder_cost: number;
  last_week_cost: number;
  cumulative_cost: number;
  last_order_placed: number;
  order_history: number[];
  inventory_history: number[];
  backlog_history: number[];
}

export interface GameStateView {
  game_id: string;
  week: number;
  total_weeks: number;
  is_finished: boolean;
  human_role: Role;
  you: RoleView;
  demand_to_decide: number;
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
