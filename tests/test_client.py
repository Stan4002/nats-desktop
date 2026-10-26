from __future__ import annotations

import httpx
import pytest

from nats_desktop.api.client import AssistantClient, AssistantClientError, BackendStatus


def _client(handler) -> AssistantClient:
    return AssistantClient(transport=httpx.MockTransport(handler))


def test_get_status_returns_backend_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/status"
        return httpx.Response(
            200,
            json={"service": "nats-assistant", "status": "online", "version": "0.1.0"},
        )

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
