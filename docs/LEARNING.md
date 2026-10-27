# Learning log

## 2026-10-26: worker thread must actually be started

The home screen stayed on “Checking assistant…” because `call_in_thread` never ran the HTTP work.

What happens on a successful startup:

1. `NatsApplication.do_activate` creates `NatsWindow`.
2. `NatsWindow.refresh()` sets `_busy`, shows the checking page, and calls `call_in_thread(self._client.fetch_overview, ...)`.
3. `call_in_thread` starts a daemon thread. That thread calls `fetch_overview()` (not the GTK thread).
4. When the thread finishes, `GLib.idle_add(_deliver, callback, value)` runs `_deliver` on the GTK main loop.
5. `_on_overview` clears `_busy` and `HomePage.show_overview()` switches the stack from `empty` to `content`.

If step 3 is missing, the API can be healthy and you still never leave the loading page, with no traceback. `_busy` also blocks the 30-second refresh.

Read [src/nats_desktop/async_call.py](../src/nats_desktop/async_call.py) first, then [src/nats_desktop/window.py](../src/nats_desktop/window.py).

Try this yourself: comment out `threading.Thread(...).start()`, run `./.venv/bin/python -m pytest tests/test_async_call.py -q`, and watch the GLib-loop tests fail the timeout with an empty `received` list. Undo by restoring `.start()`.

## 2026-10-26: home refresh, last-good data, and /v1/home summary

The home screen now asks two questions: is the assistant process alive, and what summary does `/v1/home` currently report?

Request lifecycle:

1. `NatsWindow.refresh()` runs only when `_busy` is false. Manual clicks and the 30-second GLib timeout share that gate, so you cannot stack unbounded HTTP work.
2. A worker thread calls `AssistantClient.fetch_overview()`. That method GETs `/v1/status`, then `/v1/home`. httpx timeouts stay at 3 seconds each.
3. `call_in_thread` uses `GLib.idle_add` so widget updates happen on the GTK main thread. GTK is not thread-safe; the worker must not touch widgets.
4. On success, the page shows connection, calendar `status`/`stale`/`updated_at`, and task counts. The window stores that overview plus a local "last successful refresh" timestamp.
5. If `/v1/status` fails and we already had an overview, the previous rows stay on screen and a banner explains the failed refresh. If we never succeeded, the empty offline/error page is shown.
6. If status works but home fails, assistant identity still updates and calendar/task rows keep the previous numbers when they exist.
7. On close/destroy the window sets `_disposed` and removes the GLib timeout so later idle callbacks are ignored.

Read the files in this order:

- [src/nats_desktop/api/client.py](../src/nats_desktop/api/client.py)
- [src/nats_desktop/async_call.py](../src/nats_desktop/async_call.py)
- [src/nats_desktop/window.py](../src/nats_desktop/window.py)
- [src/nats_desktop/pages/home.py](../src/nats_desktop/pages/home.py)

Try this yourself: start `.venv/bin/nats-desktop` with the assistant running, confirm calendar state and pending count, then stop `nats-assistant` and wait for the next refresh (or press the button). The previous numbers should remain, with a banner that the latest refresh failed. The window should still accept clicks.

To undo this change, revert `fetch_overview` usage in `window.py` and go back to `/v1/status` only.

## 2026-10-26: G0 window and G1 status home

We built a small Adwaita application whose only job is to ask nats-assistant whether it is alive.

How it works:

1. `nats-desktop` starts `NatsApplication`, an `Adw.Application`. That class owns one `AssistantClient`.
2. On activate, it shows `NatsWindow`. The window builds a header bar and `HomePage`, then calls `refresh_status()`.
3. `refresh_status()` starts a background thread that runs `AssistantClient.get_status()`.
4. When the thread finishes, `GLib.idle_add` runs a callback on the GTK thread. That callback updates labels. The window never waits on the socket.
5. If nothing is listening on port 8765, httpx raises a request error, the client turns it into `AssistantClientError(kind="offline")`, and the page says the assistant is offline.

Read the files in this order:

- [src/nats_desktop/api/client.py](../src/nats_desktop/api/client.py)
- [src/nats_desktop/async_call.py](../src/nats_desktop/async_call.py)
- [src/nats_desktop/pages/home.py](../src/nats_desktop/pages/home.py)
- [src/nats_desktop/window.py](../src/nats_desktop/window.py)
- [src/nats_desktop/app.py](../src/nats_desktop/app.py)

Try this yourself: run `.venv/bin/nats-desktop`, then stop `nats-assistant` and press refresh. The window should keep accepting clicks and switch to the offline page.

To undo this milestone, remove the files under `src/nats_desktop/` and the packaging files in the project root; there is no database or service unit yet.
