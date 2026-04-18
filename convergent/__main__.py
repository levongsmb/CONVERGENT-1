"""Entry point for the `convergent` command.

Phase 0: the installer can boot the app far enough to show a "scaffold only"
landing view. The NiceGUI wiring lands in Phase 6; this stub keeps the
installer smoke test green in the interim.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    if argv and argv[0] == "--version":
        from convergent import __version__

        print(__version__)
        return 0

    print(
        "Convergent scaffold (Phase 0). "
        "The interactive workbench lands in Phase 6 per docs/PROMPT_V3.md §18."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
