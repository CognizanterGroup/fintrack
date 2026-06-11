# Contributing to FinTrack

Thanks for your interest in improving FinTrack! Contributions of all kinds are
welcome — bug reports, feature ideas, documentation fixes and code.

## Getting set up

Requires Python 3.10+.

```bash
git clone https://github.com/<your-fork>/fintrack.git
cd fintrack
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[gui,dev]"
```

Run the app against the bundled demo data while developing:

```bash
python -m fintrack --data-dir sample_data/data    # log in as demo / demo1234
```

## Running the tests

```bash
pytest
```

The suite covers the entire `fintrack/core` package and runs headless. Please
add or update tests for any change to core behaviour — `tests/test_core.py`
shows the patterns used.

## Project layout in 30 seconds

- `fintrack/core/` — all business logic. **No UI imports allowed here.**
- `fintrack/gui/` — PySide6 desktop front-end (thin layer over `FinanceService`).
- `fintrack/cli/` — rich-powered terminal front-end (same rule).

The golden rule: **the CLI and GUI never duplicate logic.** If a feature needs
new behaviour, put it in `FinanceService` and call it from both front-ends.

## Making a change

1. Fork the repo and create a branch: `git checkout -b my-fix`.
2. Make your change, with tests where it touches `core/`.
3. Run `pytest` and make sure everything passes.
4. Open a pull request with a clear description of *what* and *why*.

Small, focused PRs are reviewed fastest. If you're planning something large,
please open an issue first so we can discuss the approach.

## Regenerating assets

The app icon and logo are defined in code (`fintrack/gui/icons.py`) and
mirrored in `assets/`. After changing the brand mark, regenerate the bundled
icons with:

```bash
python scripts/make_icons.py
```

## Reporting bugs

Open an issue with your OS, Python version, what you did, what you expected
and what happened instead. If the app crashed, include the traceback.

## Code of conduct

By participating you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).
