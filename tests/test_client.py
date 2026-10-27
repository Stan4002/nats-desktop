from __future__ import annotations

import httpx
import pytest

from nats_desktop.api.client import (
    AssistantClient,
    AssistantClientError,
    BackendStatus,
    CalendarOverview,
    HomeOverview,
    parse_home_fields,
)


def _client(handler) -> AssistantClient:
    return AssistantClient(transport=httpx.MockTransport(handler))


def _status_json() -> dict:
    return {"service": "nats-assistant", "status": "online", "version": "0.1.0"}


def _home_json(**overrides: object) -> dict:
    payload: dict = {
        "tasks": {"pending": 3, "due_today": 1, "items": []},
        "calendar": {
            "status": "online",
            "today_count": 2,
            "next": None,
            "events": [],
            "truncated": False,
            "updated_at": "2026-10-26T01:00:00+00:00",
            "stale": False,
        },
    }
    payload.update(overrides)
    return payload


def _router(status=None, home=None, home_error: Exception | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/status":
            if isinstance(status, Exception):
                raise status
            return httpx.Response(200, json=status or _status_json())
        if request.url.path == "/v1/home":
            if home_error is not None:
                raise home_error
            if isinstance(home, httpx.Response):
                return home
            return httpx.Response(200, json=home if home is not None else _home_json())
        return httpx.Response(404)

    return handler


def test_get_status_returns_backend_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/status"
        return httpx.Response(200, json=_status_json())

    status = _client(handler).get_status()
    assert status == BackendStatus(service="nats-assistant", status="online", version="0.1.0")


def test_get_status_maps_connection_failure_to_offline() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(AssistantClientError) as caught:
        _client(handler).get_status()
    assert caught.value.kind == "offline"


def test_get_status_maps_timeout_to_offline() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(AssistantClientError) as caught:
        _client(handler).get_status()
    assert caught.value.kind == "offline"


def test_get_status_rejects_http_errors() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "unavailable"})

    with pytest.raises(AssistantClientError) as caught:
        _client(handler).get_status()
    assert caught.value.kind == "http"


def test_get_status_rejects_invalid_payload() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"service": "other", "status": "online", "version": "1"})

    with pytest.raises(AssistantClientError) as caught:
        _client(handler).get_status()
    assert caught.value.kind == "response"


def test_fetch_overview_reads_status_and_home() -> None:
    overview = _client(_router()).fetch_overview()
    assert overview.status.version == "0.1.0"
    assert overview.pending_tasks == 3
    assert overview.due_today == 1
    assert overview.calendar == CalendarOverview(
        status="online",
        stale=False,
        updated_at="2026-10-26T01:00:00+00:00",
    )
    assert overview.home_error is None


def test_fetch_overview_offline_status_does_not_require_home() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(AssistantClientError) as caught:
        _client(handler).fetch_overview()
    assert caught.value.kind == "offline"


def test_fetch_overview_keeps_status_when_home_times_out() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/status":
            return httpx.Response(200, json=_status_json())
        raise httpx.ReadTimeout("timed out", request=request)

    overview = _client(handler).fetch_overview()
    assert overview.status.status == "online"
    assert overview.calendar is None
    assert overview.pending_tasks is None
    assert overview.home_error is not None
    assert overview.home_error.kind == "offline"


def test_fetch_overview_keeps_status_when_home_returns_http_error() -> None:
    overview = _client(_router(home=httpx.Response(500, json={"detail": "broken"}))).fetch_overview()
    assert overview.status.service == "nats-assistant"
    assert overview.home_error is not None
    assert overview.home_error.kind == "http"


def test_fetch_overview_maps_missing_optional_home_fields() -> None:
    overview = _client(_router(home={"now": None})).fetch_overview()
    assert overview.calendar is None
    assert overview.pending_tasks is None
    assert overview.due_today is None
    assert overview.home_error is None


def test_parse_home_fields_accepts_null_calendar_update() -> None:
    calendar, pending, due_today = parse_home_fields(
        {
            "tasks": {"pending": 0, "due_today": 0},
            "calendar": {
                "status": "not_connected",
                "stale": False,
                "updated_at": None,
            },
        }
    )
    assert pending == 0
    assert due_today == 0
    assert calendar == CalendarOverview(status="not_connected", stale=False, updated_at=None)


def test_parse_home_fields_ignores_unknown_calendar_status() -> None:
    calendar, pending, _due = parse_home_fields(
        {"tasks": {"pending": 2}, "calendar": {"status": "mystery", "stale": True}}
    )
    assert calendar is None
    assert pending == 2


def test_overview_keeps_previous_home_on_home_error() -> None:
    previous = HomeOverview(
        status=BackendStatus("nats-assistant", "online", "0.1.0"),
        calendar=CalendarOverview("online", True, "2026-10-26T01:00:00+00:00"),
        pending_tasks=4,
        due_today=1,
    )
    incoming = HomeOverview(
        status=BackendStatus("nats-assistant", "online", "0.1.0"),
        calendar=None,
        pending_tasks=None,
        due_today=None,
        home_error=AssistantClientError("Assistant did not respond in time", "offline"),
    )
    merged = incoming.with_previous_home(previous)
    assert merged.calendar == previous.calendar
    assert merged.pending_tasks == 4
    assert merged.home_error is incoming.home_error
