# Known bugs and fixes

## 2026-10-26: home screen stuck on “Checking assistant…”

- Symptom: the window opened on the loading page and never left it, even when `/v1/status` and `/v1/home` returned HTTP 200. The launch terminal printed nothing.
- Cause: `call_in_thread` defined a worker `runner` but never started it. `threading.Thread(...).start()` had been left after `return False` inside `_deliver`, so it was unreachable. `NatsWindow.refresh()` still set `_busy` and showed the checking page, then waited forever for a callback that could not run. The 30s timer could not help because `_busy` stayed true.
- Fix: start the daemon thread at the end of `call_in_thread`. Tests now require `.start()` in that function and wait on the GLib loop for success and error delivery.
- Verification: `./.venv/bin/python -m pytest -q` (including `tests/test_async_call.py`). A short Adw probe with a mock transport switched the stack from `empty` to `content`. Full interactive GUI still needs a manual launch.

## 2026-10-26: refresh wiped the last good home details

- Symptom: pressing refresh or losing the backend replaced service/version with "…" or em dashes, even after a successful check.
- Cause: `show_checking()` and `show_error()` always rewrote the detail rows. There was no in-memory last overview.
- Fix: keep `HomeOverview` on the window. A later failure shows a banner and leaves the previous rows in place. The empty status page is only used before the first success.
- Verification: client tests cover merging a previous overview after a home error. GTK rendering was not automated.

## 2026-10-26: GLib timeout was never removed

- Symptom: none reported yet; closing the window left a 30s source that could fire after dispose.
- Cause: G0/G1 had no interval source. Adding one without `source_remove` would leak callbacks.
- Fix: `close-request` and `destroy` both call `_cleanup_sources()`, which removes the timeout and ignores later idle deliveries.
- Verification: code inspection; no graphical shutdown test.
