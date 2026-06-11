"""FinTrack core package - shared business logic for the CLI and GUI."""

from .auth import AuthManager
from .exceptions import (
    AuthError,
    FinTrackError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from .models import Budget, Debt, SavingsGoal, Transaction
from .service import FinanceService
from .storage import JSONStore, default_data_dir

__all__ = [
    "AuthManager",
    "FinanceService",
    "JSONStore",
    "default_data_dir",
    "Transaction",
    "Budget",
    "SavingsGoal",
    "Debt",
    "FinTrackError",
    "ValidationError",
    "AuthError",
    "StorageError",
    "NotFoundError",
]
