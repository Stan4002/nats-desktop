# NATS Desktop

GTK4 / libadwaita client for the local [NATS Assistant](../../python/nats-assistant) API.

This application does not store assistant data. `nats-assistant` on `http://127.0.0.1:8765` remains the source of truth. NATS HUD stays a separate GNOME Shell presentation layer.

## Current milestone

G0 + G1: a launchable `Adw.ApplicationWindow` with a home screen that checks `GET /v1/status`, shows connection state, and stays responsive if the backend is offline.

Tasks, calendar, chat, and `/v1/home` content are out of scope.

## Architecture

```
window / pages  →  worker thread  →  AssistantClient (httpx)  →  127.0.0.1:8765
```

Widgets never call `httpx`. The GTK main loop never waits on the network.

## System packages

PyGObject, GTK 4, and libadwaita must come from the distro. They are already installed on this machine as:

- `python3-gi`
- `python3-gi-cairo`
- `gir1.2-gtk-4.0`
- `gir1.2-adw-1`

If you reinstall them:

```bash
sudo apt install python3 python3-venv python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

## Setup

Create the venv with **system site packages** so `import gi` can see GTK. Use the distro Python, not the `nats-assistant` venv:

```bash
cd /home/nats/Projects/software/desktop/nats-desktop
/usr/bin/python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
```

Confirm GTK is visible:

```bash
.venv/bin/python -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1'); from gi.repository import Gtk, Adw; print(Gtk.MAJOR_VERSION, Adw.MAJOR_VERSION)"
```

## Run

The assistant service should already be running for a connected view:

```bash
curl http://127.0.0.1:8765/v1/status
.venv/bin/nats-desktop
```

To test the offline path, stop the assistant (or simply run the app when nothing is listening on 8765). The window should still open immediately and then show "Assistant is offline".

## Tests

```bash
.venv/bin/python -m pytest -q
```

These tests cover the HTTP client with a mock transport. They do not open a window and do not contact the real backend.
