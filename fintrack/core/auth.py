"""Authentication.

Passwords are never stored in plaintext. Each user gets a random 16-byte salt
and the password is stretched with PBKDF2-HMAC-SHA256 (200k iterations). Only
the salt and derived hash are persisted. Verification is constant-time via
``hmac.compare_digest``.

PBKDF2 is used deliberately: it ships in the standard library, so the app has
no security-critical third-party dependency and remains trivially installable.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime

from .exceptions import AuthError
from .storage import JSONStore
from .validators import validate_password, validate_username

_ITERATIONS = 200_000
_ALGO = "sha256"


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    return dk.hex()


class AuthManager:
    """Registers users and verifies credentials against the JSON store."""

    def __init__(self, store: JSONStore):
        self.store = store

    def user_exists(self, username: str) -> bool:
        username = validate_username(username)
        return username in self.store.load_users()

    def register(self, username: str, password: str) -> str:
        """Create a new account. Returns the normalised username."""
        username = validate_username(username)
        password = validate_password(password)

        users = self.store.load_users()
        if username in users:
            raise AuthError(f"Username '{username}' is already taken.")

        salt = os.urandom(16)
        users[username] = {
            "salt": salt.hex(),
            "hash": _hash_password(password, salt),
            "iterations": _ITERATIONS,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.store.save_users(users)
        # Initialise an empty ledger for the new user.
        if not self.store.account_path(username).exists():
            self.store.save_account(username, {})
        return username

    def authenticate(self, username: str, password: str) -> str:
        """Verify credentials. Returns the username on success."""
        try:
            username = validate_username(username)
        except Exception:
            raise AuthError("Invalid username or password.")

        users = self.store.load_users()
        record = users.get(username)
        if not record:
            # Run a dummy hash to keep timing roughly uniform.
            _hash_password(password or "", os.urandom(16))
            raise AuthError("Invalid username or password.")

        salt = bytes.fromhex(record["salt"])
        expected = record["hash"]
        candidate = _hash_password(password or "", salt)
        if not hmac.compare_digest(candidate, expected):
            raise AuthError("Invalid username or password.")
        return username

    def change_password(self, username: str, old: str, new: str) -> None:
        self.authenticate(username, old)
        new = validate_password(new)
        users = self.store.load_users()
        salt = os.urandom(16)
        users[username]["salt"] = salt.hex()
        users[username]["hash"] = _hash_password(new, salt)
        self.store.save_users(users)
