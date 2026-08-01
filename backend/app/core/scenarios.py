from .models import GameConfig


def classic_customer_demand(
    total_weeks: int,
    initial_demand: int = 4,
    surge_week: int = 5,
    surge_demand: int = 8,
) -> tuple[int, ...]:
    """古典的なビールゲームの需要シナリオ（第1〜(surge_week-1)週は一定、以降は急増）を生成する。"""
    return tuple(
        surge_demand if week >= surge_week else initial_demand
        for week in range(1, total_weeks + 1)
    )


def default_config(total_weeks: int = 36) -> GameConfig:
    return GameConfig(
        total_weeks=total_weeks,
        customer_demand=classic_customer_demand(total_weeks),
    )
