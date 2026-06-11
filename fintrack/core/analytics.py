"""Analytics and the Financial Health Score.

These are pure functions over a list of :class:`Transaction` objects plus the
user's goals and debts. Keeping them side-effect free makes them easy to test
and reuse from both front-ends.
"""

from __future__ import annotations

from collections import defaultdict

from .models import Transaction, SavingsGoal, Debt


def totals(transactions: list[Transaction]) -> dict:
    """Aggregate income, expense and balance figures."""
    income = sum(t.amount for t in transactions if t.kind == "income")
    expense = sum(t.amount for t in transactions if t.kind == "expense")
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(income - expense, 2),
    }


def spending_by_category(transactions: list[Transaction]) -> dict[str, float]:
    """Total expense amount per category, highest first."""
    buckets: dict[str, float] = defaultdict(float)
    for t in transactions:
        if t.kind == "expense":
            buckets[t.category] += t.amount
    return dict(sorted(buckets.items(), key=lambda kv: kv[1], reverse=True))


def income_by_source(transactions: list[Transaction]) -> dict[str, float]:
    buckets: dict[str, float] = defaultdict(float)
    for t in transactions:
        if t.kind == "income":
            buckets[t.category] += t.amount
    return dict(sorted(buckets.items(), key=lambda kv: kv[1], reverse=True))


def spending_habits(transactions: list[Transaction]) -> dict:
    """Highest/lowest categories, average expense, and category count."""
    by_cat = spending_by_category(transactions)
    expenses = [t for t in transactions if t.kind == "expense"]
    if not by_cat:
        return {
            "highest_category": None,
            "lowest_category": None,
            "average_expense": 0.0,
            "category_count": 0,
            "by_category": {},
        }
    highest = max(by_cat.items(), key=lambda kv: kv[1])
    lowest = min(by_cat.items(), key=lambda kv: kv[1])
    avg = sum(t.amount for t in expenses) / len(expenses)
    return {
        "highest_category": {"category": highest[0], "amount": round(highest[1], 2)},
        "lowest_category": {"category": lowest[0], "amount": round(lowest[1], 2)},
        "average_expense": round(avg, 2),
        "category_count": len(by_cat),
        "by_category": by_cat,
    }


def monthly_trends(transactions: list[Transaction]) -> dict[str, dict]:
    """Income / expense / net per month, ordered chronologically."""
    months: dict[str, dict] = defaultdict(
        lambda: {"income": 0.0, "expense": 0.0}
    )
    for t in transactions:
        months[t.month][t.kind] += t.amount
    ordered = {}
    for m in sorted(months):
        inc = round(months[m]["income"], 2)
        exp = round(months[m]["expense"], 2)
        ordered[m] = {"income": inc, "expense": exp, "net": round(inc - exp, 2)}
    return ordered


def financial_health_score(
    transactions: list[Transaction],
    goals: list[SavingsGoal],
    debts: list[Debt],
) -> dict:
    """Rate overall financial condition from 0-100 across four dimensions.

    The score blends four well-understood personal-finance signals:

    * Savings rate   (40 pts) - what fraction of income is kept.
    * Budget surplus (20 pts) - whether the user lives within their means.
    * Debt load      (25 pts) - outstanding borrowing relative to income.
    * Goal progress  (15 pts) - momentum toward stated savings goals.

    Returns the total, a letter grade, the component breakdown, and short notes
    so a front-end can explain *why* the score is what it is.
    """
    agg = totals(transactions)
    income, expense = agg["income"], agg["expense"]

    notes: list[str] = []

    # 1) Savings rate ----------------------------------------------------
    if income > 0:
        savings_rate = max((income - expense) / income, 0.0)
    else:
        savings_rate = 0.0
    savings_pts = round(min(savings_rate / 0.20, 1.0) * 40, 1)  # 20%+ = full
    if income <= 0:
        notes.append("No income recorded yet - add income to assess savings.")
    elif savings_rate >= 0.20:
        notes.append("Strong savings rate (20%+ of income kept).")
    else:
        notes.append(f"Savings rate is {savings_rate*100:.0f}%; aim for 20%+.")

    # 2) Living within means --------------------------------------------
    if income <= 0:
        budget_pts = 0.0
    elif expense <= income:
        budget_pts = 20.0
    else:
        overspend = (expense - income) / income
        budget_pts = round(max(20 * (1 - overspend), 0.0), 1)
        notes.append("Spending exceeds income this period.")

    # 3) Debt load -------------------------------------------------------
    borrowed_out = sum(
        d.outstanding for d in debts if d.direction == "borrowed"
    )
    if income <= 0:
        debt_pts = 12.5 if borrowed_out == 0 else 0.0
    else:
        ratio = borrowed_out / income
        debt_pts = round(max(25 * (1 - min(ratio, 1.0)), 0.0), 1)
    if borrowed_out > 0:
        notes.append(f"Outstanding debt owed: {borrowed_out:,.2f}.")
    else:
        notes.append("No outstanding debt - excellent.")

    # 4) Goal progress ---------------------------------------------------
    if goals:
        avg_progress = sum(g.progress for g in goals) / len(goals)
        goal_pts = round(avg_progress * 15, 1)
        notes.append(f"Average goal progress: {avg_progress*100:.0f}%.")
    else:
        goal_pts = 0.0
        notes.append("No savings goals set yet.")

    total = round(savings_pts + budget_pts + debt_pts + goal_pts, 1)

    if total >= 85:
        grade, label = "A", "Excellent"
    elif total >= 70:
        grade, label = "B", "Good"
    elif total >= 55:
        grade, label = "C", "Fair"
    elif total >= 40:
        grade, label = "D", "Needs attention"
    else:
        grade, label = "E", "At risk"

    return {
        "score": total,
        "grade": grade,
        "label": label,
        "components": {
            "savings": {"points": savings_pts, "max": 40},
            "budget": {"points": budget_pts, "max": 20},
            "debt": {"points": debt_pts, "max": 25},
            "goals": {"points": goal_pts, "max": 15},
        },
        "notes": notes,
    }
