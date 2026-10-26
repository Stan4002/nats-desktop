# Module: desktop client (home reliability)

## Purpose

Native Linux window that talks to `nats-assistant` as a client. The home screen shows whether the assistant is reachable and the summary fields already provided by `/v1/status` and `/v1/home`.

## Data

Nothing is stored here. Last successful values are kept only in memory for the current window.

`GET /v1/status`:

```json
{"service": "nats-assistant", "status": "online", "version": "0.1.0"}
```

`GET /v1/home` fields the window may display:

- `tasks.pending` (int)
- `tasks.due_today` (int)
- `calendar.status` (`online`, `offline`, `not_connected`, `error`)
- `calendar.stale` (bool)
- `calendar.updated_at` (ISO timestamp or null)

Task items, calendar events, captures, and comms are not shown.

Last successful refresh time is local to the window, not an API field.

## Endpoints used

- `GET http://127.0.0.1:8765/v1/status`
- `GET http://127.0.0.1:8765/v1/home`

Not used: `/v1/tasks`, `/v1/captures`.

## Privacy

Requests stay on loopback. The home screen does not print task titles, event descriptions, or other private payload fields. Nothing is logged.

## Known issues

- The window needs a graphical session (Wayland/X11). Tests cover the HTTP client, not widget rendering.
- A skipped refresh (already busy) still lets the in-flight HTTP calls finish; only the matching request id may update the widgets.
- Closing the window marks it disposed and removes the 30s GLib timeout; a worker that finishes later is ignored.
