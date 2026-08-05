from pydantic import BaseModel, Field

from .core.models import Role


class CreateGameRequest(BaseModel):
    human_role: Role


class SubmitOrderRequest(BaseModel):
    order: int = Field(ge=0)


class TurnPreviewView(BaseModel):
    shipment_received: int
    shipment_sent: int
    holding_cost: float
    backorder_cost: float


class RoleView(BaseModel):
    role: Role
    inventory: int
    backlog: int
    cumulative_cost: float
    last_order_placed: int
    order_history: list[int]
    inventory_history: list[int]
    backlog_history: list[int]
    # 輸送中トークンの生データ（物理的なトークンなので中身を隠す必要はない）。先頭が今週到着する分。
    pending_shipments: list[int]
    # まだ発注していない今週の入荷・出荷・コストのプレビュー（これから提出する発注量には依存しない）
    turn_preview: TurnPreviewView


class GameStateView(BaseModel):
    game_id: str
    week: int
    total_weeks: int
    is_finished: bool
    human_role: Role
    you: RoleView
    # 今週の受注（下流の発注、小売なら顧客需要）。発注量を決める判断材料として提示する。
    demand_to_decide: int
    # 発注カードの伝達レーンの長さ。フロントで伏せカードのスロット数を描画するために使う。
    order_delay_weeks: int


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
