# Known bugs and fixes

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
