from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _utcnow() -> datetime:
    """Naive UTC timestamp for portable DuckDB TIMESTAMP storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _duckdb():
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError(
            "DuckDB is required for WAP_AS run history. Install it with `pip install duckdb`."
        ) from exc
    return duckdb


class RunRepository:
    """Small DuckDB-backed operational repository for PIQITT runs."""

    def __init__(self, db_path: str | Path = "data/piqitt_runs.duckdb") -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = _duckdb().connect(str(self.db_path))
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "RunRepository":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id VARCHAR PRIMARY KEY,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR,
                input_type VARCHAR,
                input_path VARCHAR,
                profile VARCHAR,
                file_count BIGINT,
                message_count BIGINT,
                mean_piqi DOUBLE,
                critical_failure_count BIGINT,
                elapsed_seconds DOUBLE,
                piqitt_version VARCHAR,
                config_snapshot VARCHAR,
                error_message VARCHAR
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_files (
                run_id VARCHAR,
                file_id VARCHAR,
                file_path VARCHAR,
                file_name VARCHAR,
                file_size_bytes BIGINT,
                status VARCHAR,
                detected_message_type VARCHAR,
                message_count BIGINT,
                mean_piqi DOUBLE,
                critical_failure_count BIGINT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                elapsed_seconds DOUBLE,
                error_message VARCHAR,
                PRIMARY KEY (run_id, file_id)
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_findings (
                run_id VARCHAR,
                file_id VARCHAR,
                profile VARCHAR,
                step_id VARCHAR,
                sam VARCHAR,
                dimension VARCHAR,
                status VARCHAR,
                finding_count BIGINT
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_artifacts (
                run_id VARCHAR,
                file_id VARCHAR,
                artifact_type VARCHAR,
                artifact_path VARCHAR,
                created_at TIMESTAMP,
                size_bytes BIGINT
            )
            """
        )

    def create_run(
        self,
        *,
        run_id: str,
        input_type: str,
        input_path: str,
        profile: str,
        file_count: int,
        piqitt_version: Optional[str],
        config_snapshot: Dict[str, Any],
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO runs (
                run_id, started_at, status, input_type, input_path, profile,
                file_count, message_count, mean_piqi, critical_failure_count,
                elapsed_seconds, piqitt_version, config_snapshot, error_message
            ) VALUES (?, ?, 'RUNNING', ?, ?, ?, ?, 0, NULL, 0, 0, ?, ?, NULL)
            """,
            [
                run_id,
                _utcnow(),
                input_type,
                input_path,
                profile,
                file_count,
                piqitt_version,
                json.dumps(config_snapshot, sort_keys=True),
            ],
        )

    def finish_run(
        self,
        *,
        run_id: str,
        status: str,
        message_count: int,
        mean_piqi: Optional[float],
        critical_failure_count: int,
        elapsed_seconds: float,
        error_message: Optional[str] = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET completed_at = ?, status = ?, message_count = ?, mean_piqi = ?,
                critical_failure_count = ?, elapsed_seconds = ?, error_message = ?
            WHERE run_id = ?
            """,
            [
                _utcnow(),
                status,
                message_count,
                mean_piqi,
                critical_failure_count,
                elapsed_seconds,
                error_message,
                run_id,
            ],
        )

    def register_file(
        self,
        *,
        run_id: str,
        file_id: str,
        file_path: str,
        file_name: str,
        file_size_bytes: int,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO run_files (
                run_id, file_id, file_path, file_name, file_size_bytes, status,
                message_count, critical_failure_count
            ) VALUES (?, ?, ?, ?, ?, 'PENDING', 0, 0)
            """,
            [run_id, file_id, file_path, file_name, file_size_bytes],
        )

    def start_file(self, *, run_id: str, file_id: str) -> None:
        self.conn.execute(
            """
            UPDATE run_files
            SET status = 'RUNNING', started_at = ?
            WHERE run_id = ? AND file_id = ?
            """,
            [_utcnow(), run_id, file_id],
        )

    def update_progress(
        self,
        *,
        run_id: str,
        file_id: str,
        file_message_count: int,
        file_mean_piqi: Optional[float],
        file_critical_failure_count: int,
        run_message_count: int,
        run_mean_piqi: Optional[float],
        run_critical_failure_count: int,
    ) -> None:
        self.conn.execute(
            """
            UPDATE run_files
            SET message_count = ?, mean_piqi = ?, critical_failure_count = ?
            WHERE run_id = ? AND file_id = ?
            """,
            [
                file_message_count,
                file_mean_piqi,
                file_critical_failure_count,
                run_id,
                file_id,
            ],
        )
        self.conn.execute(
            """
            UPDATE runs
            SET message_count = ?, mean_piqi = ?, critical_failure_count = ?
            WHERE run_id = ?
            """,
            [
                run_message_count,
                run_mean_piqi,
                run_critical_failure_count,
                run_id,
            ],
        )

    def finish_file(
        self,
        *,
        run_id: str,
        file_id: str,
        status: str,
        detected_message_type: Optional[str],
        message_count: int,
        mean_piqi: Optional[float],
        critical_failure_count: int,
        elapsed_seconds: float,
        error_message: Optional[str] = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE run_files
            SET completed_at = ?, status = ?, detected_message_type = ?,
                message_count = ?, mean_piqi = ?, critical_failure_count = ?,
                elapsed_seconds = ?, error_message = ?
            WHERE run_id = ? AND file_id = ?
            """,
            [
                _utcnow(),
                status,
                detected_message_type,
                message_count,
                mean_piqi,
                critical_failure_count,
                elapsed_seconds,
                error_message,
                run_id,
                file_id,
            ],
        )

    def replace_findings(
        self,
        *,
        run_id: str,
        file_id: str,
        rows: Iterable[Dict[str, Any]],
    ) -> None:
        self.conn.execute(
            "DELETE FROM run_findings WHERE run_id = ? AND file_id = ?",
            [run_id, file_id],
        )
        payload = [
            [
                run_id,
                file_id,
                row.get("profile"),
                row.get("step_id"),
                row.get("sam"),
                row.get("dimension"),
                row.get("status"),
                int(row.get("finding_count", 0)),
            ]
            for row in rows
        ]
        if payload:
            self.conn.executemany(
                """
                INSERT INTO run_findings (
                    run_id, file_id, profile, step_id, sam, dimension, status, finding_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )

    def add_artifact(
        self,
        *,
        run_id: str,
        artifact_type: str,
        artifact_path: str | Path,
        file_id: Optional[str] = None,
    ) -> None:
        path = Path(artifact_path)
        size = path.stat().st_size if path.exists() else None
        self.conn.execute(
            """
            INSERT INTO run_artifacts (
                run_id, file_id, artifact_type, artifact_path, created_at, size_bytes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [run_id, file_id, artifact_type, str(path), _utcnow(), size],
        )

    def recent_runs(self, limit: int = 25) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            """
            SELECT run_id, started_at, completed_at, status, input_type, input_path,
                   profile, file_count, message_count, mean_piqi,
                   critical_failure_count, elapsed_seconds
            FROM runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            [limit],
        )
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in rows]

    def files_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            """
            SELECT file_id, file_name, file_path, file_size_bytes, status,
                   detected_message_type, message_count, mean_piqi,
                   critical_failure_count, elapsed_seconds, error_message
            FROM run_files
            WHERE run_id = ?
            ORDER BY file_name
            """,
            [run_id],
        )
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
