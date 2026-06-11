"""FinTrack - a personal finance manager with both a CLI and a desktop GUI.

The two front-ends (``fintrack.cli`` and ``fintrack.gui``) are thin layers over
a single shared core (``fintrack.core``), so behaviour and data are identical
no matter how you launch the app.
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
