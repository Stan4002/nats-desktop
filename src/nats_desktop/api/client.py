from __future__ import annotations

from dataclasses import dataclass

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_TIMEOUT_SECONDS = 3.0
CALENDAR_STATES = frozenset({"online", "offline", "not_connected", "error"})


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


@dataclass(frozen=True)
class CalendarOverview:
    status: str
    stale: bool | None
    updated_at: str | None


@dataclass(frozen=True)
class HomeOverview:
    """Fields the home screen is allowed to show from /v1/status and /v1/home."""

    status: BackendStatus
    calendar: CalendarOverview | None
    pending_tasks: int | None
    due_today: int | None
    home_error: AssistantClientError | None = None

    def with_previous_home(self, previous: HomeOverview | None) -> HomeOverview:
        """Keep last calendar/task figures when this refresh could not read /v1/home."""

        if previous is None or self.home_error is None:
            return self
        return HomeOverview(
            status=self.status,
            calendar=self.calendar if self.calendar is not None else previous.calendar,
            pending_tasks=(
                self.pending_tasks if self.pending_tasks is not None else previous.pending_tasks
            ),
            due_today=self.due_today if self.due_today is not None else previous.due_today,
            home_error=self.home_error,
        )


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
        payload = self._get_json("/v1/status")
        if (
            payload.get("service") != "nats-assistant"
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

    def fetch_overview(self) -> HomeOverview:
        """Read /v1/status, then /v1/home. Status failure means the assistant is unreachable."""

        status = self.get_status()
        try:
            payload = self._get_json("/v1/home")
        except AssistantClientError as exc:
            return HomeOverview(
                status=status,
                calendar=None,
                pending_tasks=None,
                due_today=None,
                home_error=exc,
            )
        calendar, pending, due_today = parse_home_fields(payload)
        return HomeOverview(
            status=status,
            calendar=calendar,
            pending_tasks=pending,
            due_today=due_today,
        )

    def close(self) -> None:
        self._http.close()

    def _get_json(self, path: str) -> dict:
        try:
            response = self._http.get(path)
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

        if not isinstance(payload, dict):
            raise AssistantClientError("Assistant returned an invalid payload", "response")
        return payload


def parse_home_fields(
    payload: dict,
) -> tuple[CalendarOverview | None, int | None, int | None]:
    """Pull only documented home fields. Missing or malformed optionals become None."""

    tasks = payload.get("tasks")
    pending = _optional_int(tasks.get("pending") if isinstance(tasks, dict) else None)
    due_today = _optional_int(tasks.get("due_today") if isinstance(tasks, dict) else None)

    raw_calendar = payload.get("calendar")
    if raw_calendar is None:
        return None, pending, due_today
    if not isinstance(raw_calendar, dict):
        return None, pending, due_today

    calendar_status = raw_calendar.get("status")
    if calendar_status not in CALENDAR_STATES:
        return None, pending, due_today

    stale = raw_calendar.get("stale")
    updated_at = raw_calendar.get("updated_at")
    return (
        CalendarOverview(
            status=calendar_status,
            stale=stale if isinstance(stale, bool) else None,
            updated_at=updated_at if isinstance(updated_at, str) and updated_at else None,
        ),
        pending,
        due_today,
    )


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
