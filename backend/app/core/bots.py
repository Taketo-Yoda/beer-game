from .models import GameConfig, Role, RoleState


def decide_bot_order(role_state: RoleState, demand_this_week: int, config: GameConfig, role: Role) -> int:
    """在庫ポジション（在庫-受注残+輸送/生産中+未出荷の発注残）を目標水準に近づけるorder-up-to方策で発注量を決める。

    目標水準は「初期在庫 + 直近観測需要×リードタイム」。ギャップを1期間で解消しようとすると
    発注量が発散するため、リードタイムで按分した緩やかな調整（anchoring-and-adjustment型）にし、
    需要急増時には適度な過剰発注（ブルウィップの萌芽）を起こしつつも収束する挙動にする。
    """
    if role == Role.FACTORY:
        lead_time = config.production_delay_weeks
        pipeline_orders_not_yet_shipped = 0
    else:
        lead_time = config.order_delay_weeks + config.shipping_delay_weeks
        pipeline_orders_not_yet_shipped = sum(role_state.order_history[-config.order_delay_weeks :])

    target_position = config.initial_inventory + demand_this_week * lead_time
    inventory_position = (
        role_state.inventory
        - role_state.backlog
        + sum(role_state.incoming_shipments)
        + pipeline_orders_not_yet_shipped
    )
    gap_adjustment = (target_position - inventory_position) / lead_time
    return max(0, round(demand_this_week + gap_adjustment))
