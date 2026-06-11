"""FinTrack desktop GUI entry point.

Boots a themed ``QApplication`` and shows the full-screen home page (register /
log in). Successful authentication opens the main window; logging out returns
to the home page without restarting the process.
"""

from __future__ import annotations

import sys

from ..core import AuthManager, JSONStore


def _require_pyside():
    try:
        import PySide6  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "The FinTrack GUI requires PySide6.\n"
            "Install it with:  pip install PySide6\n"
            "Or run the terminal version:  fintrack --cli\n"
        )
        raise SystemExit(1)


def run(data_dir: str | None = None) -> int:
    _require_pyside()
    from PySide6.QtWidgets import QApplication
    from . import icons
    from .home import HomeWindow
    from .main_window import MainWindow
    from .theme import stylesheet

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("FinTrack")
    app.setOrganizationName("FinTrack")
    app.setWindowIcon(icons.app_icon())
    app.setStyleSheet(stylesheet())

    store = JSONStore(data_dir)
    auth = AuthManager(store)

    # Keep a reference to whichever window is current so it isn't collected.
    state = {"window": None}

    def show_home():
        home = HomeWindow(auth, on_authenticated=open_main)
        state["window"] = home
        home.showMaximized()

    def open_main(username: str):
        win = MainWindow(username, store, on_logout=show_home)
        state["window"] = win
        win.showMaximized()

    show_home()
    return app.exec()


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
