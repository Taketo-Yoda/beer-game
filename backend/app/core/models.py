from enum import Enum

from pydantic import BaseModel, ConfigDict


class Role(str, Enum):
    FACTORY = "factory"
    DISTRIBUTOR = "distributor"
    WHOLESALER = "wholesaler"
    RETAILER = "retailer"


# 上流(FACTORY)から下流(RETAILER)への順序。財はこの順で流れ、発注は逆方向に流れる。
ROLE_CHAIN: tuple[Role, ...] = (
    Role.FACTORY,
    Role.DISTRIBUTOR,
    Role.WHOLESALER,
    Role.RETAILER,
)


def upstream_of(role: Role) -> Role | None:
    idx = ROLE_CHAIN.index(role)
    return ROLE_CHAIN[idx - 1] if idx > 0 else None


def downstream_of(role: Role) -> Role | None:
    idx = ROLE_CHAIN.index(role)
    return ROLE_CHAIN[idx + 1] if idx < len(ROLE_CHAIN) - 1 else None


class GameConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    initial_inventory: int = 12
    shipping_delay_weeks: int = 2
    order_delay_weeks: int = 2
    production_delay_weeks: int = 2
    holding_cost_per_unit: float = 0.5
    backorder_cost_per_unit: float = 1.0
    total_weeks: int = 36
    # 週ごとの顧客需要。長さはtotal_weeksと一致し、customer_demand[i]は第(i+1)週の需要を表す。
    customer_demand: tuple[int, ...]


class RoleState(BaseModel):
    model_config = ConfigDict(frozen=True)

    inventory: int
    backlog: int
    # 輸送中/生産中で自分にまだ到着していない数量のキュー。先頭が次に到着する分。
    incoming_shipments: tuple[int, ...]
    # 下流からの発注のうち、まだ自分に届いていない（伝達遅延中の）もの。FACTORYは常に空。
    incoming_orders: tuple[int, ...]
    last_order_placed: int = 0
    cumulative_cost: float = 0.0
    order_history: tuple[int, ...] = ()
    inventory_history: tuple[int, ...] = ()
    backlog_history: tuple[int, ...] = ()


class GameState(BaseModel):
    model_config = ConfigDict(frozen=True)

    week: int
    roles: dict[Role, RoleState]
    is_finished: bool = False
