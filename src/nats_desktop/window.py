from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from nats_desktop.api.client import AssistantClient, AssistantClientError, BackendStatus
from nats_desktop.async_call import call_in_thread
from nats_desktop.pages.home import HomePage


class NatsWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, client: AssistantClient) -> None:
        super().__init__(application=application, title="NATS Desktop")
        self.set_default_size(520, 480)
        self._client = client
        self._request_id = 0
        self._busy = False

        self._home = HomePage()
        self._refresh_button = Gtk.Button(
            icon_name="view-refresh-symbolic",
            tooltip_text="Check assistant status",
        )
        self._refresh_button.connect("clicked", self._on_refresh)

        header = Adw.HeaderBar()
        header.pack_end(self._refresh_button)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(self._home)
        self.set_content(toolbar)

        self.refresh_status()

    def refresh_status(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._request_id += 1
        request_id = self._request_id
        self._refresh_button.set_sensitive(False)
        self._home.show_checking()

        call_in_thread(
            self._client.get_status,
            lambda status: self._on_status(request_id, status),
            lambda error: self._on_error(request_id, error),
        )

    def _on_refresh(self, _button: Gtk.Button) -> None:
        self.refresh_status()

    def _on_status(self, request_id: int, status: BackendStatus) -> None:
        if not self._finish_request(request_id):
            return
        self._home.show_online(status, self._client.base_url)

    def _on_error(self, request_id: int, error: BaseException) -> None:
        if not self._finish_request(request_id):
            return
        if not isinstance(error, AssistantClientError):
            error = AssistantClientError(str(error) or error.__class__.__name__, "request")
        self._home.show_error(error, self._client.base_url)

    def _finish_request(self, request_id: int) -> bool:
        if request_id != self._request_id:
            return False
        self._busy = False
        self._refresh_button.set_sensitive(True)
        return True
