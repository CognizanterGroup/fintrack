"""Small reusable widgets shared across GUI pages."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .theme import Palette


class Card(QFrame):
    """A rounded white surface used to group content."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(8)

    def layout(self) -> QVBoxLayout:  # type: ignore[override]
        return self._layout

    def add(self, widget: QWidget):
        self._layout.addWidget(widget)
        return widget


class StatCard(Card):
    """A KPI tile: small uppercase title above a large coloured value."""

    def __init__(self, title: str, value: str = "-", colour: str | None = None,
                 parent=None):
        super().__init__(parent)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        if colour:
            self.value_label.setStyleSheet(f"color: {colour};")
        self._layout.addWidget(self.title_label)
        self._layout.addWidget(self.value_label)
        self._layout.addStretch(1)

    def set_value(self, value: str, colour: str | None = None):
        self.value_label.setText(value)
        if colour:
            self.value_label.setStyleSheet(f"color: {colour};")


class StatusPill(QLabel):
    """A small coloured status badge."""

    _COLOURS = {
        "ok": (Palette.ACCENT_SOFT, Palette.ACCENT_DARK),
        "achieved": (Palette.ACCENT_SOFT, Palette.ACCENT_DARK),
        "paid": (Palette.ACCENT_SOFT, Palette.ACCENT_DARK),
        "warning": ("#fef3c7", "#b45309"),
        "partly_paid": ("#fef3c7", "#b45309"),
        "active": ("#dbeafe", "#1d4ed8"),
        "pending": ("#e2e8f0", "#475569"),
        "exceeded": ("#fee2e2", "#b91c1c"),
        "overdue": ("#fee2e2", "#b91c1c"),
    }

    def __init__(self, status: str, parent=None):
        super().__init__(status.replace("_", " "), parent)
        self.setObjectName("Pill")
        bg, fg = self._COLOURS.get(status, ("#e2e8f0", "#475569"))
        self.setStyleSheet(f"background: {bg}; color: {fg};")
        self.setAlignment(Qt.AlignCenter)


def page_header(title: str, subtitle: str = "") -> QWidget:
    """Standard page heading block."""
    wrap = QWidget()
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 6)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSub")
        lay.addWidget(s)
    return wrap


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {Palette.BORDER};")
    return line
