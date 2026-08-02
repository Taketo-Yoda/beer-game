from pydantic import BaseModel, Field

from .core.models import Role


class CreateGameRequest(BaseModel):
    human_role: Role


class SubmitOrderRequest(BaseModel):
    order: int = Field(ge=0)


class RoleView(BaseModel):
    role: Role
    inventory: int
    backlog: int
    last_shipment_received: int
    last_week_cost: float
    cumulative_cost: float
    last_order_placed: int
    order_history: list[int]
    inventory_history: list[int]
    backlog_history: list[int]


class GameStateView(BaseModel):
    game_id: str
    week: int
    total_weeks: int
    is_finished: bool
    human_role: Role
    you: RoleView
    # 今週の受注（下流の発注、小売なら顧客需要）。発注量を決める判断材料として提示する。
    demand_to_decide: int


class DebriefRoleView(BaseModel):
    role: Role
    inventory_history: list[int]
    backlog_history: list[int]
    order_history: list[int]
    cumulative_cost: float


class DebriefView(BaseModel):
    game_id: str
    weeks_played: int
    customer_demand: list[int]
    roles: list[DebriefRoleView]
