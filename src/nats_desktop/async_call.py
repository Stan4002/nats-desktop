from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TypeVar

from gi.repository import GLib

T = TypeVar("T")


def call_in_thread(
    work: Callable[[], T],
    on_success: Callable[[T], None],
    on_error: Callable[[BaseException], None],
) -> None:
    """Run *work* off the GTK main loop, then deliver the result on it.

    GTK is not thread-safe. Only the callbacks may touch widgets, and they
    run because ``GLib.idle_add`` queues them for the next main-loop iteration.
    """

    def runner() -> None:
        try:
            result = work()
        except BaseException as exc:  # noqa: BLE001 — deliver every failure to the UI
            GLib.idle_add(_deliver, on_error, exc)
        else:
            GLib.idle_add(_deliver, on_success, result)


def _deliver(callback: Callable[[object], None], value: object) -> bool:
    callback(value)
    return False

    threading.Thread(target=runner, daemon=True).start()
