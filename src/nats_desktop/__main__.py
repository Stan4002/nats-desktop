from __future__ import annotations

import sys

from nats_desktop.app import NatsApplication


def main(argv: list[str] | None = None) -> int:
    app = NatsApplication()
    return app.run(argv if argv is not None else sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
