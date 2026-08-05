import pytest

from app.core.bots import decide_bot_order
from app.core.engine import advance_week, create_initial_state, peek_demand_this_week, preview_turn
from app.core.models import ROLE_CHAIN, GameConfig, GameState, Role, RoleState
from app.core.scenarios import classic_customer_demand, default_config


def make_config(**overrides) -> GameConfig:
    defaults = dict(
        initial_inventory=12,
        shipping_delay_weeks=2,
        order_delay_weeks=2,
        production_delay_weeks=2,
        holding_cost_per_unit=0.5,
        backorder_cost_per_unit=1.0,
        total_weeks=8,
        customer_demand=(4,) * 8,
    )
    defaults.update(overrides)
    return GameConfig(**defaults)


def test_create_initial_state_seeds_pipelines_with_steady_demand():
    config = make_config()
    state = create_initial_state(config)

    assert state.week == 0
    assert not state.is_finished
    for role in ROLE_CHAIN:
        rs = state.roles[role]
        assert rs.inventory == 12
        assert rs.backlog == 0
        assert rs.last_order_placed == 4

    assert state.roles[Role.FACTORY].incoming_shipments == (4, 4)
    assert state.roles[Role.FACTORY].incoming_orders == (4, 4)
    assert state.roles[Role.RETAILER].incoming_shipments == (4, 4)
    assert state.roles[Role.RETAILER].incoming_orders == (4, 4)


def test_steady_orders_keep_the_system_in_equilibrium():
    config = make_config(total_weeks=8, customer_demand=(4,) * 8)
    state = create_initial_state(config)
    orders = {role: 4 for role in ROLE_CHAIN}

    for _ in range(8):
        state = advance_week(state, config, orders)
        for role in ROLE_CHAIN:
            rs = state.roles[role]
            assert rs.inventory == 12
            assert rs.backlog == 0
            assert rs.cumulative_cost == pytest.approx(6.0 * state.week)

    assert state.is_finished
    assert state.week == 8


def test_insufficient_inventory_creates_backlog_and_cost():
    config = make_config(total_weeks=1, customer_demand=(3,))
    state = GameState(
        week=0,
        roles={
            Role.FACTORY: RoleState(inventory=100, backlog=0, incoming_shipments=(0,) * 2, incoming_orders=()),
            Role.DISTRIBUTOR: RoleState(
                inventory=100, backlog=0, incoming_shipments=(0,) * 2, incoming_orders=(0,) * 2
            ),
            Role.WHOLESALER: RoleState(
                inventory=100, backlog=0, incoming_shipments=(0,) * 2, incoming_orders=(0,) * 2
            ),
            Role.RETAILER: RoleState(inventory=2, backlog=1, incoming_shipments=(0,) * 2, incoming_orders=(0,) * 2),
        },
    )
    orders = {role: 0 for role in ROLE_CHAIN}

    new_state = advance_week(state, config, orders)
    retailer = new_state.roles[Role.RETAILER]

    # 受注残1 + 顧客需要3 = 4 の需要に対し在庫は2しかないため、2出荷し受注残2が残る
    assert retailer.inventory == 0
    assert retailer.backlog == 2
    assert retailer.cumulative_cost == pytest.approx(2.0)
    assert retailer.inventory_history == (0,)
    assert retailer.backlog_history == (2,)
    assert retailer.order_history == (0,)


def test_shipping_delay_propagates_after_exact_number_of_weeks():
    config = make_config(
        shipping_delay_weeks=2,
        order_delay_weeks=2,
        production_delay_weeks=2,
        total_weeks=3,
        customer_demand=(0, 0, 0),
    )
    state = GameState(
        week=0,
        roles={
            Role.FACTORY: RoleState(inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=()),
            Role.DISTRIBUTOR: RoleState(
                inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=(0, 0)
            ),
            Role.WHOLESALER: RoleState(
                inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=(0, 0)
            ),
            Role.RETAILER: RoleState(inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=(0, 0)),
        },
    )

    def orders(factory_order: int) -> dict[Role, int]:
        return {Role.FACTORY: factory_order, Role.DISTRIBUTOR: 0, Role.WHOLESALER: 0, Role.RETAILER: 0}

    state = advance_week(state, config, orders(7))
    assert state.roles[Role.FACTORY].incoming_shipments == (0, 7)
    assert state.roles[Role.DISTRIBUTOR].inventory == 0

    state = advance_week(state, config, orders(0))
    assert state.roles[Role.FACTORY].incoming_shipments == (7, 0)
    assert state.roles[Role.FACTORY].inventory == 0

    state = advance_week(state, config, orders(0))
    assert state.roles[Role.FACTORY].inventory == 7


def test_order_delay_propagates_before_becoming_visible_demand():
    config = make_config(
        shipping_delay_weeks=2,
        order_delay_weeks=2,
        production_delay_weeks=2,
        total_weeks=2,
        customer_demand=(0, 0),
    )
    state = GameState(
        week=0,
        roles={
            Role.FACTORY: RoleState(inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=()),
            Role.DISTRIBUTOR: RoleState(
                inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=(0, 0)
            ),
            Role.WHOLESALER: RoleState(
                inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=(0, 0)
            ),
            Role.RETAILER: RoleState(inventory=0, backlog=0, incoming_shipments=(0, 0), incoming_orders=(0, 0)),
        },
    )

    def orders(retailer_order: int) -> dict[Role, int]:
        return {Role.FACTORY: 0, Role.DISTRIBUTOR: 0, Role.WHOLESALER: 0, Role.RETAILER: retailer_order}

    state = advance_week(state, config, orders(9))
    assert state.roles[Role.WHOLESALER].incoming_orders == (0, 9)

    state = advance_week(state, config, orders(0))
    assert state.roles[Role.WHOLESALER].incoming_orders == (9, 0)


def test_advance_week_rejects_missing_or_negative_orders():
    config = make_config()
    state = create_initial_state(config)

    with pytest.raises(ValueError):
        advance_week(state, config, {Role.FACTORY: 4})  # 他役割が欠けている

    with pytest.raises(ValueError):
        advance_week(state, config, {role: -1 for role in ROLE_CHAIN})


def test_advance_week_raises_once_game_is_finished():
    config = make_config(total_weeks=1, customer_demand=(4,))
    state = create_initial_state(config)
    orders = {role: 4 for role in ROLE_CHAIN}

    state = advance_week(state, config, orders)
    assert state.is_finished

    with pytest.raises(ValueError):
        advance_week(state, config, orders)


def test_peek_demand_this_week_matches_what_advance_week_consumes():
    config = make_config()
    state = create_initial_state(config)

    assert peek_demand_this_week(state, config, Role.RETAILER) == 4
    assert peek_demand_this_week(state, config, Role.WHOLESALER) == 4


def test_preview_turn_matches_subsequent_advance_week_regardless_of_orders():
    config = make_config(total_weeks=2, customer_demand=(3, 3))
    state = GameState(
        week=0,
        roles={
            Role.FACTORY: RoleState(inventory=100, backlog=0, incoming_shipments=(5, 5), incoming_orders=(5, 5)),
            Role.DISTRIBUTOR: RoleState(
                inventory=100, backlog=0, incoming_shipments=(5, 5), incoming_orders=(5, 5)
            ),
            Role.WHOLESALER: RoleState(
                inventory=100, backlog=0, incoming_shipments=(5, 5), incoming_orders=(5, 5)
            ),
            Role.RETAILER: RoleState(inventory=2, backlog=1, incoming_shipments=(5, 5), incoming_orders=(5, 5)),
        },
    )

    preview = preview_turn(state, config, Role.RETAILER)

    assert preview.shipment_received == 5
    # 受注残1 + 顧客需要3 = 4 の需要に対し、入荷後在庫7から4出荷
    assert preview.shipment_sent == 4
    # 出荷後在庫は7-4=3、受注残は0
    assert preview.holding_cost == pytest.approx(3 * config.holding_cost_per_unit)
    assert preview.backorder_cost == pytest.approx(0.0)

    # これから提出する発注量を変えても、プレビューした今週の結果は変わらない
    # （発注は将来のパイプラインにのみ影響するため）
    for orders in ({role: 0 for role in ROLE_CHAIN}, {role: 999 for role in ROLE_CHAIN}):
        new_state = advance_week(state, config, orders)
        retailer = new_state.roles[Role.RETAILER]
        assert retailer.inventory == 3
        assert retailer.backlog == 0
        assert retailer.cumulative_cost == pytest.approx(preview.holding_cost + preview.backorder_cost)


def test_preview_turn_raises_once_game_is_finished():
    config = make_config(total_weeks=1, customer_demand=(4,))
    state = create_initial_state(config)
    orders = {role: 4 for role in ROLE_CHAIN}

    state = advance_week(state, config, orders)
    assert state.is_finished

    with pytest.raises(ValueError):
        preview_turn(state, config, Role.RETAILER)


def test_classic_customer_demand_surges_at_configured_week():
    demand = classic_customer_demand(total_weeks=8, initial_demand=4, surge_week=5, surge_demand=8)
    assert demand == (4, 4, 4, 4, 8, 8, 8, 8)


def test_bot_orders_match_demand_in_steady_state():
    config = default_config(total_weeks=8)
    state = create_initial_state(config)

    for role in ROLE_CHAIN:
        demand = peek_demand_this_week(state, config, role)
        order = decide_bot_order(state.roles[role], demand, config, role)
        assert order == 4


def test_bot_overreacts_to_a_demand_surge_then_returns_to_new_steady_state():
    config = default_config(total_weeks=40)
    state = create_initial_state(config)
    orders = {role: 4 for role in ROLE_CHAIN}

    # 需要急増(第5週)の直前まで、bot方策そのものでシステムを進める
    for _ in range(4):
        orders = {
            role: decide_bot_order(state.roles[role], peek_demand_this_week(state, config, role), config, role)
            for role in ROLE_CHAIN
        }
        state = advance_week(state, config, orders)

    # 急増直後、顧客需要を直接観測する小売はその場で反応し、在庫ポジションのギャップも
    # 埋めようとするため新しい定常需要(8)を大きく上回って発注する(ブルウィップの萌芽)。
    # 他の役割は発注遅延分だけ遅れて観測するため、この時点ではまだ反応しない。
    retailer_demand = peek_demand_this_week(state, config, Role.RETAILER)
    assert retailer_demand == 8
    retailer_surge_order = decide_bot_order(state.roles[Role.RETAILER], retailer_demand, config, Role.RETAILER)
    assert retailer_surge_order > 8

    # 減衰型の調整により発注は一時的に振動しつつ、第35週前後には新しい定常需要(8)へ収束する
    for _ in range(30):
        orders = {
            role: decide_bot_order(state.roles[role], peek_demand_this_week(state, config, role), config, role)
            for role in ROLE_CHAIN
        }
        state = advance_week(state, config, orders)

    for role in ROLE_CHAIN:
        demand = peek_demand_this_week(state, config, role)
        order = decide_bot_order(state.roles[role], demand, config, role)
        assert order == 8
