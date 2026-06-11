"""FinTrack command-line interface.

A menu-driven terminal front-end built on `rich` for clean tables, panels and
prompts. It is a thin presentation layer: every action delegates to
:class:`fintrack.core.FinanceService`, so the CLI and GUI behave identically.
"""

from __future__ import annotations

import sys
from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import box

from ..core import AuthManager, FinanceService, JSONStore
from ..core.exceptions import FinTrackError
from ..core.validators import EXPENSE_CATEGORIES, INCOME_SOURCES

console = Console()


# --- small presentation helpers -----------------------------------------

def _money(svc: FinanceService, value: float) -> str:
    return f"{svc.currency}{value:,.2f}"


def _err(msg: str) -> None:
    console.print(f"[bold red]\u2717[/] {msg}")


def _ok(msg: str) -> None:
    console.print(f"[bold green]\u2713[/] {msg}")


def _ask(label: str, default=None) -> str:
    return Prompt.ask(f"[cyan]{label}[/]", default=default)


def _choice(label: str, choices) -> str:
    return Prompt.ask(f"[cyan]{label}[/]", choices=list(choices))


def _progress_bar(ratio: float, width: int = 12) -> str:
    filled = int(round(ratio * width))
    return "[green]" + "\u2588" * filled + "[/][dim]" + "\u2591" * (width - filled) + "[/]"


# --- authentication flow -------------------------------------------------

def _auth_screen(auth: AuthManager) -> str | None:
    console.print(Panel.fit(
        "[bold]FinTrack[/] \u00b7 Personal Finance Manager",
        subtitle="command-line edition", border_style="green",
    ))
    while True:
        action = Prompt.ask(
            "[cyan]Choose[/]",
            choices=["login", "register", "quit"], default="login",
        )
        if action == "quit":
            return None
        try:
            username = _ask("Username")
            password = Prompt.ask("[cyan]Password[/]", password=True)
            if action == "register":
                confirm = Prompt.ask("[cyan]Confirm password[/]", password=True)
                if confirm != password:
                    _err("Passwords do not match.")
                    continue
                user = auth.register(username, password)
                _ok(f"Account created. Welcome, {user}!")
                return user
            user = auth.authenticate(username, password)
            _ok(f"Welcome back, {user}!")
            return user
        except FinTrackError as exc:
            _err(str(exc))


# --- feature screens -----------------------------------------------------

def show_dashboard(svc: FinanceService) -> None:
    s = svc.summary()
    hs = svc.health_score()
    grade_colour = {"A": "green", "B": "green", "C": "yellow",
                    "D": "yellow", "E": "red"}.get(hs["grade"], "white")

    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row("Total income", f"[green]{_money(svc, s['total_income'])}[/]")
    table.add_row("Total expenses", f"[red]{_money(svc, s['total_expense'])}[/]")
    table.add_row("Total savings", _money(svc, s["total_savings"]))
    table.add_row("Remaining balance", f"[bold]{_money(svc, s['balance'])}[/]")
    table.add_row("Owed to others", _money(svc, s["debt_owed_to_others"]))
    table.add_row("Owed to you", _money(svc, s["debt_owed_to_user"]))
    table.add_row("Net worth", f"[bold]{_money(svc, s['net_worth'])}[/]")
    console.print(Panel(table, title="Summary", border_style="blue"))

    console.print(Panel(
        f"[bold {grade_colour}]{hs['score']}/100 \u00b7 Grade {hs['grade']} "
        f"({hs['label']})[/]\n" + "\n".join(f"\u2022 {n}" for n in hs["notes"]),
        title="Financial Health Score", border_style=grade_colour,
    ))

    warnings = svc.budget_warnings(date.today().strftime("%Y-%m"))
    if warnings:
        console.print(Panel("\n".join(f"\u26a0 {w}" for w in warnings),
                            title="Budget Alerts (this month)",
                            border_style="red"))


def add_transaction(svc: FinanceService, kind: str) -> None:
    try:
        amount = _ask("Amount")
        if kind == "income":
            cat = _choice("Source", INCOME_SOURCES)
        else:
            cat = _choice("Category", EXPENSE_CATEGORIES)
        desc = _ask("Description (optional)", default="")
        when = _ask("Date (YYYY-MM-DD)", default=date.today().isoformat())
        if kind == "income":
            svc.add_income(amount, cat, desc, when)
        else:
            svc.add_expense(amount, cat, desc, when)
        _ok(f"{kind.capitalize()} recorded.")
        if kind == "expense":
            for w in svc.budget_warnings(when[:7]):
                console.print(f"[red]\u26a0 {w}[/]")
    except FinTrackError as exc:
        _err(str(exc))


def list_transactions(svc: FinanceService) -> None:
    month = _ask("Filter by month YYYY-MM (blank = all)", default="")
    kind = Prompt.ask("[cyan]Type[/]", choices=["all", "income", "expense"],
                      default="all")
    try:
        txs = svc.list_transactions(
            kind=None if kind == "all" else kind,
            month=month or None,
        )
    except FinTrackError as exc:
        _err(str(exc))
        return
    if not txs:
        console.print("[dim]No transactions found.[/]")
        return
    table = Table(box=box.SIMPLE_HEAVY, header_style="bold cyan")
    for col in ("Date", "Type", "Category", "Amount", "Description", "ID"):
        table.add_column(col)
    for t in txs:
        colour = "green" if t.kind == "income" else "red"
        table.add_row(t.occurred_on, f"[{colour}]{t.kind}[/]", t.category,
                      f"[{colour}]{_money(svc, t.amount)}[/]",
                      t.description or "[dim]\u2014[/]", f"[dim]{t.id}[/]")
    console.print(table)


def search_transactions(svc: FinanceService) -> None:
    kw = _ask("Search keyword")
    results = svc.search_transactions(kw)
    if not results:
        console.print("[dim]No matches.[/]")
        return
    table = Table(box=box.SIMPLE, header_style="bold cyan")
    for col in ("Date", "Type", "Category", "Amount", "Description"):
        table.add_column(col)
    for t in results:
        table.add_row(t.occurred_on, t.kind, t.category,
                      _money(svc, t.amount), t.description or "\u2014")
    console.print(table)


def manage_budgets(svc: FinanceService) -> None:
    month = _ask("Budget month YYYY-MM", default=date.today().strftime("%Y-%m"))
    while True:
        try:
            rows = svc.budget_status(month)
        except FinTrackError as exc:
            _err(str(exc))
            return
        if rows:
            table = Table(title=f"Budgets \u00b7 {month}", box=box.SIMPLE_HEAVY,
                          header_style="bold cyan")
            for col in ("Category", "Limit", "Spent", "Remaining", "Used",
                        "Status", "ID"):
                table.add_column(col)
            colours = {"ok": "green", "warning": "yellow", "exceeded": "red"}
            for r in rows:
                c = colours[r["level"]]
                table.add_row(
                    r["category"], _money(svc, r["limit"]),
                    _money(svc, r["spent"]), _money(svc, r["remaining"]),
                    f"{r['ratio']*100:.0f}%", f"[{c}]{r['level']}[/]",
                    f"[dim]{r['id']}[/]",
                )
            console.print(table)
        else:
            console.print("[dim]No budgets set for this month.[/]")

        act = Prompt.ask("[cyan]Action[/]",
                         choices=["set", "delete", "back"], default="back")
        if act == "back":
            return
        try:
            if act == "set":
                cat = _ask("Category (or 'overall')")
                limit = _ask("Limit")
                svc.set_budget(month, cat, limit)
                _ok("Budget saved.")
            else:
                bid = _ask("Budget ID to delete")
                svc.delete_budget(bid)
                _ok("Budget deleted.")
        except FinTrackError as exc:
            _err(str(exc))


def manage_goals(svc: FinanceService) -> None:
    while True:
        if svc.goals:
            table = Table(title="Savings Goals", box=box.SIMPLE_HEAVY,
                          header_style="bold cyan")
            for col in ("Name", "Target", "Saved", "Progress", "Status",
                        "Deadline", "ID"):
                table.add_column(col)
            for g in svc.goals:
                bar = _progress_bar(g.progress)
                colour = "green" if g.status == "achieved" else "yellow"
                table.add_row(g.name, _money(svc, g.target),
                              _money(svc, g.saved),
                              f"{bar} {g.progress*100:.0f}%",
                              f"[{colour}]{g.status}[/]",
                              g.deadline or "\u2014", f"[dim]{g.id}[/]")
            console.print(table)
        else:
            console.print("[dim]No savings goals yet.[/]")

        act = Prompt.ask(
            "[cyan]Action[/]",
            choices=["add", "contribute", "withdraw", "delete", "back"],
            default="back",
        )
        if act == "back":
            return
        try:
            if act == "add":
                name = _ask("Goal name")
                target = _ask("Target amount")
                deadline = _ask("Deadline YYYY-MM-DD (optional)", default="")
                svc.add_goal(name, target, deadline or None)
                _ok("Goal created.")
            elif act in ("contribute", "withdraw"):
                gid = _ask("Goal ID")
                amount = _ask("Amount")
                if act == "contribute":
                    svc.contribute_to_goal(gid, amount)
                else:
                    svc.withdraw_from_goal(gid, amount)
                _ok("Goal updated.")
            else:
                gid = _ask("Goal ID to delete")
                svc.delete_goal(gid)
                _ok("Goal deleted.")
        except FinTrackError as exc:
            _err(str(exc))


def manage_debts(svc: FinanceService) -> None:
    while True:
        debts = svc.list_debts()
        if debts:
            table = Table(title="Debts", box=box.SIMPLE_HEAVY,
                          header_style="bold cyan")
            for col in ("Type", "Counterparty", "Amount", "Paid",
                        "Outstanding", "Due", "Status", "ID"):
                table.add_column(col)
            colours = {"paid": "green", "partly_paid": "yellow",
                       "pending": "white", "overdue": "red"}
            for d in debts:
                c = colours.get(d.status, "white")
                table.add_row(d.direction, d.counterparty,
                              _money(svc, d.amount), _money(svc, d.amount_paid),
                              _money(svc, d.outstanding), d.due_date or "\u2014",
                              f"[{c}]{d.status}[/]", f"[dim]{d.id}[/]")
            console.print(table)
        else:
            console.print("[dim]No debts recorded.[/]")

        act = Prompt.ask("[cyan]Action[/]",
                         choices=["add", "pay", "delete", "back"],
                         default="back")
        if act == "back":
            return
        try:
            if act == "add":
                direction = _choice("Direction", ("borrowed", "lent"))
                who = _ask("Counterparty (person)")
                amount = _ask("Amount")
                due = _ask("Due date YYYY-MM-DD (optional)", default="")
                desc = _ask("Note (optional)", default="")
                svc.add_debt(direction, who, amount, due or None, desc)
                _ok("Debt recorded.")
            elif act == "pay":
                did = _ask("Debt ID")
                amount = _ask("Payment amount")
                svc.pay_debt(did, amount)
                _ok("Payment recorded.")
            else:
                did = _ask("Debt ID to delete")
                svc.delete_debt(did)
                _ok("Debt deleted.")
        except FinTrackError as exc:
            _err(str(exc))


def show_analysis(svc: FinanceService) -> None:
    data = svc.spending_analysis()
    habits = data["habits"]
    if habits["highest_category"]:
        console.print(Panel(
            f"Highest spending : [red]{habits['highest_category']['category']}[/]"
            f" ({_money(svc, habits['highest_category']['amount'])})\n"
            f"Lowest spending  : {habits['lowest_category']['category']}"
            f" ({_money(svc, habits['lowest_category']['amount'])})\n"
            f"Average expense  : {_money(svc, habits['average_expense'])}\n"
            f"Categories used  : {habits['category_count']}",
            title="Spending Habits", border_style="magenta",
        ))

    if data["by_category"]:
        peak = max(data["by_category"].values())
        table = Table(title="Spending by Category", box=box.SIMPLE,
                      header_style="bold cyan")
        table.add_column("Category")
        table.add_column("Amount", justify="right")
        table.add_column("")
        for cat, amt in data["by_category"].items():
            bar = "\u2588" * int(round((amt / peak) * 24)) if peak else ""
            table.add_row(cat, _money(svc, amt), f"[blue]{bar}[/]")
        console.print(table)

    if data["trends"]:
        table = Table(title="Monthly Trends", box=box.SIMPLE,
                      header_style="bold cyan")
        for col in ("Month", "Income", "Expense", "Net"):
            table.add_column(col)
        for month, vals in data["trends"].items():
            net_colour = "green" if vals["net"] >= 0 else "red"
            table.add_row(month, _money(svc, vals["income"]),
                          _money(svc, vals["expense"]),
                          f"[{net_colour}]{_money(svc, vals['net'])}[/]")
        console.print(table)


def export_report(svc: FinanceService) -> None:
    fmt = Prompt.ask("[cyan]Format[/]", choices=["json", "csv", "txt"],
                     default="txt")
    default_name = f"fintrack_{svc.username}_report.{fmt}"
    path = _ask("Output path", default=default_name)
    try:
        out = svc.export_report(path, fmt)
        _ok(f"Report written to {out}")
    except FinTrackError as exc:
        _err(str(exc))


# --- main loop -----------------------------------------------------------

MENU = {
    "1": ("View dashboard", show_dashboard),
    "2": ("Add income", lambda s: add_transaction(s, "income")),
    "3": ("Add expense", lambda s: add_transaction(s, "expense")),
    "4": ("List / filter transactions", list_transactions),
    "5": ("Search transactions", search_transactions),
    "6": ("Budgets", manage_budgets),
    "7": ("Savings goals", manage_goals),
    "8": ("Debts", manage_debts),
    "9": ("Spending analysis", show_analysis),
    "10": ("Export report", export_report),
}


def run(data_dir: str | None = None) -> int:
    store = JSONStore(data_dir)
    auth = AuthManager(store)

    user = _auth_screen(auth)
    if not user:
        console.print("Goodbye.")
        return 0

    svc = FinanceService(user, store)
    show_dashboard(svc)

    while True:
        console.print()
        menu_table = Table.grid(padding=(0, 3))
        menu_table.add_column()
        menu_table.add_column()
        items = list(MENU.items())
        half = (len(items) + 1) // 2
        left_items = items[:half]
        right_items = items[half:] + [("0", ("Quit", None))]
        for left, right in zip(left_items, right_items):
            menu_table.add_row(f"[cyan]{left[0]:>2}[/] {left[1][0]}",
                               f"[cyan]{right[0]:>2}[/] {right[1][0]}")
        console.print(Panel(menu_table, title=f"FinTrack \u00b7 {user}",
                            border_style="green"))

        choice = Prompt.ask("[bold cyan]Select[/]",
                            choices=list(MENU) + ["0"], default="1")
        if choice == "0":
            if Confirm.ask("Quit FinTrack?", default=True):
                console.print("Goodbye.")
                return 0
            continue
        MENU[choice][1](svc)


def main() -> int:  # console-script entry point
    try:
        return run()
    except KeyboardInterrupt:
        console.print("\nInterrupted. Goodbye.")
        return 130
    except FinTrackError as exc:
        _err(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
