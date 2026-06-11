"""The feature pages of the FinTrack desktop app.

Every page is a ``QWidget`` that holds a reference to the shared
:class:`FinanceService` and exposes a ``refresh()`` method. The MainWindow calls
``refresh_all()`` after any mutation so figures stay consistent across pages.
Pages never touch storage directly - they go through the service, exactly like
the CLI does.
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core import FinanceService
from ..core.exceptions import FinTrackError
from . import charts
from .dialogs import (
    AmountDialog,
    BudgetDialog,
    DebtDialog,
    GoalDialog,
    TransactionDialog,
)
from .theme import Palette
from .widgets import Card, StatCard, StatusPill, page_header


def _readonly_item(text: str, colour: str | None = None,
                   align=Qt.AlignVCenter | Qt.AlignLeft) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
    item.setTextAlignment(align)
    if colour:
        item.setForeground(Qt.GlobalColor.black)
        from PySide6.QtGui import QColor
        item.setForeground(QColor(colour))
    return item


class _Page(QWidget):
    """Base page with a scrollable content column and service access."""

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.svc: FinanceService = main.svc

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        self.body = QWidget()
        self.col = QVBoxLayout(self.body)
        self.col.setContentsMargins(28, 24, 28, 28)
        self.col.setSpacing(16)
        scroll.setWidget(self.body)

    def money(self, value: float) -> str:
        return f"{self.svc.currency}{value:,.2f}"

    def refresh(self):  # overridden by subclasses
        pass

    def _error(self, exc: Exception):
        QMessageBox.warning(self, "FinTrack", str(exc))


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------

class DashboardPage(_Page):
    def __init__(self, main):
        super().__init__(main)
        self.col.addWidget(page_header(
            "Dashboard", "Your financial picture at a glance"))

        grid = QGridLayout()
        grid.setSpacing(14)
        self.card_income = StatCard("Total income", colour=Palette.INCOME)
        self.card_expense = StatCard("Total expenses", colour=Palette.EXPENSE)
        self.card_balance = StatCard("Balance")
        self.card_savings = StatCard("Total savings", colour=Palette.INFO)
        grid.addWidget(self.card_income, 0, 0)
        grid.addWidget(self.card_expense, 0, 1)
        grid.addWidget(self.card_balance, 0, 2)
        grid.addWidget(self.card_savings, 0, 3)
        self.col.addLayout(grid)

        row = QHBoxLayout()
        row.setSpacing(14)

        # Health score card
        self.health_card = Card()
        self.health_title = QLabel("Financial Health Score")
        self.health_title.setObjectName("CardTitle")
        self.health_value = QLabel("-")
        self.health_value.setObjectName("StatValue")
        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setTextVisible(False)
        self.health_notes = QLabel()
        self.health_notes.setWordWrap(True)
        self.health_notes.setStyleSheet(f"color: {Palette.TEXT_MUTED};")
        for w in (self.health_title, self.health_value, self.health_bar,
                  self.health_notes):
            self.health_card.layout().addWidget(w)
        self.health_card.layout().addStretch(1)
        row.addWidget(self.health_card, 1)

        # Alerts card
        self.alerts_card = Card()
        at = QLabel("Budget alerts (this month)")
        at.setObjectName("CardTitle")
        self.alerts_card.layout().addWidget(at)
        self.alerts_body = QLabel()
        self.alerts_body.setWordWrap(True)
        self.alerts_card.layout().addWidget(self.alerts_body)
        self.alerts_card.layout().addStretch(1)
        row.addWidget(self.alerts_card, 1)
        self.col.addLayout(row)

        # Recent transactions
        rt = QLabel("Recent transactions")
        rt.setObjectName("SectionTitle")
        self.col.addWidget(rt)
        self.recent = QTableWidget(0, 4)
        self.recent.setHorizontalHeaderLabels(
            ["Date", "Type", "Category", "Amount"])
        self.recent.verticalHeader().setVisible(False)
        self.recent.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.recent.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent.setMaximumHeight(260)
        self.col.addWidget(self.recent)

    def refresh(self):
        s = self.svc.summary()
        self.card_income.set_value(self.money(s["total_income"]))
        self.card_expense.set_value(self.money(s["total_expense"]))
        self.card_balance.set_value(self.money(s["balance"]))
        self.card_savings.set_value(self.money(s["total_savings"]))

        hs = self.svc.health_score()
        colour = {"A": Palette.INCOME, "B": Palette.INCOME,
                  "C": Palette.WARNING, "D": Palette.WARNING,
                  "E": Palette.DANGER}.get(hs["grade"], Palette.TEXT)
        self.health_value.setText(
            f"{hs['score']}/100  ·  {hs['grade']} ({hs['label']})")
        self.health_value.setStyleSheet(f"color: {colour};")
        self.health_bar.setValue(int(hs["score"]))
        self.health_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {colour}; border-radius: 6px; }}")
        self.health_notes.setText("\n".join(f"• {n}" for n in hs["notes"]))

        warnings = self.svc.budget_warnings(date.today().strftime("%Y-%m"))
        if warnings:
            self.alerts_body.setText("\n".join(f"⚠ {w}" for w in warnings))
            self.alerts_body.setStyleSheet(f"color: {Palette.DANGER};")
        else:
            self.alerts_body.setText("No alerts — you're within budget. ✓")
            self.alerts_body.setStyleSheet(f"color: {Palette.TEXT_MUTED};")

        txs = self.svc.list_transactions()[:8]
        self.recent.setRowCount(len(txs))
        for r, t in enumerate(txs):
            colour = Palette.INCOME if t.kind == "income" else Palette.EXPENSE
            self.recent.setItem(r, 0, _readonly_item(t.occurred_on))
            self.recent.setItem(r, 1, _readonly_item(t.kind, colour))
            self.recent.setItem(r, 2, _readonly_item(t.category))
            sign = "+" if t.kind == "income" else "-"
            self.recent.setItem(
                r, 3, _readonly_item(f"{sign}{self.money(t.amount)}", colour,
                                     Qt.AlignVCenter | Qt.AlignRight))


# --------------------------------------------------------------------------
# Transactions
# --------------------------------------------------------------------------

class TransactionsPage(_Page):
    COLS = ["Date", "Type", "Category", "Amount", "Description", ""]

    def __init__(self, main):
        super().__init__(main)
        self.col.addWidget(page_header(
            "Transactions", "Record and review your income and expenses"))

        controls = QHBoxLayout()
        self.add_income_btn = QPushButton("+ Income")
        self.add_expense_btn = QPushButton("+ Expense")
        self.add_expense_btn.setStyleSheet(
            f"background: {Palette.EXPENSE};")
        self.add_income_btn.clicked.connect(lambda: self._add("income"))
        self.add_expense_btn.clicked.connect(lambda: self._add("expense"))

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search keyword…")
        self.search.textChanged.connect(self.refresh)

        self.kind_filter = QComboBox()
        self.kind_filter.addItems(["all", "income", "expense"])
        self.kind_filter.currentTextChanged.connect(self.refresh)

        self.month_filter = QLineEdit()
        self.month_filter.setPlaceholderText("Month YYYY-MM")
        self.month_filter.setMaximumWidth(140)
        self.month_filter.textChanged.connect(self.refresh)

        controls.addWidget(self.add_income_btn)
        controls.addWidget(self.add_expense_btn)
        controls.addStretch(1)
        controls.addWidget(self.search)
        controls.addWidget(self.kind_filter)
        controls.addWidget(self.month_filter)
        self.col.addLayout(controls)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        for i in (0, 1, 2, 3, 5):
            h.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.col.addWidget(self.table)

    def _add(self, kind: str):
        dlg = TransactionDialog(kind, self)
        if dlg.exec():
            v = dlg.values()
            try:
                if kind == "income":
                    self.svc.add_income(v["amount"], v["category"],
                                        v["description"], v["occurred_on"])
                else:
                    self.svc.add_expense(v["amount"], v["category"],
                                         v["description"], v["occurred_on"])
                    for w in self.svc.budget_warnings(v["occurred_on"][:7]):
                        QMessageBox.warning(self, "Budget alert", w)
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def _delete(self, tx_id: str):
        if QMessageBox.question(self, "Delete", "Delete this transaction?") \
                == QMessageBox.Yes:
            try:
                self.svc.delete_transaction(tx_id)
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def refresh(self):
        keyword = self.search.text().strip()
        if keyword:
            txs = self.svc.search_transactions(keyword)
        else:
            kind = self.kind_filter.currentText()
            month = self.month_filter.text().strip()
            try:
                txs = self.svc.list_transactions(
                    kind=None if kind == "all" else kind,
                    month=month or None,
                )
            except FinTrackError:
                txs = []  # invalid partial month input; show nothing yet
        txs = sorted(txs, key=lambda t: t.occurred_on, reverse=True)

        self.table.setRowCount(len(txs))
        for r, t in enumerate(txs):
            colour = Palette.INCOME if t.kind == "income" else Palette.EXPENSE
            self.table.setItem(r, 0, _readonly_item(t.occurred_on))
            self.table.setItem(r, 1, _readonly_item(t.kind, colour))
            self.table.setItem(r, 2, _readonly_item(t.category))
            self.table.setItem(
                r, 3, _readonly_item(self.money(t.amount), colour,
                                     Qt.AlignVCenter | Qt.AlignRight))
            self.table.setItem(r, 4, _readonly_item(t.description or "—"))
            btn = QPushButton("Delete")
            btn.setObjectName("Danger")
            btn.clicked.connect(lambda _=False, i=t.id: self._delete(i))
            self.table.setCellWidget(r, 5, btn)


# --------------------------------------------------------------------------
# Budgets
# --------------------------------------------------------------------------

class BudgetsPage(_Page):
    COLS = ["Category", "Limit", "Spent", "Remaining", "Used", "Status", ""]

    def __init__(self, main):
        super().__init__(main)
        self.col.addWidget(page_header(
            "Budgets", "Set monthly limits and get warned before you overspend"))

        controls = QHBoxLayout()
        self.month = QLineEdit(date.today().strftime("%Y-%m"))
        self.month.setMaximumWidth(140)
        self.month.textChanged.connect(self.refresh)
        self.add_btn = QPushButton("+ Set budget")
        self.add_btn.clicked.connect(self._add)
        controls.addWidget(QLabel("Month"))
        controls.addWidget(self.month)
        controls.addStretch(1)
        controls.addWidget(self.add_btn)
        self.col.addLayout(controls)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.col.addWidget(self.table)

    def _add(self):
        dlg = BudgetDialog(self.month.text().strip(), self)
        if dlg.exec():
            v = dlg.values()
            try:
                self.svc.set_budget(v["month"], v["category"], v["limit"])
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def _delete(self, bid: str):
        try:
            self.svc.delete_budget(bid)
            self.main.refresh_all()
        except FinTrackError as exc:
            self._error(exc)

    def refresh(self):
        month = self.month.text().strip()
        try:
            rows = self.svc.budget_status(month)
        except FinTrackError:
            self.table.setRowCount(0)
            return
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, _readonly_item(row["category"]))
            self.table.setItem(r, 1, _readonly_item(self.money(row["limit"])))
            self.table.setItem(r, 2, _readonly_item(self.money(row["spent"])))
            rem_colour = Palette.DANGER if row["remaining"] < 0 else Palette.TEXT
            self.table.setItem(r, 3, _readonly_item(
                self.money(row["remaining"]), rem_colour))
            self.table.setItem(r, 4, _readonly_item(f"{row['ratio']*100:.0f}%"))
            pill = StatusPill(row["level"])
            self.table.setCellWidget(r, 5, self._center(pill))
            btn = QPushButton("Delete")
            btn.setObjectName("Danger")
            btn.clicked.connect(lambda _=False, i=row["id"]: self._delete(i))
            self.table.setCellWidget(r, 6, btn)

    @staticmethod
    def _center(widget) -> QWidget:
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.addWidget(widget)
        lay.setAlignment(Qt.AlignCenter)
        return wrap


# --------------------------------------------------------------------------
# Goals
# --------------------------------------------------------------------------

class GoalsPage(_Page):
    def __init__(self, main):
        super().__init__(main)
        self.col.addWidget(page_header(
            "Savings Goals", "Track progress toward your targets"))
        controls = QHBoxLayout()
        controls.addStretch(1)
        self.add_btn = QPushButton("+ New goal")
        self.add_btn.clicked.connect(self._add)
        controls.addWidget(self.add_btn)
        self.col.addLayout(controls)

        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.col.addWidget(self.cards_host)
        self.empty = QLabel("No savings goals yet. Create one to get started.")
        self.empty.setStyleSheet(f"color: {Palette.TEXT_MUTED};")
        self.col.addWidget(self.empty)
        self.col.addStretch(1)

    def _add(self):
        dlg = GoalDialog(self)
        if dlg.exec():
            v = dlg.values()
            try:
                self.svc.add_goal(v["name"], v["target"], v["deadline"] or None)
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def _contribute(self, gid: str, withdraw=False):
        title = "Withdraw from goal" if withdraw else "Add to goal"
        dlg = AmountDialog(title, self)
        if dlg.exec():
            try:
                if withdraw:
                    self.svc.withdraw_from_goal(gid, dlg.value())
                else:
                    self.svc.contribute_to_goal(gid, dlg.value())
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def _delete(self, gid: str):
        if QMessageBox.question(self, "Delete", "Delete this goal?") \
                == QMessageBox.Yes:
            try:
                self.svc.delete_goal(gid)
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def refresh(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        goals = self.svc.goals
        self.empty.setVisible(not goals)
        for g in goals:
            card = Card()
            head = QHBoxLayout()
            name = QLabel(g.name)
            name.setObjectName("SectionTitle")
            head.addWidget(name)
            head.addStretch(1)
            head.addWidget(StatusPill(g.status))
            card.layout().addLayout(head)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(g.progress * 100))
            bar.setFormat(f"{g.progress*100:.0f}%")
            bar.setTextVisible(True)
            card.layout().addWidget(bar)

            info = QLabel(
                f"{self.money(g.saved)} of {self.money(g.target)}  ·  "
                f"{self.money(g.remaining)} to go"
                + (f"  ·  due {g.deadline}" if g.deadline else ""))
            info.setStyleSheet(f"color: {Palette.TEXT_MUTED};")
            card.layout().addWidget(info)

            actions = QHBoxLayout()
            add = QPushButton("Add funds")
            wdr = QPushButton("Withdraw")
            wdr.setObjectName("Ghost")
            dele = QPushButton("Delete")
            dele.setObjectName("Danger")
            add.clicked.connect(lambda _=False, i=g.id: self._contribute(i))
            wdr.clicked.connect(
                lambda _=False, i=g.id: self._contribute(i, withdraw=True))
            dele.clicked.connect(lambda _=False, i=g.id: self._delete(i))
            actions.addWidget(add)
            actions.addWidget(wdr)
            actions.addStretch(1)
            actions.addWidget(dele)
            card.layout().addLayout(actions)

            self.cards_layout.addWidget(card)


# --------------------------------------------------------------------------
# Debts
# --------------------------------------------------------------------------

class DebtsPage(_Page):
    COLS = ["Type", "Counterparty", "Amount", "Paid", "Outstanding",
            "Due", "Status", ""]

    def __init__(self, main):
        super().__init__(main)
        self.col.addWidget(page_header(
            "Debts", "Money you owe and money owed to you"))
        controls = QHBoxLayout()
        controls.addStretch(1)
        self.add_btn = QPushButton("+ Record debt")
        self.add_btn.clicked.connect(self._add)
        controls.addWidget(self.add_btn)
        self.col.addLayout(controls)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.col.addWidget(self.table)

    def _add(self):
        dlg = DebtDialog(self)
        if dlg.exec():
            v = dlg.values()
            try:
                self.svc.add_debt(v["direction"], v["counterparty"],
                                  v["amount"], v["due_date"] or None,
                                  v["description"])
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def _pay(self, did: str):
        dlg = AmountDialog("Record payment", "Payment amount", self)
        if dlg.exec():
            try:
                self.svc.pay_debt(did, dlg.value())
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def _delete(self, did: str):
        if QMessageBox.question(self, "Delete", "Delete this debt?") \
                == QMessageBox.Yes:
            try:
                self.svc.delete_debt(did)
                self.main.refresh_all()
            except FinTrackError as exc:
                self._error(exc)

    def refresh(self):
        debts = self.svc.list_debts()
        self.table.setRowCount(len(debts))
        for r, d in enumerate(debts):
            self.table.setItem(r, 0, _readonly_item(d.direction))
            self.table.setItem(r, 1, _readonly_item(d.counterparty))
            self.table.setItem(r, 2, _readonly_item(self.money(d.amount)))
            self.table.setItem(r, 3, _readonly_item(self.money(d.amount_paid)))
            self.table.setItem(r, 4, _readonly_item(
                self.money(d.outstanding)))
            self.table.setItem(r, 5, _readonly_item(d.due_date or "—"))
            pill = StatusPill(d.status)
            self.table.setCellWidget(r, 6, BudgetsPage._center(pill))

            cell = QWidget()
            lay = QHBoxLayout(cell)
            lay.setContentsMargins(2, 2, 2, 2)
            pay = QPushButton("Pay")
            dele = QPushButton("Delete")
            dele.setObjectName("Danger")
            pay.clicked.connect(lambda _=False, i=d.id: self._pay(i))
            dele.clicked.connect(lambda _=False, i=d.id: self._delete(i))
            lay.addWidget(pay)
            lay.addWidget(dele)
            self.table.setCellWidget(r, 7, cell)


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

class AnalysisPage(_Page):
    def __init__(self, main):
        super().__init__(main)
        self.col.addWidget(page_header(
            "Spending Analysis", "Understand where your money goes"))

        self.habits_card = Card()
        self.habits_card.layout().addWidget(self._label("Spending habits",
                                                        "CardTitle"))
        self.habits_body = QLabel("No expense data yet.")
        self.habits_body.setWordWrap(True)
        self.habits_card.layout().addWidget(self.habits_body)
        self.col.addWidget(self.habits_card)

        self.charts_host = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_host)
        self.charts_layout.setContentsMargins(0, 0, 0, 0)
        self.charts_layout.setSpacing(16)
        self.col.addWidget(self.charts_host)
        self.col.addStretch(1)

    @staticmethod
    def _label(text, obj):
        lbl = QLabel(text)
        lbl.setObjectName(obj)
        return lbl

    def refresh(self):
        data = self.svc.spending_analysis()
        habits = data["habits"]
        if habits["highest_category"]:
            self.habits_body.setText(
                f"Highest spending category:  {habits['highest_category']['category']} "
                f"({self.money(habits['highest_category']['amount'])})\n"
                f"Lowest spending category:  {habits['lowest_category']['category']} "
                f"({self.money(habits['lowest_category']['amount'])})\n"
                f"Average expense:  {self.money(habits['average_expense'])}\n"
                f"Categories used:  {habits['category_count']}")
        else:
            self.habits_body.setText("No expense data yet.")

        # Rebuild charts
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if data["by_category"]:
            c1 = Card()
            c1.layout().addWidget(
                charts.category_donut(data["by_category"], self.svc.currency))
            self.charts_layout.addWidget(c1)
        if data["trends"]:
            c2 = Card()
            c2.layout().addWidget(charts.monthly_bars(data["trends"]))
            self.charts_layout.addWidget(c2)


# --------------------------------------------------------------------------
# Settings & export
# --------------------------------------------------------------------------

class SettingsPage(_Page):
    def __init__(self, main):
        super().__init__(main)
        self.col.addWidget(page_header(
            "Settings & Export", "Preferences and shareable reports"))

        # Currency
        cur_card = Card()
        cur_card.layout().addWidget(self._lbl("Currency symbol", "CardTitle"))
        row = QHBoxLayout()
        self.currency_input = QLineEdit(self.svc.currency)
        self.currency_input.setMaximumWidth(120)
        save_cur = QPushButton("Save")
        save_cur.clicked.connect(self._save_currency)
        row.addWidget(self.currency_input)
        row.addWidget(save_cur)
        row.addStretch(1)
        cur_card.layout().addLayout(row)
        self.col.addWidget(cur_card)

        # Export
        exp_card = Card()
        exp_card.layout().addWidget(self._lbl("Export report", "CardTitle"))
        desc = QLabel("Save a shareable report for your financial advisor or "
                      "personal records.")
        desc.setStyleSheet(f"color: {Palette.TEXT_MUTED};")
        desc.setWordWrap(True)
        exp_card.layout().addWidget(desc)
        exp_row = QHBoxLayout()
        for fmt in ("txt", "csv", "json"):
            btn = QPushButton(f"Export {fmt.upper()}")
            btn.setObjectName("Ghost")
            btn.clicked.connect(lambda _=False, f=fmt: self._export(f))
            exp_row.addWidget(btn)
        exp_row.addStretch(1)
        exp_card.layout().addLayout(exp_row)
        self.col.addWidget(exp_card)
        self.col.addStretch(1)

    @staticmethod
    def _lbl(text, obj):
        lbl = QLabel(text)
        lbl.setObjectName(obj)
        return lbl

    def _save_currency(self):
        try:
            self.svc.set_currency(self.currency_input.text())
            self.main.refresh_all()
            QMessageBox.information(self, "FinTrack", "Currency updated.")
        except FinTrackError as exc:
            self._error(exc)

    def _export(self, fmt: str):
        default = f"fintrack_{self.svc.username}_report.{fmt}"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export report", default,
            f"{fmt.upper()} files (*.{fmt})")
        if not path:
            return
        try:
            out = self.svc.export_report(path, fmt)
            QMessageBox.information(self, "FinTrack",
                                    f"Report saved to:\n{out}")
        except FinTrackError as exc:
            self._error(exc)

    def refresh(self):
        self.currency_input.setText(self.svc.currency)
