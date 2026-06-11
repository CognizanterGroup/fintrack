"""Modal input dialogs used by the GUI pages.

Each dialog collects validated input and returns a plain dict of values; the
calling page passes those to the FinanceService. Validation errors raised by
the service are surfaced to the user via a message box at the call site.
"""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from ..core.validators import (
    DEBT_TYPES,
    EXPENSE_CATEGORIES,
    INCOME_SOURCES,
)


def _amount_spin() -> QDoubleSpinBox:
    spin = QDoubleSpinBox()
    spin.setMaximum(1_000_000_000)
    spin.setDecimals(2)
    spin.setGroupSeparatorShown(True)
    spin.setSingleStep(1000)
    return spin


def _date_edit(optional: bool = False) -> QDateEdit:
    edit = QDateEdit()
    edit.setCalendarPopup(True)
    edit.setDisplayFormat("yyyy-MM-dd")
    edit.setDate(QDate.currentDate())
    if optional:
        edit.setSpecialValueText(" ")
        edit.setMinimumDate(QDate(2000, 1, 1))
    return edit


class _BaseDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self.setModal(True)
        root = QVBoxLayout(self)
        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignLeft)
        self.form.setSpacing(10)
        root.addLayout(self.form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)


class TransactionDialog(_BaseDialog):
    def __init__(self, kind: str, parent=None):
        super().__init__(f"Add {kind}", parent)
        self.kind = kind
        self.amount = _amount_spin()
        self.category = QComboBox()
        self.category.addItems(
            INCOME_SOURCES if kind == "income" else EXPENSE_CATEGORIES
        )
        self.description = QLineEdit()
        self.date = _date_edit()
        self.form.addRow("Amount", self.amount)
        self.form.addRow("Source" if kind == "income" else "Category",
                         self.category)
        self.form.addRow("Description", self.description)
        self.form.addRow("Date", self.date)

    def values(self) -> dict:
        return {
            "amount": self.amount.value(),
            "category": self.category.currentText(),
            "description": self.description.text(),
            "occurred_on": self.date.date().toString("yyyy-MM-dd"),
        }


class BudgetDialog(_BaseDialog):
    def __init__(self, month: str, parent=None):
        super().__init__("Set budget", parent)
        self.month_input = QLineEdit(month)
        self.category = QComboBox()
        self.category.addItem("overall")
        self.category.addItems(EXPENSE_CATEGORIES)
        self.limit = _amount_spin()
        self.form.addRow("Month (YYYY-MM)", self.month_input)
        self.form.addRow("Category", self.category)
        self.form.addRow("Limit", self.limit)

    def values(self) -> dict:
        return {
            "month": self.month_input.text(),
            "category": self.category.currentText(),
            "limit": self.limit.value(),
        }


class GoalDialog(_BaseDialog):
    def __init__(self, parent=None):
        super().__init__("New savings goal", parent)
        self.name = QLineEdit()
        self.target = _amount_spin()
        self.deadline = _date_edit()
        self.form.addRow("Goal name", self.name)
        self.form.addRow("Target amount", self.target)
        self.form.addRow("Deadline", self.deadline)

    def values(self) -> dict:
        return {
            "name": self.name.text(),
            "target": self.target.value(),
            "deadline": self.deadline.date().toString("yyyy-MM-dd"),
        }


class AmountDialog(_BaseDialog):
    """Generic single-amount prompt (contribute, withdraw, pay)."""

    def __init__(self, title: str, label: str = "Amount", parent=None):
        super().__init__(title, parent)
        self.amount = _amount_spin()
        self.form.addRow(label, self.amount)

    def value(self) -> float:
        return self.amount.value()


class DebtDialog(_BaseDialog):
    def __init__(self, parent=None):
        super().__init__("Record debt", parent)
        self.direction = QComboBox()
        self.direction.addItems(DEBT_TYPES)
        self.counterparty = QLineEdit()
        self.amount = _amount_spin()
        self.due = _date_edit()
        self.description = QLineEdit()
        self.form.addRow("Type", self.direction)
        self.form.addRow("Counterparty", self.counterparty)
        self.form.addRow("Amount", self.amount)
        self.form.addRow("Due date", self.due)
        self.form.addRow("Note", self.description)

    def values(self) -> dict:
        return {
            "direction": self.direction.currentText(),
            "counterparty": self.counterparty.text(),
            "amount": self.amount.value(),
            "due_date": self.due.date().toString("yyyy-MM-dd"),
            "description": self.description.text(),
        }
