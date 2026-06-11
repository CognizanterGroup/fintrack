"""The FinanceService - FinTrack's business-logic core.

A :class:`FinanceService` instance represents one authenticated user's session.
It owns the in-memory model objects, persists every mutation to JSON, and
exposes high-level operations (add income, set a budget, contribute to a goal,
pay a debt, export a report, ...). Both the CLI and the GUI talk *only* to this
class, never to the storage layer directly - so behaviour stays identical
across front-ends and there is a single place to test.
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path

from . import analytics
from .exceptions import NotFoundError, ValidationError
from .models import Budget, Debt, SavingsGoal, Transaction
from .storage import JSONStore
from .validators import (
    DEBT_TYPES,
    EXPENSE_CATEGORIES,
    INCOME_SOURCES,
    validate_amount,
    validate_choice,
    validate_date,
    validate_month,
    validate_text,
)

DEFAULT_CURRENCY = "\u20a6"  # Naira sign


class FinanceService:
    """Stateful facade over one user's financial data."""

    def __init__(self, username: str, store: JSONStore):
        self.username = username
        self.store = store
        self.currency = DEFAULT_CURRENCY
        self.transactions: list[Transaction] = []
        self.budgets: list[Budget] = []
        self.goals: list[SavingsGoal] = []
        self.debts: list[Debt] = []
        self._load()

    # --- persistence ----------------------------------------------------

    def _load(self) -> None:
        data = self.store.load_account(self.username)
        self.currency = data.get("meta", {}).get("currency", DEFAULT_CURRENCY)
        self.transactions = [
            Transaction.from_dict(d) for d in data.get("transactions", [])
        ]
        self.budgets = [Budget.from_dict(d) for d in data.get("budgets", [])]
        self.goals = [SavingsGoal.from_dict(d) for d in data.get("goals", [])]
        self.debts = [Debt.from_dict(d) for d in data.get("debts", [])]
        self._refresh_derived()

    def _save(self) -> None:
        payload = {
            "meta": {
                "currency": self.currency,
                "owner": self.username,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
            "transactions": [t.to_dict() for t in self.transactions],
            "budgets": [b.to_dict() for b in self.budgets],
            "goals": [g.to_dict() for g in self.goals],
            "debts": [d.to_dict() for d in self.debts],
        }
        self.store.save_account(self.username, payload)

    def _refresh_derived(self) -> None:
        """Recompute statuses that depend on time or amounts."""
        for g in self.goals:
            g.refresh_status()
        for d in self.debts:
            d.refresh_status()

    def set_currency(self, symbol: str) -> None:
        self.currency = validate_text(symbol, field="currency", max_length=8)
        self._save()

    # --- transactions ---------------------------------------------------

    def add_income(self, amount, source, description="", occurred_on=None) -> Transaction:
        tx = Transaction(
            kind="income",
            amount=validate_amount(amount),
            category=validate_choice(source, INCOME_SOURCES, field="source"),
            description=validate_text(description, field="description",
                                      required=False),
            occurred_on=validate_date(occurred_on or date.today().isoformat()),
        )
        self.transactions.append(tx)
        self._save()
        return tx

    def add_expense(self, amount, category, description="", occurred_on=None) -> Transaction:
        tx = Transaction(
            kind="expense",
            amount=validate_amount(amount),
            category=validate_choice(category, EXPENSE_CATEGORIES,
                                     field="category"),
            description=validate_text(description, field="description",
                                      required=False),
            occurred_on=validate_date(occurred_on or date.today().isoformat()),
        )
        self.transactions.append(tx)
        self._save()
        return tx

    def delete_transaction(self, tx_id: str) -> None:
        before = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.id != tx_id]
        if len(self.transactions) == before:
            raise NotFoundError("Transaction not found.")
        self._save()

    def list_transactions(self, *, kind=None, month=None, year=None,
                          category=None) -> list[Transaction]:
        """Return transactions matching optional filters, newest first."""
        items = self.transactions
        if kind:
            items = [t for t in items if t.kind == kind]
        if month:
            month = validate_month(month)
            items = [t for t in items if t.month == month]
        if year:
            year = str(year).strip()
            items = [t for t in items if t.year == year]
        if category:
            category = str(category).strip().lower()
            items = [t for t in items if t.category == category]
        return sorted(items, key=lambda t: (t.occurred_on, t.created_at),
                      reverse=True)

    def search_transactions(self, keyword: str) -> list[Transaction]:
        """Case-insensitive search across description, category and kind."""
        kw = (keyword or "").strip().lower()
        if not kw:
            return []
        return [
            t for t in self.transactions
            if kw in t.description.lower()
            or kw in t.category.lower()
            or kw in t.kind.lower()
        ]

    # --- budgets --------------------------------------------------------

    def set_budget(self, month, category, limit) -> Budget:
        """Create or update the budget for a category in a month."""
        month = validate_month(month)
        if str(category).strip().lower() == "overall":
            category = "overall"
        else:
            category = validate_choice(category, EXPENSE_CATEGORIES,
                                       field="category")
        limit = validate_amount(limit, field="limit")

        for b in self.budgets:
            if b.month == month and b.category == category:
                b.limit = limit
                self._save()
                return b
        budget = Budget(month=month, category=category, limit=limit)
        self.budgets.append(budget)
        self._save()
        return budget

    def delete_budget(self, budget_id: str) -> None:
        before = len(self.budgets)
        self.budgets = [b for b in self.budgets if b.id != budget_id]
        if len(self.budgets) == before:
            raise NotFoundError("Budget not found.")
        self._save()

    def budget_status(self, month: str) -> list[dict]:
        """For each budget in ``month`` report spend, limit and any warning."""
        month = validate_month(month)
        spent_by_cat = {}
        month_expenses = [
            t for t in self.transactions
            if t.kind == "expense" and t.month == month
        ]
        for t in month_expenses:
            spent_by_cat[t.category] = spent_by_cat.get(t.category, 0.0) + t.amount
        total_spent = sum(spent_by_cat.values())

        rows = []
        for b in self.budgets:
            if b.month != month:
                continue
            spent = total_spent if b.category == "overall" else spent_by_cat.get(
                b.category, 0.0
            )
            ratio = spent / b.limit if b.limit else 0.0
            if ratio >= 1.0:
                level = "exceeded"
            elif ratio >= 0.8:
                level = "warning"
            else:
                level = "ok"
            rows.append({
                "id": b.id,
                "month": b.month,
                "category": b.category,
                "limit": round(b.limit, 2),
                "spent": round(spent, 2),
                "remaining": round(b.limit - spent, 2),
                "ratio": round(ratio, 3),
                "level": level,
            })
        return sorted(rows, key=lambda r: r["ratio"], reverse=True)

    def budget_warnings(self, month: str) -> list[str]:
        """Human-readable warnings for budgets at/over their limit."""
        msgs = []
        for row in self.budget_status(month):
            label = "overall spending" if row["category"] == "overall" \
                else row["category"]
            if row["level"] == "exceeded":
                msgs.append(
                    f"Over budget on {label}: spent {row['spent']:,.2f} "
                    f"of {row['limit']:,.2f} ({row['ratio']*100:.0f}%)."
                )
            elif row["level"] == "warning":
                msgs.append(
                    f"Approaching budget on {label}: {row['ratio']*100:.0f}% used."
                )
        return msgs

    # --- savings goals --------------------------------------------------

    def add_goal(self, name, target, deadline=None) -> SavingsGoal:
        goal = SavingsGoal(
            name=validate_text(name, field="goal name", max_length=80),
            target=validate_amount(target, field="target"),
            deadline=validate_date(deadline, allow_empty=True),
        )
        goal.refresh_status()
        self.goals.append(goal)
        self._save()
        return goal

    def contribute_to_goal(self, goal_id, amount) -> SavingsGoal:
        goal = self._find_goal(goal_id)
        goal.saved = round(goal.saved + validate_amount(amount), 2)
        goal.refresh_status()
        self._save()
        return goal

    def withdraw_from_goal(self, goal_id, amount) -> SavingsGoal:
        goal = self._find_goal(goal_id)
        amt = validate_amount(amount)
        if amt > goal.saved:
            raise ValidationError("Cannot withdraw more than is saved.")
        goal.saved = round(goal.saved - amt, 2)
        goal.refresh_status()
        self._save()
        return goal

    def delete_goal(self, goal_id: str) -> None:
        before = len(self.goals)
        self.goals = [g for g in self.goals if g.id != goal_id]
        if len(self.goals) == before:
            raise NotFoundError("Goal not found.")
        self._save()

    def _find_goal(self, goal_id: str) -> SavingsGoal:
        for g in self.goals:
            if g.id == goal_id:
                return g
        raise NotFoundError("Goal not found.")

    # --- debts ----------------------------------------------------------

    def add_debt(self, direction, counterparty, amount, due_date=None,
                 description="") -> Debt:
        debt = Debt(
            direction=validate_choice(direction, DEBT_TYPES, field="direction"),
            counterparty=validate_text(counterparty, field="counterparty",
                                       max_length=80),
            amount=validate_amount(amount),
            due_date=validate_date(due_date, allow_empty=True),
            description=validate_text(description, field="description",
                                      required=False),
        )
        debt.refresh_status()
        self.debts.append(debt)
        self._save()
        return debt

    def pay_debt(self, debt_id, amount) -> Debt:
        debt = self._find_debt(debt_id)
        amt = validate_amount(amount)
        debt.amount_paid = round(min(debt.amount_paid + amt, debt.amount), 2)
        debt.refresh_status()
        self._save()
        return debt

    def delete_debt(self, debt_id: str) -> None:
        before = len(self.debts)
        self.debts = [d for d in self.debts if d.id != debt_id]
        if len(self.debts) == before:
            raise NotFoundError("Debt not found.")
        self._save()

    def _find_debt(self, debt_id: str) -> Debt:
        for d in self.debts:
            if d.id == debt_id:
                return d
        raise NotFoundError("Debt not found.")

    def list_debts(self, *, direction=None) -> list[Debt]:
        self._refresh_derived()
        items = self.debts
        if direction:
            items = [d for d in items if d.direction == direction]
        return sorted(items, key=lambda d: (d.status != "overdue",
                                             d.due_date or "9999"))

    # --- summaries & analytics -----------------------------------------

    def summary(self) -> dict:
        agg = analytics.totals(self.transactions)
        saved = round(sum(g.saved for g in self.goals), 2)
        owed_to_others = round(
            sum(d.outstanding for d in self.debts if d.direction == "borrowed"),
            2,
        )
        owed_to_user = round(
            sum(d.outstanding for d in self.debts if d.direction == "lent"), 2
        )
        return {
            "currency": self.currency,
            "total_income": agg["income"],
            "total_expense": agg["expense"],
            "total_savings": saved,
            "balance": agg["balance"],
            "debt_owed_to_others": owed_to_others,
            "debt_owed_to_user": owed_to_user,
            "net_worth": round(agg["balance"] + owed_to_user - owed_to_others, 2),
        }

    def spending_analysis(self) -> dict:
        return {
            "habits": analytics.spending_habits(self.transactions),
            "by_category": analytics.spending_by_category(self.transactions),
            "by_source": analytics.income_by_source(self.transactions),
            "trends": analytics.monthly_trends(self.transactions),
        }

    def health_score(self) -> dict:
        self._refresh_derived()
        return analytics.financial_health_score(
            self.transactions, self.goals, self.debts
        )

    # --- export ---------------------------------------------------------

    def export_report(self, path: str | Path, fmt: str = "json") -> Path:
        """Write a shareable report. Supported formats: json, csv, txt."""
        fmt = fmt.lower().strip()
        path = Path(path).expanduser()
        if path.parent != Path(""):
            path.parent.mkdir(parents=True, exist_ok=True)
        report = self._build_report()

        if fmt == "json":
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        elif fmt == "csv":
            self._export_csv(path, report)
        elif fmt == "txt":
            path.write_text(self._render_text_report(report), encoding="utf-8")
        else:
            raise ValidationError("Export format must be json, csv or txt.")
        return path

    def _build_report(self) -> dict:
        self._refresh_derived()
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "user": self.username,
            "currency": self.currency,
            "summary": self.summary(),
            "health_score": self.health_score(),
            "spending_analysis": self.spending_analysis(),
            "transactions": [t.to_dict() for t in self.list_transactions()],
            "budgets": [b.to_dict() for b in self.budgets],
            "goals": [g.to_dict() for g in self.goals],
            "debts": [d.to_dict() for d in self.debts],
        }

    def _export_csv(self, path: Path, report: dict) -> None:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["FinTrack report", report["generated_at"]])
            writer.writerow([])
            writer.writerow(["TRANSACTIONS"])
            writer.writerow(["date", "kind", "category", "amount", "description"])
            for t in report["transactions"]:
                writer.writerow([t["occurred_on"], t["kind"], t["category"],
                                 t["amount"], t["description"]])
            writer.writerow([])
            writer.writerow(["SUMMARY"])
            for key, val in report["summary"].items():
                writer.writerow([key, val])

    def _render_text_report(self, report: dict) -> str:
        cur = report["currency"]
        s = report["summary"]
        hs = report["health_score"]
        lines = [
            "=" * 52,
            "  FINTRACK FINANCIAL REPORT",
            f"  User: {report['user']}",
            f"  Generated: {report['generated_at']}",
            "=" * 52,
            "",
            "SUMMARY",
            "-" * 52,
            f"  Total income      : {cur}{s['total_income']:,.2f}",
            f"  Total expenses    : {cur}{s['total_expense']:,.2f}",
            f"  Total savings     : {cur}{s['total_savings']:,.2f}",
            f"  Remaining balance : {cur}{s['balance']:,.2f}",
            f"  Owed to others    : {cur}{s['debt_owed_to_others']:,.2f}",
            f"  Owed to you       : {cur}{s['debt_owed_to_user']:,.2f}",
            f"  Net worth         : {cur}{s['net_worth']:,.2f}",
            "",
            "FINANCIAL HEALTH",
            "-" * 52,
            f"  Score: {hs['score']}/100  Grade {hs['grade']} ({hs['label']})",
        ]
        for note in hs["notes"]:
            lines.append(f"    - {note}")
        lines += ["", "SPENDING BY CATEGORY", "-" * 52]
        for cat, amt in report["spending_analysis"]["by_category"].items():
            lines.append(f"  {cat:<16}{cur}{amt:,.2f}")
        lines.append("")
        return "\n".join(lines)
