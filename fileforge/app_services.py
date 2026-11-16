"""Desktop application services: app-data paths, rotating logs and task history."""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QStandardPaths


def app_data_directory() -> Path:
    """Return the per-user application data directory, creating it if needed."""
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    directory = Path(location).expanduser() if location else Path.home() / ".fileforge"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def configure_app_logging(data_directory: Path | None = None) -> logging.Logger:
    """Configure a small rotating diagnostic log without duplicating handlers."""
    directory = data_directory or app_data_directory()
    log_directory = directory / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("FileForge")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(getattr(handler, "_fileforge_handler", False) for handler in logger.handlers):
        handler = RotatingFileHandler(
            log_directory / "fileforge.log",
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler._fileforge_handler = True
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger


def install_exception_logging(logger: logging.Logger) -> None:
    """Write uncaught Python exceptions to the diagnostic log before delegation."""
    previous_hook = sys.excepthook

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            previous_hook(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "Unhandled application exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        previous_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception


class TaskHistoryStore:
    """SQLite-backed task history; stores metadata, never file or editor contents."""

    def __init__(self, database_path: str | Path, max_entries: int = 500):
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_entries = max(1, int(max_entries))
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_count INTEGER NOT NULL DEFAULT 0,
                    input_names_json TEXT NOT NULL DEFAULT '[]',
                    output_paths_json TEXT NOT NULL DEFAULT '[]',
                    output_folder TEXT NOT NULL DEFAULT '',
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    summary TEXT NOT NULL DEFAULT '',
                    error_message TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_history_created "
                "ON task_history(created_at DESC)"
            )

    @staticmethod
    def _as_input_names(inputs: Iterable[str | Path]) -> list[str]:
        return [Path(value).name or str(value) for value in inputs]

    @staticmethod
    def _as_paths(paths: Iterable[str | Path]) -> list[str]:
        return [str(Path(value).expanduser()) for value in paths if str(value)]

    def record(
        self,
        operation: str,
        status: str,
        inputs: Iterable[str | Path] = (),
        outputs: Iterable[str | Path] = (),
        output_folder: str | Path = "",
        duration_ms: int = 0,
        summary: str = "",
        error_message: str = "",
    ) -> int:
        """Append one task record and retain only the newest configured entries."""
        input_names = self._as_input_names(inputs)
        output_paths = self._as_paths(outputs)
        created_at = datetime.now().astimezone().isoformat(timespec="seconds")
        normalized_status = status if status in {"success", "partial", "failed"} else "failed"

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO task_history (
                    created_at, operation, status, input_count, input_names_json,
                    output_paths_json, output_folder, duration_ms, summary, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    str(operation)[:120],
                    normalized_status,
                    len(input_names),
                    json.dumps(input_names, ensure_ascii=False),
                    json.dumps(output_paths, ensure_ascii=False),
                    str(output_folder)[:2000],
                    max(0, int(duration_ms)),
                    str(summary)[:1000],
                    str(error_message)[:8000],
                ),
            )
            record_id = int(cursor.lastrowid)
            connection.execute(
                """
                DELETE FROM task_history
                WHERE id NOT IN (
                    SELECT id FROM task_history ORDER BY id DESC LIMIT ?
                )
                """,
                (self.max_entries,),
            )
        return record_id

    def recent(self, limit: int = 500) -> list[dict]:
        """Return newest tasks first, decoding the metadata JSON columns."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM task_history ORDER BY id DESC LIMIT ?",
                (max(1, min(int(limit), self.max_entries)),),
            ).fetchall()

        records = []
        for row in rows:
            item = dict(row)
            try:
                item["input_names"] = json.loads(item.pop("input_names_json"))
            except (TypeError, ValueError):
                item["input_names"] = []
            try:
                item["output_paths"] = json.loads(item.pop("output_paths_json"))
            except (TypeError, ValueError):
                item["output_paths"] = []
            records.append(item)
        return records

    def clear(self) -> None:
        """Delete all user-visible task history."""
        with self._connect() as connection:
            connection.execute("DELETE FROM task_history")
            connection.execute(
                "DELETE FROM sqlite_sequence WHERE name = 'task_history'"
            )
