# AGENTS.md — rules for AI coding agents

Put this file at the ROOT of the repo. Agents read it before working.

## Project
NATS is a personal assistant ecosystem running locally on Ubuntu (GNOME, Wayland):
- `nats-assistant`: Python/FastAPI backend, SQLite, systemd user service on 127.0.0.1:8765. It owns ALL data and logic.
- `nats-hud`: GNOME Shell extension. Presentation only.
- `nats-desktop` (this repo): GTK4/libadwaita desktop client of the assistant API.

Architecture rules that must not be broken:
1. Backend is the only owner of data. This app displays state and will later send intents. It is not a second backend.
2. Do not modify `nats-assistant` or `nats-hud` from this project.
3. UI widgets must not make HTTP calls. All assistant traffic goes through `nats_desktop.api`.
4. HTTP work must not run on the GTK main loop. A blocked UI is a bug.
5. Local only: talk to loopback (`http://127.0.0.1:8765` by default). No cloud calls unless a task explicitly says so.
6. Never send messages, emails or reply on the user's behalf.
7. Private data is never logged.

## Git workflow (strict)
- Never commit to `main`. Create a branch from an up-to-date `main`: `feature/<short-name>` or `fix/<short-name>`.
- Small commits, one idea each, message format `type: what and why` (feat, fix, docs, test, refactor).
- Do not push, merge, rebase, force-push or delete branches. Stop and tell the user the branch is ready for review.
- Do not touch files outside the task's scope.

## Quality
- Python >=3.11 compatible. GTK/libadwaita come from system packages (`python3-gi`), not PyPI.
- The virtualenv must be created with `--system-site-packages` so PyGObject can see GTK 4 and libadwaita.
- Run before finishing: `python -m pytest -q` (from this project's venv).
- New behaviour needs tests, including the failure path. Prefer testing the HTTP client without a display.
- Prefer small readable code over clever code. The owner is learning and must be able to follow it.

## Documentation duty (the owner wants to learn and reverse engineer everything)
For EVERY task, before finishing, create or update:
1. `docs/modules/<name>.md` — purpose, data, endpoints, privacy, known issues.
2. `docs/decisions/NNNN-<title>.md` — an ADR for each real choice (why X over Y, what we gave up).
3. `docs/LEARNING.md` — add a dated entry: what was built, how it works step by step, which files to read in what order, one thing to try yourself, and how to undo it.
4. `CHANGELOG.md` — one line per user-visible change.
5. `docs/BUGS.md` — any bug hit: symptom, cause, fix, how it was verified.
6. Comments explain WHY, not WHAT. Name things plainly.

## When unsure
Stop and ask. Do not guess about auth, data deletion, or anything touching the user's accounts.

## Useful commands
```
source .venv/bin/activate
python -m pytest -q
nats-desktop
curl http://127.0.0.1:8765/v1/status
```
