#!/usr/bin/env python3
"""Generate realistic sample data for FinTrack.

Running this script populates a data directory with a demo user and several
months of transactions, budgets, savings goals and debts, then writes a sample
exported report. It is used to produce the bundled ``sample_data/`` files and is
handy for trying the app without entering data by hand.

    python seed_sample_data.py [data_dir]

Default data_dir: ./sample_data/data
Demo login:  username "demo"   password "demo1234"
"""

from __future__ import annotations

import sys
from pathlib import Path

from fintrack.core import AuthManager, FinanceService, JSONStore


def seed(data_dir: str) -> None:
    store = JSONStore(data_dir)
    auth = AuthManager(store)

    username = "demo"
    if not auth.user_exists(username):
        auth.register(username, "demo1234")
    svc = FinanceService(username, store)

    # Start clean so re-running is idempotent.
    svc.transactions.clear()
    svc.budgets.clear()
    svc.goals.clear()
    svc.debts.clear()

    # --- Income across three months -----------------------------------
    income = [
        ("2025-04-01", 450000, "salary", "April salary"),
        ("2025-04-18", 90000, "freelance", "Website project"),
        ("2025-05-01", 450000, "salary", "May salary"),
        ("2025-05-22", 60000, "business", "Side shop sales"),
        ("2025-06-01", 480000, "salary", "June salary (raise)"),
        ("2025-06-09", 120000, "freelance", "Logo + brand kit"),
        ("2025-06-15", 25000, "gift", "Birthday gift"),
        ("2025-06-20", 40000, "investment", "Dividend payout"),
    ]
    for d, amt, src, note in income:
        svc.add_income(amt, src, note, d)

    # --- Expenses ------------------------------------------------------
    expenses = [
        ("2025-04-03", 120000, "rent", "Apartment rent"),
        ("2025-04-06", 42000, "food", "Groceries"),
        ("2025-04-12", 18000, "transportation", "Fuel"),
        ("2025-04-20", 15000, "utilities", "Electricity"),
        ("2025-05-03", 120000, "rent", "Apartment rent"),
        ("2025-05-08", 38000, "food", "Groceries"),
        ("2025-05-14", 22000, "health", "Pharmacy + checkup"),
        ("2025-05-19", 12000, "entertainment", "Cinema + dinner"),
        ("2025-05-25", 30000, "education", "Online course"),
        ("2025-06-03", 120000, "rent", "Apartment rent"),
        ("2025-06-06", 47000, "food", "Groceries + dining"),
        ("2025-06-10", 20000, "transportation", "Ride-hailing"),
        ("2025-06-12", 16000, "utilities", "Internet + electricity"),
        ("2025-06-18", 25000, "business", "Software subscriptions"),
        ("2025-06-22", 14000, "entertainment", "Concert ticket"),
    ]
    for d, amt, cat, note in expenses:
        svc.add_expense(amt, cat, note, d)

    # --- Budgets for the current sample month --------------------------
    svc.set_budget("2025-06", "overall", 360000)
    svc.set_budget("2025-06", "food", 40000)          # deliberately exceeded
    svc.set_budget("2025-06", "transportation", 25000)
    svc.set_budget("2025-06", "entertainment", 20000)

    # --- Savings goals -------------------------------------------------
    laptop = svc.add_goal("New Laptop", 600000, "2025-12-31")
    svc.contribute_to_goal(laptop.id, 220000)
    emergency = svc.add_goal("Emergency Fund", 500000, "2026-06-30")
    svc.contribute_to_goal(emergency.id, 175000)
    trip = svc.add_goal("Holiday Trip", 300000, "2025-11-01")
    svc.contribute_to_goal(trip.id, 300000)  # achieved

    # --- Debts ---------------------------------------------------------
    loan = svc.add_debt("borrowed", "Ada", 80000, "2025-05-15",
                        "Short-term loan")
    svc.pay_debt(loan.id, 30000)  # partly paid + overdue
    svc.add_debt("borrowed", "Cooperative", 150000, "2025-09-30",
                 "Equipment financing")
    lent = svc.add_debt("lent", "Tunde", 40000, "2025-07-10",
                        "Lent for rent")
    svc.pay_debt(lent.id, 40000)  # fully repaid to user

    # --- Sample exported report ---------------------------------------
    reports_dir = Path(data_dir).parent
    svc.export_report(reports_dir / "sample_report.txt", "txt")
    svc.export_report(reports_dir / "sample_report.json", "json")
    svc.export_report(reports_dir / "sample_report.csv", "csv")

    s = svc.summary()
    print("Seeded sample data for user 'demo' (password: demo1234)")
    print(f"  data dir : {Path(data_dir).resolve()}")
    print(f"  income   : {s['currency']}{s['total_income']:,.2f}")
    print(f"  expenses : {s['currency']}{s['total_expense']:,.2f}")
    print(f"  balance  : {s['currency']}{s['balance']:,.2f}")
    print(f"  health   : {svc.health_score()['score']}/100 "
          f"({svc.health_score()['grade']})")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "sample_data/data"
    seed(target)
