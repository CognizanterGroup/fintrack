"""Vector icons and the FinTrack logo, rendered at runtime.

Everything here is drawn from inline SVG (feather-style, stroke-based), so the
app ships zero binary image assets and every icon can be tinted to any palette
colour at any size. ``icon(name, color)`` returns a crisp ``QIcon`` and
``logo_pixmap(size)`` / ``app_icon()`` produce the brand mark used in the
window chrome, the home page and the sidebar.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from .theme import Palette

# ---------------------------------------------------------------------------
# Icon registry — 24x24 viewBox, stroke-based, ``{c}`` is the tint colour.
# ---------------------------------------------------------------------------

_BODIES = {
    "dashboard": (
        '<rect x="3" y="3" width="7" height="9" rx="1.5"/>'
        '<rect x="14" y="3" width="7" height="5" rx="1.5"/>'
        '<rect x="14" y="12" width="7" height="9" rx="1.5"/>'
        '<rect x="3" y="16" width="7" height="5" rx="1.5"/>'
    ),
    "transactions": (
        '<path d="M17 3l4 4-4 4"/><path d="M21 7H7"/>'
        '<path d="M7 13l-4 4 4 4"/><path d="M3 17h14"/>'
    ),
    "budgets": (
        '<path d="M21.2 15.9A10 10 0 1 1 8 2.8"/>'
        '<path d="M22 12A10 10 0 0 0 12 2v10z"/>'
    ),
    "goals": (
        '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/>'
        '<circle cx="12" cy="12" r="1"/>'
    ),
    "debts": (
        '<rect x="2" y="5" width="20" height="14" rx="2"/>'
        '<path d="M2 10h20"/><path d="M6 15h4"/>'
    ),
    "analysis": (
        '<path d="M3 3v18h18"/><path d="M7 14l4-4 3 3 6-6"/>'
        '<path d="M16 7h4v4"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.9 2.9l-.1-.1'
        'a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1'
        'a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.9-2.9l.1-.1'
        'a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1'
        'a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.9-2.9l.1.1'
        'a1.7 1.7 0 0 0 1.9.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1'
        'a1.7 1.7 0 0 0 1 1.5h.1a1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.9 2.9'
        'l-.1.1a1.7 1.7 0 0 0-.3 1.9v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4'
        'h-.1a1.7 1.7 0 0 0-1.5 1z"/>'
    ),
    "logout": (
        '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
        '<path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>'
    ),
    "wallet": (
        '<path d="M20 7H4a2 2 0 0 1 0-4h13a1 1 0 0 1 1 1v3"/>'
        '<path d="M4 7h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5"/>'
        '<circle cx="16.5" cy="14" r="1.2"/>'
    ),
    "shield": (
        '<path d="M12 22s8-3.6 8-9V5l-8-3-8 3v8c0 5.4 8 9 8 9z"/>'
        '<path d="M9 11.5l2 2 4-4.5"/>'
    ),
    "trending": (
        '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>'
    ),
    "piggy": (
        '<path d="M19 9.5a2.5 2.5 0 0 1 2 2.4v1.6a1 1 0 0 1-1 1h-1'
        'a6.5 6.5 0 0 1-2.5 3.4V20a1 1 0 0 1-1 1h-1.5a1 1 0 0 1-1-1v-1h-3v1'
        'a1 1 0 0 1-1 1H7.5a1 1 0 0 1-1-1v-2.1A6.5 6.5 0 0 1 10.5 6H14'
        'a6.5 6.5 0 0 1 5 3.5z"/>'
        '<circle cx="15.5" cy="11" r="0.8"/>'
        '<path d="M9 6c-.5-1.5.3-3 2-3s2.5 1.5 2 3"/>'
    ),
    "user": (
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    "lock": (
        '<rect x="3" y="11" width="18" height="11" rx="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    ),
    "github": (
        '<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.9a3.4 3.4 0 0 0-1-2.6'
        'c3.2-.4 6.5-1.6 6.5-7A5.4 5.4 0 0 0 20 4.8 5 5 0 0 0 19.9 1S18.7.6 16 2.5'
        'a13.4 13.4 0 0 0-7 0C6.3.6 5.1 1 5.1 1A5 5 0 0 0 5 4.8a5.4 5.4 0 0 0-1.5 3.7'
        'c0 5.4 3.3 6.6 6.5 7a3.4 3.4 0 0 0-1 2.6V22"/>'
    ),
}


def _svg(name: str, color: str, stroke_width: float = 2.0) -> bytes:
    body = _BODIES[name]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    ).encode()


def _render(svg_bytes: bytes, size: int) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap


def pixmap(name: str, color: str = Palette.TEXT, size: int = 20,
           stroke_width: float = 2.0) -> QPixmap:
    """Render a registry icon to a tinted pixmap (2x for HiDPI crispness)."""
    pm = _render(_svg(name, color, stroke_width), size * 2)
    pm.setDevicePixelRatio(2.0)
    return pm


def icon(name: str, color: str = Palette.TEXT, size: int = 20,
         stroke_width: float = 2.0) -> QIcon:
    return QIcon(pixmap(name, color, size, stroke_width))


# ---------------------------------------------------------------------------
# Brand logo — emerald rounded square with a rising spark-line. Mirrors
# assets/logo.svg; keep the two in sync if the mark changes.
# ---------------------------------------------------------------------------

LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#10b981"/>'
    '<stop offset="1" stop-color="#059669"/>'
    '</linearGradient></defs>'
    '<rect width="64" height="64" rx="14" fill="url(#g)"/>'
    '<path d="M14 42 L26 30 L34 37 L50 20" fill="none" stroke="white" '
    'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M41 20 H50 V29" fill="none" stroke="white" stroke-width="5" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="17" cy="47" r="3" fill="white" opacity="0.9"/>'
    '</svg>'
).encode()


def logo_pixmap(size: int = 64) -> QPixmap:
    pm = _render(LOGO_SVG, size * 2)
    pm.setDevicePixelRatio(2.0)
    return pm


def app_icon() -> QIcon:
    ico = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        ico.addPixmap(_render(LOGO_SVG, size))
    return ico
