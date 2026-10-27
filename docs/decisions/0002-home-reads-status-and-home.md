# 0002: home screen reads /v1/status and /v1/home

- Status: accepted
- Date: 2026-10-26

## Context

G0/G1 only called `/v1/status`, so the window could not show calendar connection or task counts that the backend already exposes. The home route is the documented summary for those fields. Building a second calendar or task module in the desktop app would duplicate backend logic.

## Decision

`AssistantClient.fetch_overview()` calls `/v1/status` first, then `/v1/home`. The window shows only existing summary fields: assistant service/status/version, calendar `status` / `stale` / `updated_at`, and task `pending` / `due_today`. Event lists, capture text, and comms stay unused.

If `/v1/status` fails, the assistant is treated as unreachable. If status succeeds and home fails, assistant identity is still shown and the last good calendar/task figures are kept.

## Consequences

- One worker thread does two short loopback GETs; the GTK loop still does not wait on I/O.
- Older or partial home payloads are safe: missing optionals render as "—".
- We still are not a task or calendar client. Those remain later work.
