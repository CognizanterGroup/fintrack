"""Domain models.

Each entity is a dataclass that knows how to serialise itself to a plain dict
(for JSON storage) and rebuild itself from one. Identity is a short UUID so
records remain stable across edits and exports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, date


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Transaction:
    """A single income or expense entry.

    ``kind`` is either ``"income"`` or ``"expense"``. For income, ``category``
    holds the source (salary, freelance, ...); for expenses it holds the
    spending category (food, rent, ...). Sharing one model keeps the ledger and
    its analytics uniform.
    """

    kind: str
    amount: float
    category: str
    description: str = ""
    occurred_on: str = field(default_factory=lambda: date.today().isoformat())
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now)

    @property
    def month(self) -> str:
        return self.occurred_on[:7]  # 'YYYY-MM'

    @property
    def year(self) -> str:
        return self.occurred_on[:4]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(**data)


@dataclass
class Budget:
    """A spending limit for one category in one month.

    A ``category`` of ``"overall"`` represents a whole-month cap across every
    category.
    """

    month: str          # 'YYYY-MM'
    category: str        # expense category or 'overall'
    limit: float
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        return cls(**data)


@dataclass
class SavingsGoal:
    """A savings target with running progress."""

    name: str
    target: float
    saved: float = 0.0
    deadline: str | None = None
    status: str = "active"
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now)

    @property
    def progress(self) -> float:
        """Completion ratio in the range 0.0 - 1.0."""
        if self.target <= 0:
            return 0.0
        return min(self.saved / self.target, 1.0)

    @property
    def remaining(self) -> float:
        return max(self.target - self.saved, 0.0)

    def refresh_status(self) -> None:
        self.status = "achieved" if self.saved >= self.target else "active"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SavingsGoal":
        return cls(**data)


@dataclass
class Debt:
    """Money borrowed from, or lent to, another person."""

    direction: str       # 'borrowed' or 'lent'
    counterparty: str
    amount: float
    amount_paid: float = 0.0
    due_date: str | None = None
    status: str = "pending"
    description: str = ""
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now)

    @property
    def outstanding(self) -> float:
        return max(self.amount - self.amount_paid, 0.0)

    def refresh_status(self) -> None:
        """Recompute status from amounts paid and the due date."""
        if self.amount_paid >= self.amount:
            self.status = "paid"
            return
        overdue = (
            self.due_date is not None
            and self.due_date < date.today().isoformat()
        )
        if overdue:
            self.status = "overdue"
        elif self.amount_paid > 0:
            self.status = "partly_paid"
        else:
            self.status = "pending"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Debt":
        return cls(**data)
