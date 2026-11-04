"""Local repository boundary. Cloud implementations must add per-user isolation."""

from typing import Protocol
from pathlib import Path
import sqlite3
import json
import uuid
from datetime import datetime, timezone

# Aliases defined outside the classes: inside them, the method named `list` hides the
# built-in `list`, so a hint such as `list[dict]` would refer to the method instead.
Records = list[dict]
Ids = list[str]


def now() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


class InspectionRepository(Protocol):
    """The smallest set of operations every inspection store provides."""

    def save(self, record: dict) -> dict: ...
    def get(self, identifier: str) -> dict | None: ...
    def list(
        self, category: str = "", verdict: str = "", batch: str = "", limit: int = 100, offset: int = 0
    ) -> Records: ...


class SQLiteRepository:
    """Local single-user inspection store kept in one SQLite file (WAL mode).

    Holds inspections, assistant messages, alerts, failed requests, archive marks and an
    audit log. An inspection is stored as a JSON payload; category, verdict, batch and time
    are separate columns so the history can be filtered. Each call opens its own connection.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS inspections(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,category TEXT NOT NULL,verdict TEXT NOT NULL,batch TEXT NOT NULL,payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS inspection_filter ON inspections(category,verdict,batch,created_at);
            CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,inspection_id TEXT NOT NULL,created_at TEXT NOT NULL,role TEXT NOT NULL,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY,inspection_id TEXT NOT NULL,created_at TEXT NOT NULL,kind TEXT NOT NULL,acknowledged INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS failures(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,category TEXT,error TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS inspection_archives(id TEXT PRIMARY KEY,archived_at TEXT NOT NULL,archive_batch TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_events(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,action TEXT NOT NULL,payload TEXT NOT NULL);
            """)

    def connect(self) -> sqlite3.Connection:
        """Open a new connection that returns rows by column name and waits up to 20 s for a lock."""
        connection = sqlite3.connect(self.path, timeout=20)
        connection.row_factory = sqlite3.Row
        return connection

    def save(self, record: dict) -> dict:
        """Store an inspection. A verdict other than "Good" also creates an alert. Returns the record."""
        with self.connect() as db:
            db.execute(
                "INSERT INTO inspections VALUES(?,?,?,?,?,?)",
                (
                    record["id"],
                    record["created_at"],
                    record["category"],
                    record["verdict"],
                    record.get("batch", ""),
                    json.dumps(record),
                ),
            )
            if record["verdict"] != "Good":
                db.execute(
                    "INSERT INTO alerts(id,inspection_id,created_at,kind) VALUES(?,?,?,?)",
                    (uuid.uuid4().hex, record["id"], record["created_at"], record["verdict"]),
                )
        return record

    def get(self, identifier: str) -> dict | None:
        """Return one inspection by ID, or None if it does not exist or has been archived."""
        with self.connect() as db:
            row = db.execute(
                "SELECT payload FROM inspections WHERE id=? AND id NOT IN (SELECT id FROM inspection_archives)",
                (identifier,),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def list(
        self,
        category: str = "",
        verdict: str = "",
        batch: str = "",
        limit: int = 100,
        offset: int = 0,
        archived: bool = False,
    ) -> Records:
        """Return inspections newest first, optionally filtered by category, verdict and batch.

        An empty filter value means "any". With archived=True the archived inspections are
        returned instead of the active ones. Column names are fixed in the code and all values
        are passed as bound parameters, so user input never becomes part of the SQL text.
        """
        clauses, params = ["id " + ("IN" if archived else "NOT IN") + " (SELECT id FROM inspection_archives)"], []
        for key, value in [("category", category), ("verdict", verdict), ("batch", batch)]:
            if value:
                clauses.append(key + "=?")
                params.append(value)
        query = (
            "SELECT payload FROM inspections"
            + (" WHERE " + " AND ".join(clauses) if clauses else "")
            + " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        )
        with self.connect() as db:
            rows = db.execute(query, [*params, limit, offset]).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def stats(self) -> dict:
        """Count active inspections per verdict and per batch, plus failed requests and archived total."""
        with self.connect() as db:
            counts = {
                r["verdict"]: r["n"]
                for r in db.execute(
                    "SELECT verdict,count(*) n FROM inspections WHERE id NOT IN (SELECT id FROM inspection_archives) GROUP BY verdict"
                )
            }
            batches = [
                dict(r)
                for r in db.execute(
                    'SELECT batch,count(*) total,sum(verdict="Anomalous") anomalous,sum(verdict="Uncertain") uncertain FROM inspections WHERE id NOT IN (SELECT id FROM inspection_archives) GROUP BY batch ORDER BY max(created_at) DESC'
                )
            ]
            failures = db.execute("SELECT count(*) FROM failures").fetchone()[0]
            archived = db.execute("SELECT count(*) FROM inspection_archives").fetchone()[0]
        return {
            "counts": counts,
            "total": sum(counts.values()),
            "batches": batches,
            "failed_requests": failures,
            "archived_total": archived,
        }

    def alerts(self) -> Records:
        """Return up to 200 newest alerts for inspections that are not archived."""
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM alerts WHERE inspection_id NOT IN (SELECT id FROM inspection_archives) ORDER BY created_at DESC LIMIT 200"
                )
            ]

    def archive(self, category: str = "", verdict: str = "", batch: str = "") -> dict:
        """Archive every active inspection that matches the filters. Nothing is deleted.

        Writes an audit event and returns how many were archived and the new archive batch ID.
        """
        clauses = ["id NOT IN (SELECT id FROM inspection_archives)"]
        params = []
        for key, value in [("category", category), ("verdict", verdict), ("batch", batch)]:
            if value:
                clauses.append(key + "=?")
                params.append(value)
        identifier = uuid.uuid4().hex
        timestamp = now()
        with self.connect() as db:
            changed = db.execute(
                "INSERT INTO inspection_archives SELECT id,?,? FROM inspections WHERE " + " AND ".join(clauses),
                [timestamp, identifier, *params],
            ).rowcount
            db.execute(
                "INSERT INTO audit_events VALUES(?,?,?,?)",
                (
                    uuid.uuid4().hex,
                    timestamp,
                    "archive",
                    json.dumps(
                        {
                            "archive_batch": identifier,
                            "count": changed,
                            "filters": dict(category=category, verdict=verdict, batch=batch),
                        }
                    ),
                ),
            )
        return {"archived": changed, "archive_batch": identifier}

    def restore(self, identifiers: Ids) -> dict:
        """Bring archived inspections back to the active history and record an audit event."""
        placeholders = ",".join("?" for _ in identifiers)
        with self.connect() as db:
            changed = db.execute(
                "DELETE FROM inspection_archives WHERE id IN (" + placeholders + ")", identifiers
            ).rowcount
            db.execute(
                "INSERT INTO audit_events VALUES(?,?,?,?)",
                (uuid.uuid4().hex, now(), "restore", json.dumps({"ids": identifiers, "count": changed})),
            )
        return {"restored": changed}

    def acknowledge(self, identifier: str) -> bool:
        """Mark an alert as acknowledged. Returns False if no alert has that ID."""
        with self.connect() as db:
            return db.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (identifier,)).rowcount > 0

    def add_message(self, identifier: str, role: str, payload: dict) -> None:
        """Append one assistant-conversation message to an inspection."""
        with self.connect() as db:
            db.execute(
                "INSERT INTO messages(inspection_id,created_at,role,payload) VALUES(?,?,?,?)",
                (identifier, now(), role, json.dumps(payload)),
            )

    def add_conversation(self, identifier: str, question: str, answer: dict) -> None:
        """Save a question and its answer together, so a half-finished exchange is never stored."""
        with self.connect() as db:
            db.executemany(
                "INSERT INTO messages(inspection_id,created_at,role,payload) VALUES(?,?,?,?)",
                [
                    (identifier, now(), "user", json.dumps({"question": question})),
                    (identifier, now(), "assistant", json.dumps(answer)),
                ],
            )

    def messages(self, identifier: str) -> Records:
        """Return the last 20 conversation messages of an inspection, oldest first."""
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM (SELECT * FROM messages WHERE inspection_id=? ORDER BY id DESC LIMIT 20) ORDER BY id",
                (identifier,),
            ).fetchall()
        return [{"role": r["role"], "created_at": r["created_at"], **json.loads(r["payload"])} for r in rows]

    def failure(self, category: str | None, error: str) -> None:
        """Record a request that failed before an inspection could be saved (for the failure count)."""
        with self.connect() as db:
            db.execute("INSERT INTO failures VALUES(?,?,?,?)", (uuid.uuid4().hex, now(), category, error))

    def add_review(self, identifier: str, status: str, decision: str, note: str = "") -> dict:
        """Validate a human review and append it to the audit log. Returns the stored review."""
        from .reviews import validate_review

        review = {
            **validate_review(status, decision, note),
            "inspection_id": identifier,
            "reviewer": "Local operator (single-user workspace)",
            "created_at": now(),
        }
        with self.connect() as db:
            db.execute(
                "INSERT INTO audit_events VALUES(?,?,?,?)",
                (uuid.uuid4().hex, review["created_at"], "human_review", json.dumps(review)),
            )
        return review

    def review_history(self, identifier: str) -> Records:
        """Return the human reviews of an inspection, oldest first."""
        with self.connect() as db:
            rows = db.execute(
                "SELECT payload FROM audit_events WHERE action='human_review' AND json_extract(payload,'$.inspection_id')=? ORDER BY created_at",
                (identifier,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def review_notes(self, identifier: str) -> Records:
        """The local store keeps no review notes, so this always returns an empty list."""
        return []
