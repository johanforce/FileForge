"""Shared exceptions for cooperatively cancellable background tasks."""


class TaskCancelledError(Exception):
    """Raised when a task observes a user cancellation request."""


def raise_if_cancelled(is_cancelled=None) -> None:
    """Abort the current operation when its cancellation callback returns true."""
    if is_cancelled is not None and is_cancelled():
        raise TaskCancelledError("Tác vụ đã được người dùng hủy.")
