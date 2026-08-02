import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.rate_limit import _MAX_REQUESTS_PER_WINDOW, _request_log, rate_limit


def make_request(client_ip: str) -> Request:
    return Request({"type": "http", "client": (client_ip, 12345), "headers": []})


def test_allows_requests_up_to_the_threshold():
    _request_log.clear()
    request = make_request("1.2.3.4")
    for _ in range(_MAX_REQUESTS_PER_WINDOW):
        rate_limit(request)  # raises on failure


def test_blocks_requests_beyond_the_threshold():
    _request_log.clear()
    request = make_request("5.6.7.8")
    for _ in range(_MAX_REQUESTS_PER_WINDOW):
        rate_limit(request)

    with pytest.raises(HTTPException) as exc_info:
        rate_limit(request)
    assert exc_info.value.status_code == 429


def test_tracks_each_ip_independently():
    _request_log.clear()
    heavy_client = make_request("9.9.9.9")
    other_client = make_request("8.8.8.8")

    for _ in range(_MAX_REQUESTS_PER_WINDOW):
        rate_limit(heavy_client)

    rate_limit(other_client)  # 別IPなので上限に達していても拒否されない
