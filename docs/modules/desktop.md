# Module: desktop client (G0/G1)

## Purpose

Native Linux window that talks to `nats-assistant` as a client. G0 is the application shell. G1 is a status-only home screen.

## Data

None stored here. The only payload read is `/v1/status`:

```json
{"service": "nats-assistant", "status": "online", "version": "0.1.0"}
```

## Endpoints used

- `GET http://127.0.0.1:8765/v1/status`

Not used yet: `/v1/home`, `/v1/tasks`, `/v1/captures`.

## Privacy

Requests stay on loopback. Status JSON contains no private user data. Nothing is logged.

## Known issues

- The window needs a graphical session (Wayland/X11). Tests do not cover widget rendering.
- A stale in-flight check is ignored via a request id, but the HTTP call still runs to completion.
