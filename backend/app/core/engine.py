from .models import ROLE_CHAIN, GameConfig, GameState, Role, RoleState, downstream_of, upstream_of


def create_initial_state(config: GameConfig) -> GameState:
    """定常状態（需要急増前の一定需要）からゲームを開始する初期状態を作る。"""
    steady_demand = config.customer_demand[0] if config.customer_demand else 0

    roles: dict[Role, RoleState] = {}
    for role in ROLE_CHAIN:
        # FACTORYは自分の生産指示で自分の入荷パイプラインを賄う点だけが特殊(shipment_len)。
        # incoming_orders（一次卸からの受注キュー）は他役割と同じ扱いが必要。
        shipment_len = config.production_delay_weeks if role == Role.FACTORY else config.shipping_delay_weeks
        order_len = config.order_delay_weeks

        roles[role] = RoleState(
            inventory=config.initial_inventory,
            backlog=0,
            incoming_shipments=tuple(steady_demand for _ in range(shipment_len)),
            incoming_orders=tuple(steady_demand for _ in range(order_len)),
            last_order_placed=steady_demand,
            # order_history もbotの在庫ポジション計算が初週から一貫するよう定常需要で種付けする
            order_history=tuple(steady_demand for _ in range(order_len)),
        )

    return GameState(week=0, roles=roles, is_finished=False)


def peek_demand_this_week(state: GameState, config: GameConfig, role: Role) -> int:
    """次に処理される週で各役割が受け取る需要（下流の発注、小売なら顧客需要）を、出荷判断より前に確認する。"""
    if state.is_finished:
        raise ValueError("game already finished")
    if role == Role.RETAILER:
        return config.customer_demand[state.week]
    rs = state.roles[role]
    return rs.incoming_orders[0] if rs.incoming_orders else 0


def advance_week(state: GameState, config: GameConfig, orders: dict[Role, int]) -> GameState:
    """入荷→受注確認→出荷→コスト加算→発注 の順に1週間分を全役割へ適用し、新しいGameStateを返す。"""
    if state.is_finished:
        raise ValueError("game already finished")
    missing = [role for role in ROLE_CHAIN if role not in orders]
    if missing:
        raise ValueError(f"missing orders for roles: {missing}")
    for role, qty in orders.items():
        if qty < 0:
            raise ValueError(f"order quantity must be non-negative: {role}={qty}")

    next_week = state.week + 1
    customer_demand = config.customer_demand[next_week - 1]

    # Phase 1: 入荷（輸送/生産パイプラインの先頭を在庫へ）
    stage1: dict[Role, RoleState] = {}
    for role, rs in state.roles.items():
        arrived = rs.incoming_shipments[0] if rs.incoming_shipments else 0
        stage1[role] = rs.model_copy(
            update={
                "inventory": rs.inventory + arrived,
                "incoming_shipments": rs.incoming_shipments[1:],
                "last_shipment_received": arrived,
            }
        )

    # Phase 2: 受注確認（発注伝達パイプラインの先頭を取得。小売は顧客需要をそのまま使う）
    demand_this_week: dict[Role, int] = {}
    stage2: dict[Role, RoleState] = {}
    for role, rs in stage1.items():
        if role == Role.RETAILER:
            demand_this_week[role] = customer_demand
            stage2[role] = rs
        else:
            demand_this_week[role] = rs.incoming_orders[0] if rs.incoming_orders else 0
            stage2[role] = rs.model_copy(update={"incoming_orders": rs.incoming_orders[1:]})

    # Phase 3: 出荷（在庫の範囲で受注残+今週の需要を充足、不足分は受注残に計上）
    shipped: dict[Role, int] = {}
    stage3: dict[Role, RoleState] = {}
    for role, rs in stage2.items():
        total_demand = rs.backlog + demand_this_week[role]
        ship_qty = min(rs.inventory, total_demand)
        shipped[role] = ship_qty
        stage3[role] = rs.model_copy(
            update={
                "inventory": rs.inventory - ship_qty,
                "backlog": total_demand - ship_qty,
            }
        )

    # Phase 4: コスト加算、履歴記録
    stage4: dict[Role, RoleState] = {}
    for role, rs in stage3.items():
        cost = rs.inventory * config.holding_cost_per_unit + rs.backlog * config.backorder_cost_per_unit
        stage4[role] = rs.model_copy(
            update={
                "last_week_cost": cost,
                "cumulative_cost": rs.cumulative_cost + cost,
                "inventory_history": rs.inventory_history + (rs.inventory,),
                "backlog_history": rs.backlog_history + (rs.backlog,),
            }
        )

    # Phase 5a: 出荷した数量を下流の入荷パイプラインへ積む
    stage5: dict[Role, RoleState] = dict(stage4)
    for role in ROLE_CHAIN:
        down = downstream_of(role)
        if down is not None:
            rs = stage5[down]
            stage5[down] = rs.model_copy(
                update={"incoming_shipments": rs.incoming_shipments + (shipped[role],)}
            )

    # Phase 5b: 新規発注を記録し、上流の受注パイプラインへ積む（工場は生産指示として自分の入荷パイプラインへ直接積む）
    for role in ROLE_CHAIN:
        order_qty = orders[role]
        rs = stage5[role].model_copy(
            update={
                "order_history": stage5[role].order_history + (order_qty,),
                "last_order_placed": order_qty,
            }
        )
        if role == Role.FACTORY:
            stage5[role] = rs.model_copy(
                update={"incoming_shipments": rs.incoming_shipments + (order_qty,)}
            )
        else:
            stage5[role] = rs
            up = upstream_of(role)
            assert up is not None
            rs_up = stage5[up]
            stage5[up] = rs_up.model_copy(
                update={"incoming_orders": rs_up.incoming_orders + (order_qty,)}
            )

    is_finished = next_week >= config.total_weeks
    return GameState(week=next_week, roles=stage5, is_finished=is_finished)
