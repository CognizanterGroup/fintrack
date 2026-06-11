"""The main application window: sidebar navigation + stacked feature pages."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..core import FinanceService, JSONStore
from . import icons
from .pages import (
    AnalysisPage,
    BudgetsPage,
    DashboardPage,
    DebtsPage,
    GoalsPage,
    SettingsPage,
    TransactionsPage,
)


class MainWindow(QWidget):
    """Hosts the FinanceService and switches between feature pages."""

    NAV = [
        ("Dashboard", "dashboard", DashboardPage),
        ("Transactions", "transactions", TransactionsPage),
        ("Budgets", "budgets", BudgetsPage),
        ("Savings Goals", "goals", GoalsPage),
        ("Debts", "debts", DebtsPage),
        ("Analysis", "analysis", AnalysisPage),
        ("Settings", "settings", SettingsPage),
    ]

    _ICON_IDLE = "#94a3b8"   # slate 400 — inactive nav icons
    _ICON_ACTIVE = "#ffffff"

    def __init__(self, username: str, store: JSONStore, on_logout=None):
        super().__init__()
        self.svc = FinanceService(username, store)
        self.on_logout = on_logout
        self.setWindowTitle(f"FinTrack — {username}")
        self.setWindowIcon(icons.app_icon())
        self.resize(1280, 800)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar(username))

        self.stack = QStackedWidget()
        self.pages = []
        for _, _, page_cls in self.NAV:
            page = page_cls(self)
            self.pages.append(page)
            self.stack.addWidget(page)
        root.addWidget(self.stack, 1)

        self.nav_buttons[0].setChecked(True)
        self._switch(0)

    def _build_sidebar(self, username: str) -> QWidget:
        bar = QWidget()
        bar.setObjectName("Sidebar")
        bar.setFixedWidth(236)
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Brand row: logo mark + name / tagline
        brand_wrap = QWidget()
        brand_lay = QHBoxLayout(brand_wrap)
        brand_lay.setContentsMargins(18, 20, 18, 16)
        brand_lay.setSpacing(10)
        mark = QLabel()
        mark.setPixmap(icons.logo_pixmap(34))
        brand_lay.addWidget(mark)
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        brand = QLabel("FinTrack")
        brand.setStyleSheet("color: white; font-size: 19px; font-weight: 800;")
        sub = QLabel("Personal Finance")
        sub.setStyleSheet("color: #94a3b8; font-size: 11px;")
        text_col.addWidget(brand)
        text_col.addWidget(sub)
        brand_lay.addLayout(text_col)
        brand_lay.addStretch(1)
        lay.addWidget(brand_wrap)

        self.nav_buttons = []
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for idx, (label, icon_name, _) in enumerate(self.NAV):
            btn = QPushButton(f"  {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(icons.icon(icon_name, self._ICON_IDLE, 18))
            btn.setIconSize(QSize(18, 18))
            btn.clicked.connect(lambda _=False, i=idx: self._switch(i))
            self.group.addButton(btn, idx)
            self.nav_buttons.append(btn)
            lay.addWidget(btn)

        lay.addStretch(1)
        chip = QLabel(f"Signed in as\n{username}")
        chip.setObjectName("UserChip")
        lay.addWidget(chip)
        logout = QPushButton("  Log out")
        logout.setObjectName("NavButton")
        logout.setCursor(Qt.PointingHandCursor)
        logout.setIcon(icons.icon("logout", self._ICON_IDLE, 18))
        logout.setIconSize(QSize(18, 18))
        logout.clicked.connect(self._logout)
        lay.addWidget(logout)
        lay.addSpacing(10)
        return bar

    def _switch(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            color = self._ICON_ACTIVE if i == index else self._ICON_IDLE
            btn.setIcon(icons.icon(self.NAV[i][1], color, 18))
        self.nav_buttons[index].setChecked(True)
        self.pages[index].refresh()

    def refresh_all(self):
        for page in self.pages:
            page.refresh()

    def _logout(self):
        if self.on_logout:
            self.on_logout()
        self.close()
