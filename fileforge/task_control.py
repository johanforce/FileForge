"""Shared exceptions for cooperatively cancellable background tasks."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable


class TaskCancelledError(Exception):
    """Raised when a task observes a user cancellation request.

    Completed outputs are retained as metadata so the UI can report partial work
    without mistaking already-published output files for temporary files.
    """

    def __init__(
        self,
        message: str = "Tác vụ đã được người dùng hủy.",
        completed_outputs: Iterable[str | Path] = (),
    ):
        super().__init__(message)
        self.completed_outputs = [str(path) for path in completed_outputs]


def raise_if_cancelled(is_cancelled=None) -> None:
    """Abort the current operation when its cancellation callback returns true."""
    if is_cancelled is not None and is_cancelled():
        raise TaskCancelledError()
