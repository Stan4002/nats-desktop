from __future__ import annotations

from dataclasses import dataclass

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_TIMEOUT_SECONDS = 3.0


class AssistantClientError(Exception):
    """Transport or payload failure talking to nats-assistant."""

    def __init__(self, message: str, kind: str = "request") -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class BackendStatus:
    service: str
    status: str
    version: str


class AssistantClient:
    """Synchronous HTTP client for the assistant API.

    Call this from a worker thread. GTK widgets must not use it directly.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
        )

    def get_status(self) -> BackendStatus:
        try:
            response = self._http.get("/v1/status")
        except httpx.TimeoutException as exc:
            raise AssistantClientError("Assistant did not respond in time", "offline") from exc
        except httpx.RequestError as exc:
            raise AssistantClientError("Cannot reach nats-assistant", "offline") from exc

        if response.status_code != 200:
            raise AssistantClientError(
                f"Assistant returned HTTP {response.status_code}",
                "http",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise AssistantClientError("Assistant returned invalid JSON", "response") from exc

        if (
            not isinstance(payload, dict)
            or payload.get("service") != "nats-assistant"
            or payload.get("status") != "online"
            or not isinstance(payload.get("version"), str)
            or not payload["version"]
        ):
            raise AssistantClientError("Assistant returned an invalid status", "response")

        return BackendStatus(
            service=payload["service"],
            status=payload["status"],
            version=payload["version"],
        )

    def close(self) -> None:
        self._http.close()
