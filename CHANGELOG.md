# Changelog

## Unreleased

- Fix the home screen staying on “Checking assistant…” because the refresh worker thread was never started.
- Show calendar connection, stale/update time, and task counts from `/v1/home` on the home screen.
- Refresh every 30 seconds, refuse overlapping requests, and keep the last successful summary when a later refresh fails.

## 0.1.0

- Add a launchable GTK4/libadwaita window that checks `GET /v1/status` off the UI thread and shows connected or offline state.
