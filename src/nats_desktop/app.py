from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from nats_desktop.api.client import AssistantClient
from nats_desktop.window import NatsWindow

APPLICATION_ID = "dev.nats.Desktop"


class NatsApplication(Adw.Application):
    """Application object: owns the HTTP client and the main window."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APPLICATION_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._client = AssistantClient()

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = NatsWindow(application=self, client=self._client)
        window.present()

    def do_shutdown(self) -> None:
        self._client.close()
        Adw.Application.do_shutdown(self)
