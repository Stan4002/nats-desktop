from __future__ import annotations

from datetime import datetime

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from nats_desktop.api.client import AssistantClientError, HomeOverview


def format_timestamp(value: str | datetime | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        moment = value
    else:
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    if moment.tzinfo is not None:
        moment = moment.astimezone()
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def _label(value: str | int | None) -> str:
    if value is None:
        return "—"
    return str(value)


def _state_label(value: str | None) -> str:
    if not value:
        return "—"
    return value.replace("_", " ").capitalize()


class HomePage(Gtk.Box):
    """Home view. It never talks to the network itself."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._banner = Adw.Banner()
        self._banner.set_revealed(False)

        self._status_page = Adw.StatusPage(
            icon_name="network-idle-symbolic",
            title="Checking assistant…",
            description="Looking for nats-assistant on 127.0.0.1:8765.",
        )

        self._assistant_row = Adw.ActionRow(title="Assistant")
        self._service_row = Adw.ActionRow(title="Service")
        self._version_row = Adw.ActionRow(title="Version")
        self._endpoint_row = Adw.ActionRow(title="Endpoint")
        self._refreshed_row = Adw.ActionRow(title="Last successful refresh")

        connection = Adw.PreferencesGroup(title="Connection")
        connection.add(self._assistant_row)
        connection.add(self._service_row)
        connection.add(self._version_row)
        connection.add(self._endpoint_row)
        connection.add(self._refreshed_row)

        self._calendar_state_row = Adw.ActionRow(title="Connection")
        self._calendar_stale_row = Adw.ActionRow(title="Data")
        self._calendar_updated_row = Adw.ActionRow(title="Updated")
        calendar = Adw.PreferencesGroup(title="Calendar")
        calendar.add(self._calendar_state_row)
        calendar.add(self._calendar_stale_row)
        calendar.add(self._calendar_updated_row)

        self._pending_row = Adw.ActionRow(title="Pending")
        self._due_today_row = Adw.ActionRow(title="Due today")
        tasks = Adw.PreferencesGroup(title="Tasks")
        tasks.add(self._pending_row)
        tasks.add(self._due_today_row)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content.set_margin_top(12)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.append(connection)
        content.append(calendar)
        content.append(tasks)

        clamp = Adw.Clamp(maximum_size=560, tightening_threshold=360)
        clamp.set_child(content)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_child(clamp)

        self._stack = Gtk.Stack()
        self._stack.set_vexpand(True)
        self._stack.add_named(self._status_page, "empty")
        self._stack.add_named(scrolled, "content")

        self.append(self._banner)
        self.append(self._stack)
        self.show_checking()

    def show_checking(self) -> None:
        self._banner.set_revealed(False)
        self._status_page.set_icon_name("network-idle-symbolic")
        self._status_page.set_title("Checking assistant…")
        self._status_page.set_description("Looking for nats-assistant on 127.0.0.1:8765.")
        self._stack.set_visible_child_name("empty")

    def show_unavailable(self, error: AssistantClientError, endpoint: str) -> None:
        self._banner.set_revealed(False)
        if error.kind == "offline":
            self._status_page.set_icon_name("network-offline-symbolic")
            self._status_page.set_title("Assistant is offline")
        else:
            self._status_page.set_icon_name("dialog-warning-symbolic")
            self._status_page.set_title("Could not read assistant status")
        self._status_page.set_description(f"{error} Endpoint: {endpoint}")
        self._stack.set_visible_child_name("empty")

    def show_overview(
        self,
        overview: HomeOverview,
        endpoint: str,
        last_success: datetime | None,
        failure: AssistantClientError | None = None,
    ) -> None:
        if failure is not None:
            self._banner.set_title(str(failure))
            self._banner.set_revealed(True)
        elif overview.home_error is not None:
            self._banner.set_title(str(overview.home_error))
            self._banner.set_revealed(True)
        else:
            self._banner.set_revealed(False)

        self._assistant_row.set_subtitle(_state_label(overview.status.status))
        self._service_row.set_subtitle(overview.status.service)
        self._version_row.set_subtitle(overview.status.version)
        self._endpoint_row.set_subtitle(endpoint)
        self._refreshed_row.set_subtitle(format_timestamp(last_success))

        calendar = overview.calendar
        self._calendar_state_row.set_subtitle(_state_label(calendar.status if calendar else None))
        if calendar is None or calendar.stale is None:
            stale_label = "—"
        else:
            stale_label = "Stale" if calendar.stale else "Fresh"
        self._calendar_stale_row.set_subtitle(stale_label)
        self._calendar_updated_row.set_subtitle(
            format_timestamp(calendar.updated_at if calendar else None)
        )

        self._pending_row.set_subtitle(_label(overview.pending_tasks))
        self._due_today_row.set_subtitle(_label(overview.due_today))
        self._stack.set_visible_child_name("content")
