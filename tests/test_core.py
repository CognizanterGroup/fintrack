"""Core test suite for FinTrack.

Run with:  pytest    (from the project root)

These tests exercise the business-logic core - authentication, validation,
persistence, budgets, goals, debts, analytics and export - without needing a
display, so they run anywhere.
"""

from __future__ import annotations

import json

import pytest

from fintrack.core import AuthManager, FinanceService, JSONStore
from fintrack.core.exceptions import AuthError, NotFoundError, ValidationError


@pytest.fixture()
def store(tmp_path):
    return JSONStore(tmp_path / "data")


@pytest.fixture()
def svc(store):
    AuthManager(store).register("alice", "secret123")
    return FinanceService("alice", store)


# --- authentication ------------------------------------------------------

def test_register_and_authenticate(store):
    auth = AuthManager(store)
    auth.register("Bob", "password1")
    assert auth.authenticate("bob", "password1") == "bob"


def test_password_not_stored_plaintext(store):
    auth = AuthManager(store)
    auth.register("carol", "supersecret")
    raw = json.loads(store.users_path.read_text())
    assert "supersecret" not in json.dumps(raw)
    assert raw["carol"]["hash"] != "supersecret"


def test_wrong_password_rejected(store):
    auth = AuthManager(store)
    auth.register("dave", "rightpass")
    with pytest.raises(AuthError):
        auth.authenticate("dave", "wrongpass")


def test_duplicate_username_rejected(store):
    auth = AuthManager(store)
    auth.register("eve", "passpass")
    with pytest.raises(AuthError):
        auth.register("eve", "another1")


def test_short_password_rejected(store):
    with pytest.raises(ValidationError):
        AuthManager(store).register("frank", "123")


# --- validation ----------------------------------------------------------

def test_negative_amount_rejected(svc):
    with pytest.raises(ValidationError):
        svc.add_expense(-100, "food")


def test_invalid_category_rejected(svc):
    with pytest.raises(ValidationError):
        svc.add_expense(100, "not_a_category")


def test_invalid_date_rejected(svc):
    with pytest.raises(ValidationError):
        svc.add_income(100, "salary", "x", "not-a-date")


# --- transactions & persistence -----------------------------------------

def test_add_and_persist(store):
    AuthManager(store).register("gina", "passpass")
    svc = FinanceService("gina", store)
    svc.add_income(1000, "salary")
    svc.add_expense(300, "food")
    reloaded = FinanceService("gina", store)
    assert len(reloaded.transactions) == 2
    assert reloaded.summary()["balance"] == 700


def test_search_and_filter(svc):
    svc.add_income(1000, "freelance", "Logo design", "2025-06-01")
    svc.add_expense(200, "food", "Lunch", "2025-05-02")
    assert len(svc.search_transactions("logo")) == 1
    assert len(svc.list_transactions(month="2025-06")) == 1
    assert len(svc.list_transactions(kind="expense")) == 1


def test_delete_transaction(svc):
    tx = svc.add_expense(50, "food")
    svc.delete_transaction(tx.id)
    assert svc.transactions == []
    with pytest.raises(NotFoundError):
        svc.delete_transaction("missing")


# --- budgets -------------------------------------------------------------

def test_budget_warning_on_overspend(svc):
    svc.set_budget("2025-06", "food", 100)
    svc.add_expense(150, "food", "", "2025-06-10")
    warnings = svc.budget_warnings("2025-06")
    assert any("food" in w for w in warnings)
    status = svc.budget_status("2025-06")[0]
    assert status["level"] == "exceeded"


def test_budget_update_is_idempotent(svc):
    svc.set_budget("2025-06", "rent", 100)
    svc.set_budget("2025-06", "rent", 200)
    rows = [b for b in svc.budgets if b.category == "rent"]
    assert len(rows) == 1 and rows[0].limit == 200


# --- goals ---------------------------------------------------------------

def test_goal_progress_and_status(svc):
    g = svc.add_goal("Phone", 1000)
    svc.contribute_to_goal(g.id, 1000)
    g = svc._find_goal(g.id)
    assert g.progress == 1.0 and g.status == "achieved"


def test_cannot_overwithdraw_goal(svc):
    g = svc.add_goal("Bike", 1000)
    svc.contribute_to_goal(g.id, 200)
    with pytest.raises(ValidationError):
        svc.withdraw_from_goal(g.id, 500)


# --- debts ---------------------------------------------------------------

def test_debt_payment_and_status(svc):
    d = svc.add_debt("borrowed", "Sam", 500, None, "loan")
    svc.pay_debt(d.id, 500)
    d = svc._find_debt(d.id)
    assert d.outstanding == 0 and d.status == "paid"


def test_overdue_detection(svc):
    d = svc.add_debt("borrowed", "Old", 100, "2000-01-01")
    d = svc.list_debts()[0]
    assert d.status == "overdue"


# --- analytics & health --------------------------------------------------

def test_spending_habits(svc):
    svc.add_expense(300, "food", "", "2025-06-01")
    svc.add_expense(100, "transportation", "", "2025-06-02")
    habits = svc.spending_analysis()["habits"]
    assert habits["highest_category"]["category"] == "food"
    assert habits["lowest_category"]["category"] == "transportation"
    assert habits["average_expense"] == 200


def test_health_score_bounds(svc):
    svc.add_income(1000, "salary")
    svc.add_expense(200, "food")
    hs = svc.health_score()
    assert 0 <= hs["score"] <= 100
    assert hs["grade"] in {"A", "B", "C", "D", "E"}


# --- export --------------------------------------------------------------

@pytest.mark.parametrize("fmt", ["json", "csv", "txt"])
def test_export_formats(svc, tmp_path, fmt):
    svc.add_income(1000, "salary")
    out = svc.export_report(tmp_path / f"report.{fmt}", fmt)
    assert out.exists() and out.stat().st_size > 0
