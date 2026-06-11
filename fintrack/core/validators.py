"""Input validation and domain constants.

Every value that enters the system from a human (CLI prompt or GUI field)
passes through one of these validators. They raise :class:`ValidationError`
with a clear message on bad input and return a normalised, typed value on
success, so the rest of the codebase can trust its inputs.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .exceptions import ValidationError

# --- Domain vocabularies -------------------------------------------------

INCOME_SOURCES = (
    "salary",
    "business",
    "freelance",
    "gift",
    "investment",
    "other",
)

EXPENSE_CATEGORIES = (
    "food",
    "transportation",
    "education",
    "health",
    "rent",
    "utilities",
    "entertainment",
    "business",
    "others",
)

DEBT_TYPES = ("borrowed", "lent")
DEBT_STATUSES = ("pending", "partly_paid", "paid", "overdue")
GOAL_STATUSES = ("active", "achieved")

MAX_AMOUNT = Decimal("1000000000000")  # 1 trillion sanity ceiling


# --- Validators ----------------------------------------------------------

def validate_amount(value, *, field: str = "amount") -> float:
    """Return a positive float, rounded to 2 dp, or raise ValidationError."""
    if value is None or value == "":
        raise ValidationError(f"{field.capitalize()} is required.")
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{field.capitalize()} must be a number.")
    if amount.is_nan() or amount.is_infinite():
        raise ValidationError(f"{field.capitalize()} must be a real number.")
    if amount <= 0:
        raise ValidationError(f"{field.capitalize()} must be greater than zero.")
    if amount > MAX_AMOUNT:
        raise ValidationError(f"{field.capitalize()} is unrealistically large.")
    return float(round(amount, 2))


def validate_non_negative_amount(value, *, field: str = "amount") -> float:
    """Like :func:`validate_amount` but allows exactly zero."""
    try:
        return validate_amount(value, field=field)
    except ValidationError:
        if str(value).strip() in ("0", "0.0", "0.00"):
            return 0.0
        raise


def validate_text(value, *, field: str, max_length: int = 200,
                  required: bool = True) -> str:
    """Strip and bound-check a free-text field."""
    text = (value or "").strip()
    if required and not text:
        raise ValidationError(f"{field.capitalize()} cannot be empty.")
    if len(text) > max_length:
        raise ValidationError(
            f"{field.capitalize()} must be {max_length} characters or fewer."
        )
    return text


def validate_choice(value, allowed, *, field: str) -> str:
    """Normalise a categorical value against an allowed vocabulary."""
    if value is None:
        raise ValidationError(f"{field.capitalize()} is required.")
    choice = str(value).strip().lower()
    if choice not in allowed:
        options = ", ".join(allowed)
        raise ValidationError(
            f"{field.capitalize()} must be one of: {options}."
        )
    return choice


def validate_date(value, *, field: str = "date", allow_empty: bool = False):
    """Accept a date / datetime / 'YYYY-MM-DD' string, return ISO date string."""
    if value in (None, ""):
        if allow_empty:
            return None
        raise ValidationError(f"{field.capitalize()} is required.")
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValidationError(
        f"{field.capitalize()} must be a valid date (e.g. 2025-06-15)."
    )


def validate_month(value, *, field: str = "month") -> str:
    """Validate a 'YYYY-MM' month string and return it normalised."""
    text = str(value).strip()
    try:
        parsed = datetime.strptime(text, "%Y-%m")
    except ValueError:
        raise ValidationError(
            f"{field.capitalize()} must be in YYYY-MM format (e.g. 2025-06)."
        )
    return parsed.strftime("%Y-%m")


def validate_username(value) -> str:
    """Usernames: 3-32 chars, letters/digits/underscore, case-insensitive."""
    name = (value or "").strip()
    if not name:
        raise ValidationError("Username is required.")
    if not 3 <= len(name) <= 32:
        raise ValidationError("Username must be 3-32 characters long.")
    if not all(c.isalnum() or c == "_" for c in name):
        raise ValidationError(
            "Username may only contain letters, numbers and underscores."
        )
    return name.lower()


def validate_password(value) -> str:
    """Enforce a minimal but real password policy."""
    pwd = value or ""
    if len(pwd) < 6:
        raise ValidationError("Password must be at least 6 characters long.")
    if pwd.strip() == "":
        raise ValidationError("Password cannot be blank.")
    return pwd
