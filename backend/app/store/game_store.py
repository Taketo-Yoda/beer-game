import uuid
from dataclasses import dataclass

from ..core.engine import create_initial_state
from ..core.models import GameConfig, GameState, Role


@dataclass
class StoredGame:
    game_id: str
    human_role: Role
    config: GameConfig
    state: GameState


_MAX_STORED_GAMES = 1000


class GameStore:
    """ゲーム状態の永続化層。Phase 1ではプロセス内メモリのdictで十分だが、
    将来Redis/DBへ差し替えられるようインターフェースをこのクラスに閉じ込める。"""

    def __init__(self) -> None:
        self._games: dict[str, StoredGame] = {}

    def create(self, human_role: Role, config: GameConfig) -> StoredGame:
        # 際限のないメモリ増加を防ぐため、上限を超えたら最も古いゲームから破棄する
        if len(self._games) >= _MAX_STORED_GAMES:
            oldest_game_id = next(iter(self._games))
            del self._games[oldest_game_id]

        game_id = str(uuid.uuid4())
        game = StoredGame(
            game_id=game_id,
            human_role=human_role,
            config=config,
            state=create_initial_state(config),
        )
        self._games[game_id] = game
        return game

    def get(self, game_id: str) -> StoredGame:
        game = self._games.get(game_id)
        if game is None:
            raise KeyError(game_id)
        return game

    def update_state(self, game_id: str, new_state: GameState) -> StoredGame:
        game = self.get(game_id)
        game.state = new_state
        return game


_store = GameStore()


def get_game_store() -> GameStore:
    return _store
