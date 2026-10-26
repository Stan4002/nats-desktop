from __future__ import annotations

from datetime import datetime

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk

from nats_desktop.api.client import AssistantClient, AssistantClientError, HomeOverview
from nats_desktop.async_call import call_in_thread
from nats_desktop.pages.home import HomePage

REFRESH_INTERVAL_SECONDS = 30


class NatsWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, client: AssistantClient) -> None:
        super().__init__(application=application, title="NATS Desktop")
        self.set_default_size(560, 640)
        self._client = client
        self._request_id = 0
        self._busy = False
        self._disposed = False
        self._overview: HomeOverview | None = None
        self._last_success: datetime | None = None

        self._home = HomePage()
        self._spinner = Gtk.Spinner()
        self._refresh_button = Gtk.Button(
            icon_name="view-refresh-symbolic",
            tooltip_text="Refresh assistant status",
        )
        self._refresh_button.connect("clicked", self._on_refresh)

        header = Adw.HeaderBar()
        header.pack_start(self._spinner)
        header.pack_end(self._refresh_button)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(self._home)
        self.set_content(toolbar)

        self._timeout_id = GLib.timeout_add_seconds(REFRESH_INTERVAL_SECONDS, self._on_interval)
        self.connect("close-request", self._on_close_request)
        self.connect("destroy", self._on_destroy)
        self.refresh()

    def refresh(self) -> None:
        if self._busy or self._disposed:
            return
        self._busy = True
        self._request_id += 1
        request_id = self._request_id
        self._refresh_button.set_sensitive(False)
        self._spinner.start()
        if self._overview is None:
            self._home.show_checking()

        call_in_thread(
            self._client.fetch_overview,
            lambda overview: self._on_overview(request_id, overview),
            lambda error: self._on_error(request_id, error),
        )

    def _on_refresh(self, _button: Gtk.Button) -> None:
        self.refresh()

    def _on_interval(self) -> bool:
        if self._disposed:
            return False
        self.refresh()
        return True

    def _on_overview(self, request_id: int, overview: HomeOverview) -> None:
        if not self._finish_request(request_id):
            return
        merged = overview.with_previous_home(self._overview)
        self._overview = merged
        self._last_success = datetime.now().astimezone()
        self._home.show_overview(
            merged,
            self._client.base_url,
            self._last_success,
        )

    def _on_error(self, request_id: int, error: BaseException) -> None:
        if not self._finish_request(request_id):
            return
        if not isinstance(error, AssistantClientError):
            error = AssistantClientError(str(error) or error.__class__.__name__, "request")
        if self._overview is None:
            self._home.show_unavailable(error, self._client.base_url)
            return
        self._home.show_overview(
            self._overview,
            self._client.base_url,
            self._last_success,
            failure=error,
        )

    def _finish_request(self, request_id: int) -> bool:
        if self._disposed or request_id != self._request_id:
            return False
        self._busy = False
        self._refresh_button.set_sensitive(True)
        self._spinner.stop()
        return True

    def _on_close_request(self, *_args) -> bool:
        self._cleanup_sources()
        return False

    def _on_destroy(self, *_args) -> None:
        self._cleanup_sources()

    def _cleanup_sources(self) -> None:
        self._disposed = True
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0
