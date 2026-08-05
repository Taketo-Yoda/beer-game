from fastapi import APIRouter, Depends, HTTPException

from ..core.bots import decide_bot_order
from ..core.engine import advance_week, peek_demand_this_week, preview_turn
from ..core.models import ROLE_CHAIN, GameConfig, GameState, Role
from ..core.scenarios import default_config
from ..rate_limit import rate_limit
from ..schemas import (
    CreateGameRequest,
    DebriefRoleView,
    DebriefView,
    GameStateView,
    RoleView,
    SubmitOrderRequest,
    TurnPreviewView,
)
from ..store.game_store import GameStore, StoredGame, get_game_store

router = APIRouter(prefix="/api/games", tags=["games"], dependencies=[Depends(rate_limit)])


def _get_game_or_404(store: GameStore, game_id: str) -> StoredGame:
    try:
        return store.get(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found") from None


def _to_role_view(state: GameState, config: GameConfig, role: Role) -> RoleView:
    rs = state.roles[role]

    if state.is_finished:
        turn_preview = TurnPreviewView(shipment_received=0, shipment_sent=0, holding_cost=0.0, backorder_cost=0.0)
    else:
        preview = preview_turn(state, config, role)
        turn_preview = TurnPreviewView(
            shipment_received=preview.shipment_received,
            shipment_sent=preview.shipment_sent,
            holding_cost=preview.holding_cost,
            backorder_cost=preview.backorder_cost,
        )

    # order_historyは在庫ポジション計算のため開始時にorder_delay_weeks分だけ定常需要で
    # 種付けされている。inventory_history/backlog_historyと週数を揃えるため公開時に取り除く。
    return RoleView(
        role=role,
        inventory=rs.inventory,
        backlog=rs.backlog,
        cumulative_cost=rs.cumulative_cost,
        last_order_placed=rs.last_order_placed,
        order_history=list(rs.order_history[config.order_delay_weeks :]),
        inventory_history=list(rs.inventory_history),
        backlog_history=list(rs.backlog_history),
        pending_shipments=list(rs.incoming_shipments),
        turn_preview=turn_preview,
    )


def _to_state_view(game: StoredGame) -> GameStateView:
    demand_to_decide = (
        0 if game.state.is_finished else peek_demand_this_week(game.state, game.config, game.human_role)
    )
    return GameStateView(
        game_id=game.game_id,
        week=game.state.week,
        total_weeks=game.config.total_weeks,
        is_finished=game.state.is_finished,
        human_role=game.human_role,
        you=_to_role_view(game.state, game.config, game.human_role),
        demand_to_decide=demand_to_decide,
        order_delay_weeks=game.config.order_delay_weeks,
    )


@router.post("", response_model=GameStateView)
def create_game(request: CreateGameRequest, store: GameStore = Depends(get_game_store)) -> GameStateView:
    game = store.create(request.human_role, default_config())
    return _to_state_view(game)


@router.get("/{game_id}", response_model=GameStateView)
def get_game(game_id: str, store: GameStore = Depends(get_game_store)) -> GameStateView:
    game = _get_game_or_404(store, game_id)
    return _to_state_view(game)


@router.post("/{game_id}/orders", response_model=GameStateView)
def submit_order(
    game_id: str, request: SubmitOrderRequest, store: GameStore = Depends(get_game_store)
) -> GameStateView:
    game = _get_game_or_404(store, game_id)
    if game.state.is_finished:
        raise HTTPException(status_code=400, detail="game already finished")

    orders: dict[Role, int] = {}
    for role in ROLE_CHAIN:
        if role == game.human_role:
            orders[role] = request.order
        else:
            demand = peek_demand_this_week(game.state, game.config, role)
            orders[role] = decide_bot_order(game.state.roles[role], demand, game.config, role)

    new_state = advance_week(game.state, game.config, orders)
    game = store.update_state(game_id, new_state)
    return _to_state_view(game)


@router.get("/{game_id}/debrief", response_model=DebriefView)
def get_debrief(game_id: str, store: GameStore = Depends(get_game_store)) -> DebriefView:
    game = _get_game_or_404(store, game_id)
    if not game.state.is_finished:
        raise HTTPException(status_code=400, detail="game is not finished yet")

    return DebriefView(
        game_id=game.game_id,
        weeks_played=game.state.week,
        customer_demand=list(game.config.customer_demand),
        roles=[
            DebriefRoleView(
                role=role,
                inventory_history=list(game.state.roles[role].inventory_history),
                backlog_history=list(game.state.roles[role].backlog_history),
                order_history=list(game.state.roles[role].order_history[game.config.order_delay_weeks :]),
                cumulative_cost=game.state.roles[role].cumulative_cost,
            )
            for role in ROLE_CHAIN
        ],
    )
