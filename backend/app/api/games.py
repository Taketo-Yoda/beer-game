from fastapi import APIRouter, Depends, HTTPException

from ..core.bots import decide_bot_order
from ..core.engine import advance_week, peek_demand_this_week
from ..core.models import ROLE_CHAIN, Role, RoleState
from ..core.scenarios import default_config
from ..schemas import (
    CreateGameRequest,
    DebriefRoleView,
    DebriefView,
    GameStateView,
    RoleView,
    SubmitOrderRequest,
)
from ..store.game_store import GameStore, StoredGame, get_game_store

router = APIRouter(prefix="/api/games", tags=["games"])


def _get_game_or_404(store: GameStore, game_id: str) -> StoredGame:
    try:
        return store.get(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found") from None


def _to_role_view(role: Role, rs: RoleState, order_delay_weeks: int) -> RoleView:
    # order_historyは在庫ポジション計算のため開始時にorder_delay_weeks分だけ定常需要で
    # 種付けされている。inventory_history/backlog_historyと週数を揃えるため公開時に取り除く。
    return RoleView(
        role=role,
        inventory=rs.inventory,
        backlog=rs.backlog,
        cumulative_cost=rs.cumulative_cost,
        last_order_placed=rs.last_order_placed,
        order_history=list(rs.order_history[order_delay_weeks:]),
        inventory_history=list(rs.inventory_history),
        backlog_history=list(rs.backlog_history),
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
        you=_to_role_view(game.human_role, game.state.roles[game.human_role], game.config.order_delay_weeks),
        demand_to_decide=demand_to_decide,
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
