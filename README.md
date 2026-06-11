<div align="center">

<img src="assets/logo.svg" alt="FinTrack logo" width="110">

# FinTrack

**Take control of your money.**

A fast, private, open-source personal finance manager for the desktop —
track income & expenses, set budgets, hit savings goals and watch your
financial health score climb.

[![CI](https://github.com/CognizanterGroup/fintrack/actions/workflows/ci.yml/badge.svg)](https://github.com/CognizanterGroup/fintrack/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Made with PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-41cd52.svg)](https://doc.qt.io/qtforpython-6/)

</div>

---

## 📥 Download the desktop app

**[⬇ Download the latest release](https://github.com/CognizanterGroup/fintrack/releases/latest)** —
prebuilt, no Python required. Available for:

| Platform | File |
| --- | --- |
| 🪟 Windows | `FinTrack-windows.zip` — unzip and run `FinTrack.exe` |
| 🍎 macOS | `FinTrack-macos.zip` — unzip and open `FinTrack.app` |
| 🐧 Linux | `FinTrack-linux.tar.gz` — extract and run `FinTrack/FinTrack` |

> Your data never leaves your machine — FinTrack stores everything in local
> JSON files. No cloud, no account, no tracking.

---

## ✨ Features

- 🖥️ **Full-screen home page** — register or log in, then you're straight
  into a polished dashboard
- 💸 **Income & expenses** with sources/categories, descriptions and dates
- 📊 **Monthly budgets** (per category or overall) with overspend warnings
- 🎯 **Savings goals** with progress tracking and an "achieved" state
- 🤝 **Debt management** (borrowed / lent) with due dates, payment status and
  automatic overdue detection
- 📈 **Spending analysis** — highest/lowest category, averages, monthly trends,
  native Qt charts (donut + grouped bars)
- ❤️ **Financial Health Score (0–100, A–E)** blending savings rate, living
  within means, debt load and goal progress
- 🔎 **Search & filter** by keyword, month or type
- 📤 **Export reports** to TXT, CSV or JSON
- 🔐 **Multi-user with authentication** — passwords hashed with
  PBKDF2-HMAC-SHA256 (200k iterations); each user's data is isolated
- 💾 **Crash-safe JSON persistence** via atomic writes
- ⌨️ **Two front-ends, one core** — the desktop GUI and a full terminal UI
  share the same `FinanceService`, so behaviour and data are identical

> Default currency is the Naira (₦) and is configurable in Settings.

---

## 🚀 Run from source

Requires Python 3.10+.

```bash
git clone https://github.com/CognizanterGroup/fintrack.git
cd fintrack

# GUI + CLI (recommended)
pip install ".[gui]"

# CLI only (no Qt dependency)
pip install .
```

Then launch:

```bash
fintrack            # desktop GUI (default)
fintrack --cli      # terminal interface
fintrack-gui        # GUI shortcut
fintrack-cli        # CLI shortcut
```

Or run without installing, straight from the project root:

```bash
python -m fintrack            # GUI
python -m fintrack --cli      # CLI
```

### Try the demo account

A demo user with three months of realistic activity ships in `sample_data/`:

```bash
fintrack --data-dir sample_data/data
```

Log in as **`demo` / `demo1234`**. Regenerate the sample data any time with
`python seed_sample_data.py`.

---

## 🏗️ Architecture

```
fintrack/
├── core/                 shared business logic (no UI, fully tested)
│   ├── models.py         Transaction, Budget, SavingsGoal, Debt (dataclasses)
│   ├── validators.py     input validation + the allowed sources/categories
│   ├── storage.py        JSONStore — atomic, per-user JSON persistence
│   ├── auth.py           AuthManager — PBKDF2 password hashing
│   ├── analytics.py      pure functions: trends, habits, health score
│   ├── service.py        FinanceService — the facade both UIs call
│   └── exceptions.py     typed error hierarchy
├── cli/
│   └── app.py            rich-powered menu interface
├── gui/                  PySide6 desktop app
│   ├── app.py            entry point (home page → main window)
│   ├── home.py           full-screen landing page with register / login
│   ├── icons.py          vector icon set + the FinTrack logo (no binaries)
│   ├── theme.py          palette + Qt stylesheet
│   ├── main_window.py    sidebar navigation + stacked pages
│   ├── pages.py          dashboard, transactions, budgets, goals, debts, …
│   ├── dialogs.py        modal input forms
│   ├── charts.py         QtCharts donut + bar builders
│   └── widgets.py        reusable cards / stat tiles / pills
└── __main__.py           dual-entry router (GUI vs CLI)
```

The key design point: **the CLI and GUI never duplicate logic.** Adding income,
warning about a budget, scoring financial health — all of it lives in
`FinanceService`, so the two front-ends can't drift apart and there is a single
place to test.

### Data & files

Data lives in a per-OS application directory by default. Override with
`--data-dir` or the `FINTRACK_DATA_DIR` environment variable:

```
<data_dir>/
├── users.json                 credentials (salted PBKDF2 hashes only)
└── accounts/
    └── <username>.json        that user's transactions, budgets, goals, debts
```

Writes are atomic (write-to-temp then replace), so an interrupted save can't
corrupt your data.

### Why PySide6 (not PyQt6)?

Both wrap the same Qt libraries, but **PySide6 is LGPL**, which permits
bundling and distributing the app without licensing friction. PyQt6 is
GPL-or-commercial. For a distributable desktop product PySide6 is the
pragmatic choice.

---

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest
```

Covers authentication, validation, persistence, search/filter, budgets, goals,
debts, analytics, the health score and all three export formats. The suite is
headless and runs without a display. CI runs it on Windows, macOS and Linux.

---

## 📦 Building the desktop app yourself

Releases are built automatically by
[`release.yml`](.github/workflows/release.yml) when a `v*` tag is pushed.
To build locally:

```bash
pip install ".[build]"
pyinstaller --noconfirm --windowed --name FinTrack \
    --icon assets/icon.ico packaging/fintrack_entry.py
# result: dist/FinTrack/
```

The app icon is generated from the in-code logo — after changing the brand
mark in `fintrack/gui/icons.py`, run `python scripts/make_icons.py`.

---

## 🤝 Contributing

Contributions are very welcome! Please read
[CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, project
conventions and the PR checklist, and our
[Code of Conduct](CODE_OF_CONDUCT.md).

Good first contributions: new export formats, more chart types, translations,
currency presets, packaging improvements.

---

## 📄 License

[MIT](LICENSE) © FinTrack contributors
