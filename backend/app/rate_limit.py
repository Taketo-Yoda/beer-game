import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_WINDOW_SECONDS = 60
_MAX_REQUESTS_PER_WINDOW = 30

_request_log: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    """同一IPからの過度なリクエストを防ぐ簡易レート制限(1分あたり30リクエストまで)。

    プロセス内メモリで管理するため、複数インスタンスにスケールする場合は
    共有ストア(例: Redis)への差し替えが必要になる。
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    log = _request_log[client_ip]

    while log and now - log[0] > _WINDOW_SECONDS:
        log.popleft()

    if len(log) >= _MAX_REQUESTS_PER_WINDOW:
        raise HTTPException(status_code=429, detail="too many requests, please slow down")

    log.append(now)
