from __future__ import annotations

import inspect

from gi.repository import GLib

from nats_desktop.api.client import BackendStatus, CalendarOverview, HomeOverview
from nats_desktop.async_call import call_in_thread


def _run_until(callback_holder: list, timeout_ms: int = 2000) -> None:
    loop = GLib.MainLoop()

    def stop_if_done() -> bool:
        if callback_holder:
            loop.quit()
            return False
        return True

    GLib.timeout_add(10, stop_if_done)
    GLib.timeout_add(timeout_ms, loop.quit)
    loop.run()


def test_call_in_thread_starts_a_worker() -> None:
    source = inspect.getsource(call_in_thread)
    assert "threading.Thread" in source
    assert ".start()" in source


def test_call_in_thread_delivers_success_on_the_glib_loop() -> None:
    received: list[object] = []

    call_in_thread(lambda: "overview", received.append, received.append)
    _run_until(received)

    assert received == ["overview"]


def test_call_in_thread_delivers_worker_exceptions() -> None:
    received: list[object] = []

    def work() -> str:
        raise RuntimeError("worker failed")

    def on_success(_value: str) -> None:
        received.append("success")

    call_in_thread(work, on_success, received.append)
    _run_until(received)

    assert len(received) == 1
    assert isinstance(received[0], RuntimeError)
    assert str(received[0]) == "worker failed"


def test_call_in_thread_delivers_home_overview_objects() -> None:
    overview = HomeOverview(
        status=BackendStatus("nats-assistant", "online", "0.1.0"),
        calendar=CalendarOverview("not_connected", False, None),
        pending_tasks=0,
        due_today=0,
    )
    received: list[object] = []

    call_in_thread(lambda: overview, received.append, received.append)
    _run_until(received)

    assert received == [overview]
