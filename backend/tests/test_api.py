from fastapi.testclient import TestClient

from app.main import app
from app.rate_limit import rate_limit

# レート制限はここでは対象外(専用のtest_rate_limit.pyで検証する)。
# 有効なままだと1テストが上限(30req/分)を超え、ビジネスロジックのテストに影響するため無効化する。
app.dependency_overrides[rate_limit] = lambda: None

client = TestClient(app)


def create_game(human_role: str = "retailer") -> dict:
    response = client.post("/api/games", json={"human_role": human_role})
    assert response.status_code == 200
    return response.json()


def test_create_game_returns_initial_state():
    game = create_game("retailer")

    assert game["week"] == 0
    assert not game["is_finished"]
    assert game["human_role"] == "retailer"
    assert game["you"]["inventory"] == 12
    assert game["you"]["backlog"] == 0
    assert game["demand_to_decide"] == 4


def test_get_game_returns_same_state():
    created = create_game("wholesaler")
    response = client.get(f"/api/games/{created['game_id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_game_returns_404():
    response = client.get("/api/games/does-not-exist")
    assert response.status_code == 404


def test_submitting_negative_order_is_rejected():
    game = create_game("retailer")
    response = client.post(f"/api/games/{game['game_id']}/orders", json={"order": -1})
    assert response.status_code == 422


def test_submit_order_advances_one_week():
    game = create_game("retailer")
    response = client.post(f"/api/games/{game['game_id']}/orders", json={"order": 4})

    assert response.status_code == 200
    updated = response.json()
    assert updated["week"] == 1
    assert updated["you"]["order_history"] == [4]
    assert updated["you"]["inventory"] == 12
    assert updated["you"]["backlog"] == 0


def test_debrief_unavailable_until_game_finishes():
    game = create_game("retailer")
    response = client.get(f"/api/games/{game['game_id']}/debrief")
    assert response.status_code == 400


def test_full_game_reaches_debrief_and_shows_bullwhip_amplification():
    game = create_game("retailer")
    game_id = game["game_id"]
    total_weeks = game["total_weeks"]

    state = game
    for _ in range(total_weeks):
        response = client.post(f"/api/games/{game_id}/orders", json={"order": state["demand_to_decide"]})
        assert response.status_code == 200
        state = response.json()

    assert state["is_finished"]

    orders_response = client.post(f"/api/games/{game_id}/orders", json={"order": 4})
    assert orders_response.status_code == 400

    debrief_response = client.get(f"/api/games/{game_id}/debrief")
    assert debrief_response.status_code == 200
    debrief = debrief_response.json()

    assert debrief["weeks_played"] == total_weeks
    assert len(debrief["customer_demand"]) == total_weeks
    assert {r["role"] for r in debrief["roles"]} == {"factory", "distributor", "wholesaler", "retailer"}

    # ブルウィップ効果: 需要変動の振れ幅は上流(工場)ほど下流(小売)より大きくなる
    def order_swing(role: str) -> int:
        history = next(r["order_history"] for r in debrief["roles"] if r["role"] == role)
        return max(history) - min(history)

    assert order_swing("factory") >= order_swing("retailer")
