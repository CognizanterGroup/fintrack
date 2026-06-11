"""PyInstaller entry script for the FinTrack desktop app.

PyInstaller needs a plain script (not ``python -m fintrack``) as its target.
This simply hands off to the normal CLI router, which defaults to the GUI.

Build (from the project root, with `.[gui]` and pyinstaller installed):

    pyinstaller --noconfirm --windowed --name FinTrack \
        --icon assets/icon.ico packaging/fintrack_entry.py
"""

import sys

from fintrack.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
