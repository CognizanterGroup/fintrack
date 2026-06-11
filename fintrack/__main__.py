"""Single entry point that routes to the GUI or the CLI.

    python -m fintrack            # launch the desktop GUI (default)
    python -m fintrack --cli      # launch the terminal interface
    python -m fintrack --gui      # explicitly launch the GUI
    python -m fintrack --data-dir /path/to/data   # custom data location

When installed (``pip install .``) the same routing is available via the
``fintrack`` command, with ``fintrack-cli`` and ``fintrack-gui`` as shortcuts.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__


def _parse(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fintrack",
        description="FinTrack - personal finance manager (GUI + CLI).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--gui", action="store_true",
                      help="launch the desktop GUI (default)")
    mode.add_argument("--cli", action="store_true",
                      help="launch the terminal interface")
    parser.add_argument("--data-dir", default=None,
                        help="directory for JSON data files")
    parser.add_argument("--version", action="version",
                        version=f"FinTrack {__version__}")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    if args.cli:
        from .cli.app import run as run_cli
        return run_cli(args.data_dir)
    from .gui.app import run as run_gui
    return run_gui(args.data_dir)


if __name__ == "__main__":
    sys.exit(main())
