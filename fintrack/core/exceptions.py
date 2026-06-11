"""Custom exception hierarchy for FinTrack.

Using domain-specific exceptions keeps error handling explicit and lets the
CLI and GUI front-ends present clean, user-facing messages instead of leaking
raw tracebacks.
"""


class FinTrackError(Exception):
    """Base class for every error raised by the FinTrack core."""


class ValidationError(FinTrackError):
    """Raised when user-supplied input fails a validation rule."""


class AuthError(FinTrackError):
    """Raised for authentication / registration failures."""


class StorageError(FinTrackError):
    """Raised when reading or writing the JSON data store fails."""


class NotFoundError(FinTrackError):
    """Raised when a referenced record (goal, debt, etc.) does not exist."""
