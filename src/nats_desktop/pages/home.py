from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from nats_desktop.api.client import AssistantClientError, BackendStatus


class HomePage(Gtk.Box):
    """Status-only home view. It never talks to the network itself."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._status_page = Adw.StatusPage(
            icon_name="network-idle-symbolic",
            title="Checking assistant…",
            description="Looking for nats-assistant on 127.0.0.1:8765.",
        )
        self._status_page.set_vexpand(True)

        self._service_row = Adw.ActionRow(title="Service")
        self._status_row = Adw.ActionRow(title="Status")
        self._version_row = Adw.ActionRow(title="Version")
        self._endpoint_row = Adw.ActionRow(title="Endpoint", subtitle="http://127.0.0.1:8765")

        group = Adw.PreferencesGroup(title="Connection")
        group.add(self._service_row)
        group.add(self._status_row)
        group.add(self._version_row)
        group.add(self._endpoint_row)

        clamp = Adw.Clamp(maximum_size=480, tightening_threshold=300)
        clamp.set_child(group)

        self.append(self._status_page)
        self.append(clamp)
        self.show_checking()

    def show_checking(self) -> None:
        self._status_page.set_icon_name("network-idle-symbolic")
        self._status_page.set_title("Checking assistant…")
        self._status_page.set_description("Looking for nats-assistant on 127.0.0.1:8765.")
        self._set_details("…", "checking", "…")

    def show_online(self, status: BackendStatus, endpoint: str) -> None:
        self._status_page.set_icon_name("network-transmit-receive-symbolic")
        self._status_page.set_title("Connected")
        self._status_page.set_description("nats-assistant is online.")
        self._endpoint_row.set_subtitle(endpoint)
        self._set_details(status.service, status.status, status.version)

    def show_error(self, error: AssistantClientError, endpoint: str) -> None:
        if error.kind == "offline":
            icon = "network-offline-symbolic"
            title = "Assistant is offline"
        else:
            icon = "dialog-warning-symbolic"
            title = "Could not read assistant status"
        self._status_page.set_icon_name(icon)
        self._status_page.set_title(title)
        self._status_page.set_description(str(error))
        self._endpoint_row.set_subtitle(endpoint)
        self._set_details("—", error.kind, "—")

    def _set_details(self, service: str, status: str, version: str) -> None:
        self._service_row.set_subtitle(service)
        self._status_row.set_subtitle(status)
        self._version_row.set_subtitle(version)
