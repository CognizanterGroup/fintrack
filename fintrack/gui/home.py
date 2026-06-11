"""The full-screen home page: product hero on the left, auth card on the right.

This is the first thing a user sees. The left panel sells the product (logo,
headline, feature cards); the right panel holds a single card that flips
between *log in* and *create account*. On success the window hands the
authenticated username to ``on_authenticated`` and closes itself.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..core import AuthManager
from ..core.exceptions import FinTrackError
from . import icons
from .theme import Palette

_FEATURES = [
    ("wallet", "Track everything",
     "Income, expenses, budgets, savings goals and debts in one place."),
    ("trending", "Understand your money",
     "Trends, spending analysis and a 0–100 financial health score."),
    ("shield", "Private by design",
     "Your data stays on your machine. No cloud, no tracking, no ads."),
    ("piggy", "Reach your goals",
     "Set monthly budgets and savings targets, get overspend warnings."),
]


class _FeatureCard(QFrame):
    def __init__(self, icon_name: str, title: str, body: str, parent=None):
        super().__init__(parent)
        self.setObjectName("HeroCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)

        ic = QLabel()
        ic.setPixmap(icons.pixmap(icon_name, Palette.ACCENT, 26))
        lay.addWidget(ic)

        t = QLabel(title)
        t.setObjectName("HeroCardTitle")
        lay.addWidget(t)

        b = QLabel(body)
        b.setObjectName("HeroCardBody")
        b.setWordWrap(True)
        lay.addWidget(b)
        lay.addStretch(1)


class HomeWindow(QWidget):
    """Landing window shown maximized; replaces the old modal login dialog."""

    def __init__(self, auth: AuthManager, on_authenticated=None):
        super().__init__()
        self.auth = auth
        self.on_authenticated = on_authenticated
        self.mode = "login"  # or "register"

        self.setWindowTitle("FinTrack — Personal Finance Manager")
        self.setWindowIcon(icons.app_icon())
        self.setStyleSheet(self._qss())

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_hero(), 11)
        root.addWidget(self._build_auth_panel(), 9)

    # ------------------------------------------------------------------ hero

    def _build_hero(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("HeroPanel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(56, 44, 56, 32)
        lay.setSpacing(0)

        # Brand row: logo + wordmark
        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        logo = QLabel()
        logo.setPixmap(icons.logo_pixmap(44))
        brand_row.addWidget(logo)
        word = QLabel("FinTrack")
        word.setObjectName("HeroBrand")
        brand_row.addWidget(word)
        brand_row.addStretch(1)
        lay.addLayout(brand_row)

        lay.addStretch(2)

        headline = QLabel("Take control of\nyour money.")
        headline.setObjectName("HeroHeadline")
        lay.addWidget(headline)
        lay.addSpacing(14)

        sub = QLabel(
            "A fast, private, open-source personal finance manager.\n"
            "Track income and expenses, set budgets, hit savings goals\n"
            "and watch your financial health score climb."
        )
        sub.setObjectName("HeroSub")
        lay.addWidget(sub)
        lay.addSpacing(34)

        grid = QGridLayout()
        grid.setSpacing(14)
        for i, (icon_name, title, body) in enumerate(_FEATURES):
            grid.addWidget(_FeatureCard(icon_name, title, body),
                           i // 2, i % 2)
        lay.addLayout(grid)

        lay.addStretch(3)

        foot = QLabel(f"Free & open source  ·  MIT licensed  ·  v{__version__}")
        foot.setObjectName("HeroFoot")
        lay.addWidget(foot)
        return panel

    # ------------------------------------------------------------ auth panel

    def _build_auth_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("AuthPanel")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(48, 24, 48, 24)
        outer.addStretch(1)

        card = QFrame()
        card.setObjectName("AuthCard")
        card.setMaximumWidth(430)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(34, 32, 34, 30)
        cl.setSpacing(9)

        mark = QLabel()
        mark.setPixmap(icons.logo_pixmap(52))
        mark.setAlignment(Qt.AlignCenter)
        cl.addWidget(mark)
        cl.addSpacing(4)

        self.title = QLabel("Welcome back")
        self.title.setObjectName("AuthTitle")
        self.title.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.title)

        self.subtitle = QLabel("Log in to continue to FinTrack")
        self.subtitle.setObjectName("AuthSub")
        self.subtitle.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.subtitle)
        cl.addSpacing(14)

        cl.addWidget(self._field_label("user", "Username"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("e.g. princewill")
        cl.addWidget(self.user_input)
        cl.addSpacing(4)

        cl.addWidget(self._field_label("lock", "Password"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("at least 6 characters")
        cl.addWidget(self.pass_input)
        cl.addSpacing(4)

        self.confirm_label = self._field_label("lock", "Confirm password")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("repeat your password")
        cl.addWidget(self.confirm_label)
        cl.addWidget(self.confirm_input)

        cl.addSpacing(12)
        self.submit_btn = QPushButton("Log in")
        self.submit_btn.setObjectName("AuthSubmit")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self._submit)
        cl.addWidget(self.submit_btn)
        cl.addSpacing(4)

        toggle_row = QHBoxLayout()
        self.toggle_text = QLabel("New here?")
        self.toggle_text.setObjectName("AuthSub")
        self.toggle_btn = QPushButton("Create an account")
        self.toggle_btn.setObjectName("LinkButton")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle_mode)
        toggle_row.addStretch(1)
        toggle_row.addWidget(self.toggle_text)
        toggle_row.addWidget(self.toggle_btn)
        toggle_row.addStretch(1)
        cl.addLayout(toggle_row)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        outer.addLayout(row)

        hint = QLabel("Try the demo account:  demo / demo1234")
        hint.setObjectName("DemoHint")
        hint.setAlignment(Qt.AlignCenter)
        outer.addSpacing(16)
        outer.addWidget(hint)
        outer.addStretch(1)

        for w in (self.user_input, self.pass_input, self.confirm_input):
            w.returnPressed.connect(self._submit)
        self._apply_mode()
        return panel

    @staticmethod
    def _field_label(icon_name: str, text: str) -> QWidget:
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        ic = QLabel()
        ic.setPixmap(icons.pixmap(icon_name, Palette.TEXT_MUTED, 14))
        lay.addWidget(ic)
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        lay.addWidget(lbl)
        lay.addStretch(1)
        return wrap

    # ----------------------------------------------------------------- logic

    def _toggle_mode(self):
        self.mode = "register" if self.mode == "login" else "login"
        self._apply_mode()

    def _apply_mode(self):
        register = self.mode == "register"
        self.title.setText("Create your account" if register else "Welcome back")
        self.subtitle.setText("It's free — your data stays on this device"
                              if register else "Log in to continue to FinTrack")
        self.submit_btn.setText("Create account" if register else "Log in")
        self.confirm_label.setVisible(register)
        self.confirm_input.setVisible(register)
        self.toggle_text.setText("Already have an account?" if register
                                 else "New here?")
        self.toggle_btn.setText("Log in" if register else "Create an account")

    def _submit(self):
        username = self.user_input.text()
        password = self.pass_input.text()
        try:
            if self.mode == "register":
                if password != self.confirm_input.text():
                    raise FinTrackError("Passwords do not match.")
                username = self.auth.register(username, password)
            else:
                username = self.auth.authenticate(username, password)
        except FinTrackError as exc:
            QMessageBox.warning(self, "FinTrack", str(exc))
            return
        if self.on_authenticated:
            self.on_authenticated(username)
        self.close()

    # ------------------------------------------------------------------- qss

    @staticmethod
    def _qss() -> str:
        p = Palette
        return f"""
        #HeroPanel {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p.SIDEBAR}, stop:1 #134e4a);
        }}
        #HeroBrand {{ color: white; font-size: 26px; font-weight: 800; }}
        #HeroHeadline {{
            color: white; font-size: 46px; font-weight: 800;
            line-height: 110%;
        }}
        #HeroSub {{ color: {p.SIDEBAR_TEXT}; font-size: 15px; }}
        #HeroFoot {{ color: #64748b; font-size: 12px; }}
        #HeroCard {{
            background: rgba(255, 255, 255, 14);
            border: 1px solid rgba(255, 255, 255, 26);
            border-radius: 14px;
        }}
        #HeroCardTitle {{ color: white; font-size: 15px; font-weight: 700; }}
        #HeroCardBody {{ color: {p.SIDEBAR_TEXT}; font-size: 12px; }}

        #AuthPanel {{ background: {p.CANVAS}; }}
        #AuthCard {{
            background: {p.CARD}; border: 1px solid {p.BORDER};
            border-radius: 18px;
        }}
        #AuthTitle {{ font-size: 24px; font-weight: 800; color: {p.TEXT}; }}
        #AuthSub {{ color: {p.TEXT_MUTED}; font-size: 13px; }}
        #FieldLabel {{ color: {p.TEXT_MUTED}; font-size: 12px;
                       font-weight: 600; }}
        #AuthSubmit {{ padding: 12px 16px; font-size: 15px;
                       border-radius: 10px; }}
        QPushButton#LinkButton {{
            background: transparent; color: {p.ACCENT_DARK};
            border: none; padding: 2px 4px; font-weight: 700;
        }}
        QPushButton#LinkButton:hover {{ color: {p.ACCENT}; }}
        #DemoHint {{ color: {p.TEXT_MUTED}; font-size: 12px; }}
        """
