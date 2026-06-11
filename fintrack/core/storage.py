"""JSON persistence layer.

All state lives in plain JSON files under a single data directory:

    <data_dir>/
        users.json            # credentials (hashed) keyed by username
        accounts/<user>.json  # one financial ledger per user

Writes are *atomic*: data is written to a temporary file and then
``os.replace``-d over the target, so a crash mid-write can never corrupt an
existing file. This is the durability guarantee the brief asks for.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .exceptions import StorageError


def default_data_dir() -> Path:
    """Per-OS application data directory (overridable via FINTRACK_DATA_DIR)."""
    env = os.environ.get("FINTRACK_DATA_DIR")
    if env:
        return Path(env).expanduser()
    home = Path.home()
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", home))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return base / "FinTrack"


class JSONStore:
    """Thin, safe wrapper around reading/writing JSON documents."""

    def __init__(self, data_dir: str | os.PathLike | None = None):
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self.accounts_dir = self.data_dir / "accounts"
        try:
            self.accounts_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - filesystem dependent
            raise StorageError(f"Could not create data directory: {exc}") from exc

    # --- low-level read / write -----------------------------------------

    def _read(self, path: Path, default):
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Failed to read {path.name}: {exc}") from exc

    def _write(self, path: Path, payload) -> None:
        try:
            # Write to a temp file in the same dir, then atomically replace.
            fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except OSError as exc:
            raise StorageError(f"Failed to write {path.name}: {exc}") from exc

    # --- users ----------------------------------------------------------

    @property
    def users_path(self) -> Path:
        return self.data_dir / "users.json"

    def load_users(self) -> dict:
        return self._read(self.users_path, {})

    def save_users(self, users: dict) -> None:
        self._write(self.users_path, users)

    # --- per-user accounts ----------------------------------------------

    def account_path(self, username: str) -> Path:
        return self.accounts_dir / f"{username}.json"

    def load_account(self, username: str) -> dict:
        return self._read(self.account_path(username), {})

    def save_account(self, username: str, data: dict) -> None:
        self._write(self.account_path(username), data)
