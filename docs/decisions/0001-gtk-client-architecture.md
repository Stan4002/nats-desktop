# 0001: GTK client with a thread-bound httpx layer

- Status: accepted
- Date: 2026-10-26

## Context

nats-desktop must be a GTK4/libadwaita application and a client of `nats-assistant`. The GTK main loop must stay interactive when the backend is down. PyGObject is provided by Ubuntu packages, while `httpx` is a normal PyPI dependency.

## Decision

1. Keep all HTTP in `nats_desktop.api.client.AssistantClient` (synchronous `httpx.Client`).
2. Run those calls on a daemon thread and deliver results with `GLib.idle_add`.
3. Create the project venv with `--system-site-packages` instead of pip-installing PyGObject.
4. G1 reads only `/v1/status`, not `/v1/home`, so tasks and calendar stay out of the first window.

## Alternatives considered

- `httpx.AsyncClient` on an asyncio loop integrated with GLib: more moving parts before we have multiple concurrent requests.
- Calling `httpx` from widget handlers: simpler, but a timeout would freeze the window.
- Pip-installing PyGObject: fights the distro GIR/GTK versions.

## Consequences

- UI code can be taught independently of HTTP error handling.
- Client tests need no display.
- The venv must always be created with `--system-site-packages`.
