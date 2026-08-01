export type Role = "factory" | "distributor" | "wholesaler" | "retailer";

export const ROLE_LABELS: Record<Role, string> = {
  factory: "工場",
  distributor: "一次卸",
  wholesaler: "二次卸",
  retailer: "小売",
};

export interface RoleView {
  role: Role;
  inventory: number;
  backlog: number;
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
