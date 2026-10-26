# Learning log

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
