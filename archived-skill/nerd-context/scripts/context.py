#!/usr/bin/env python3
"""Nerd Context deterministic engine and JSON CLI.

Persists one ID-addressed Context in a private user-local SQLite store. The
engine ports the proven POC serializer and Context-local BM25 ranking, adds
the production requirements from `docs/plans/2026-08-27-nerd-context.md`
(schema migration, forget/preview lifecycle, tombstones, symlink refusal,
user-only permissions), and mirrors the same signatures in a JSON CLI so an
MCP adapter can be a thin dispatcher.

This engine performs no live model calls, no network I/O, and never reads or
writes any other Nerd datastore. All authority labels on returned records are
``untrusted_context``; the caller applies ordinary action authority.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat
import sys
from typing import Any


SCHEMA_VERSION = 1
PRODUCTION_MAX_PACK_BYTES = 2_048
DEPLOYABLE_MAX_PACK_BYTES = PRODUCTION_MAX_PACK_BYTES
PACK_START = "<NERD_CONTEXT_PACK_V1>"
PACK_END = "</NERD_CONTEXT_PACK_V1>"
PACK_AUTHORITY = '{"authority":"untrusted_context"}'

RECORD_KINDS = frozenset(
    {"goal", "boundary", "decision", "evidence", "open_question", "checkpoint"}
)
RECORD_SOURCES = frozenset(
    {"direct_user", "assistant_summary", "verified_tool", "repository_fact"}
)
MANDATORY_ORDER = {"boundary": 0, "decision": 1, "goal": 2}
MAX_CAPTURE_RECORDS = 20
MAX_VALUE_BYTES = 4_096
MAX_SOURCE_REF_BYTES = 256
MAX_CAPTURE_ARGUMENT_BYTES = 256 * 1024
MAX_ANCHORS = 8
MAX_ANCHOR_BYTES = 512
MAX_ACTIVATION_REF_BYTES = 256
MAX_CAPTURE_REF_BYTES = 256
MAX_PREVIEW_REF_BYTES = 256
MAX_CONFIRMATION_REF_BYTES = 256
MAX_PREVIEW_AGE_SECONDS = 300

CONTEXT_ID_RE = re.compile(r"ctx_[a-z2-7]{38}[aiqy]\Z")
_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"
TERM_RE = re.compile(r"[a-z0-9]+")
IDENTIFIER_TERM_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)+")
STOP_WORDS = frozenset(
    {
        "a", "an", "and", "at", "case", "current", "for", "from", "in", "is",
        "next", "of", "only", "or", "request", "retrieval", "return", "task",
        "the", "to", "topic",
    }
)
SECRET_MARKERS = (
    "AKIA", "aws_secret_access_key", "-----BEGIN", "PRIVATE KEY",
    "xoxb-", "xoxp-", "ghp_", "gho_", "ghs_", "AIza",
)
EXECUTABLE_MARKERS = ("<script", "javascript:", "data:text/html", "#!")


ERROR_CODES: tuple[tuple[type, str, int], ...]


class ContextEngineError(Exception):
    """Base class for structured Context engine failures."""


class ContextInputError(ContextEngineError, ValueError):
    """The caller supplied invalid arguments."""


class ContextInvariantError(ContextEngineError, RuntimeError):
    """An engine invariant would be violated by continuing."""


class ContextNotFoundError(ContextEngineError, LookupError):
    """The referenced Context does not exist."""


class ContextSchemaError(ContextEngineError, RuntimeError):
    """The persisted schema disagrees with the running engine."""


class ContextStorageError(ContextEngineError, RuntimeError):
    """The underlying SQLite storage failed unexpectedly."""


class ContextClosedError(ContextEngineError, RuntimeError):
    """The store is closed or permanently fenced."""


ERROR_CODES = (
    (ContextInputError, "invalid_arguments", 2),
    (ContextNotFoundError, "not_found", 3),
    (ContextInvariantError, "invariant_violation", 4),
    (ContextSchemaError, "restart_required", 5),
    (ContextStorageError, "storage_error", 6),
    (ContextClosedError, "storage_error", 6),
)


def default_database_path() -> Path:
    """Return the one configured user-local Context database path."""
    explicit = os.environ.get("NERD_CONTEXT_DB")
    if explicit:
        return Path(explicit).expanduser()
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "nerd-context" / "context.sqlite3"
    return Path.home() / ".codex" / "nerd-context" / "context.sqlite3"


# ---------------------------------------------------------------------------
# Serialization primitives (byte-parity with the passing POC).
# ---------------------------------------------------------------------------


def _canonical_record(record: dict) -> dict:
    return {
        "kind": str(record["kind"]),
        "value": str(record["value"]),
        "source": str(record.get("source", "assistant_summary")),
        "source_ref": str(record["source_ref"]),
    }


def _record_line(record: dict) -> str:
    return json.dumps(
        _canonical_record(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def serialize_pack(records: list[dict]) -> str:
    body = "\n".join(_record_line(record) for record in records)
    segment = f"{PACK_START}\n{PACK_AUTHORITY}\n{body}\n{PACK_END}"
    if len(segment.encode("utf-8")) > PRODUCTION_MAX_PACK_BYTES:
        raise ContextInvariantError(
            "context pack exceeds the 2048-byte deployable ceiling"
        )
    return segment


def _terms(value: str) -> frozenset[str]:
    """Baseline unigrams plus whole hyphen/underscore identifiers."""
    folded = value.casefold()
    unigrams = {
        term
        for term in TERM_RE.findall(folded)
        if term not in STOP_WORDS and not (term.isdigit() and len(term) == 1)
    }
    identifiers = set(IDENTIFIER_TERM_RE.findall(folded))
    return frozenset(unigrams | identifiers)


# ---------------------------------------------------------------------------
# Validators.
# ---------------------------------------------------------------------------


def _validate_context_id(context_id: Any) -> str:
    if not isinstance(context_id, str) or not CONTEXT_ID_RE.fullmatch(context_id):
        raise ContextInputError("invalid canonical context ID")
    encoded = context_id[4:]
    try:
        decoded = base64.b32decode(encoded.upper() + "=")
    except Exception as error:
        raise ContextInputError("invalid canonical context ID") from error
    if len(decoded) != 24:
        raise ContextInputError("invalid canonical context ID")
    if base64.b32encode(decoded).decode().rstrip("=").lower() != encoded:
        raise ContextInputError("invalid canonical context ID")
    return context_id


def _new_context_id() -> str:
    encoded = base64.b32encode(secrets.token_bytes(24)).decode("ascii").rstrip("=").lower()
    candidate = "ctx_" + encoded
    if not CONTEXT_ID_RE.fullmatch(candidate):
        raise ContextStorageError("generated non-canonical context ID")
    return candidate


def _require_text(name: str, value: Any, *, max_bytes: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextInputError(f"{name} must be a non-empty string")
    if "\x00" in value:
        raise ContextInputError(f"{name} contains a null byte")
    if len(value.encode("utf-8")) > max_bytes:
        raise ContextInputError(f"{name} exceeds the size limit")
    return value


def _contains_dangerous(value: str) -> bool:
    lowered = value.lower()
    return any(marker.lower() in lowered for marker in SECRET_MARKERS) or any(
        marker in lowered for marker in EXECUTABLE_MARKERS
    )


def _validate_record(record: Any) -> dict:
    if not isinstance(record, dict):
        raise ContextInputError("record must be an object")
    allowed = {"kind", "value", "source", "source_ref", "supersedes_id", "anchors"}
    if set(record) - allowed:
        raise ContextInputError("unsupported capture record fields")
    kind = record.get("kind")
    if not isinstance(kind, str) or kind not in RECORD_KINDS:
        raise ContextInputError("unsupported record kind")
    source = record.get("source")
    if not isinstance(source, str) or source not in RECORD_SOURCES:
        raise ContextInputError("unsupported record source")
    value = _require_text("record value", record.get("value"), max_bytes=MAX_VALUE_BYTES)
    if _contains_dangerous(value):
        raise ContextInputError("record value contains sensitive or executable material")
    source_ref = _require_text(
        "record source_ref", record.get("source_ref"), max_bytes=MAX_SOURCE_REF_BYTES
    )
    supersedes_id = record.get("supersedes_id")
    if supersedes_id is not None and (
        not isinstance(supersedes_id, str) or not supersedes_id.strip()
    ):
        raise ContextInputError("invalid supersedes ID")
    anchors = record.get("anchors")
    if anchors is not None:
        if not isinstance(anchors, list) or len(anchors) > MAX_ANCHORS:
            raise ContextInputError("anchors must be a bounded list")
        for anchor in anchors:
            if not isinstance(anchor, str):
                raise ContextInputError("anchor must be a string")
            _require_text("anchor", anchor, max_bytes=MAX_ANCHOR_BYTES)
            if _contains_dangerous(anchor):
                raise ContextInputError(
                    "anchor contains sensitive or executable material"
                )
    return {
        "kind": kind,
        "value": value,
        "source": source,
        "source_ref": source_ref,
        "supersedes_id": supersedes_id,
        "anchors": list(anchors) if anchors else [],
    }


def _reject_symlink(path: Path) -> None:
    for check in (path, path.parent):
        try:
            if check.exists() and check.is_symlink():
                raise ContextStorageError(f"refusing symlinked path: {check}")
        except OSError as error:
            raise ContextStorageError(str(error)) from error


@dataclass(frozen=True)
class RecallResult:
    """Outcome of a `recall` call."""

    status: str
    created: bool
    context_id: str | None
    records: list[dict]
    segment: str
    conflicts: list[dict]
    overflow: bool
    serialized_bytes: int
    estimated_tokens: int
    authority: str
    record_ids: tuple[str, ...]
    index_mode: str


# ---------------------------------------------------------------------------
# ContextStore.
# ---------------------------------------------------------------------------


class ContextStore:
    """User-local append-only Context store with deterministic bounded recall."""

    def __init__(self, database: Path | None = None, *, index_mode: str | None = None) -> None:
        self._path = Path(database) if database is not None else default_database_path()
        self._closed = False
        self._schema_fenced = False
        parent = self._path.parent
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            parent.chmod(0o700)
        except PermissionError:
            pass
        _reject_symlink(self._path)
        if self._path.exists():
            try:
                self._path.chmod(0o600)
            except PermissionError:
                pass
        self._connection = sqlite3.connect(self._path)
        self._connection.row_factory = sqlite3.Row
        try:
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA synchronous = FULL")
            self._connection.execute("PRAGMA secure_delete = ON")
            self._probe_and_migrate(index_mode)
        except BaseException:
            self._connection.close()
            raise
        if not self._path.exists() or (self._path.stat().st_mode & 0o777) != 0o600:
            try:
                self._path.chmod(0o600)
            except PermissionError:
                pass

    # -------- schema and index-mode --------

    def _probe_and_migrate(self, requested_mode: str | None) -> None:
        cursor = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
        )
        existing = {row[0] for row in cursor}
        if "metadata" in existing:
            row = self._connection.execute(
                "SELECT value FROM metadata WHERE key='schema_version'"
            ).fetchone()
            if row is None or int(row["value"]) != SCHEMA_VERSION:
                self._schema_fenced = True
                raise ContextSchemaError("context schema version mismatch")
            row = self._connection.execute(
                "SELECT value FROM metadata WHERE key='index_mode'"
            ).fetchone()
            existing_mode = row["value"] if row else "normalized_scan"
            if requested_mode is not None and requested_mode != existing_mode:
                raise ContextSchemaError(
                    "requested index_mode differs from persisted schema"
                )
            self.index_mode = existing_mode
            return
        mode = requested_mode or self._probe_fts5()
        if mode not in {"fts5", "normalized_scan"}:
            raise ContextInputError("unsupported index mode")
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE contexts (
                    context_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE records (
                    sequence INTEGER PRIMARY KEY,
                    id TEXT NOT NULL UNIQUE,
                    context_id TEXT NOT NULL REFERENCES contexts(context_id),
                    kind TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    active INTEGER NOT NULL CHECK (active IN (0,1)),
                    supersedes_id TEXT REFERENCES records(id),
                    anchors TEXT NOT NULL,
                    terms TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    capture_ref TEXT
                );
                CREATE INDEX records_context_active
                    ON records(context_id, active, sequence);
                CREATE TABLE record_events (
                    event_id INTEGER PRIMARY KEY,
                    record_id TEXT NOT NULL REFERENCES records(id),
                    change TEXT NOT NULL,
                    at TEXT NOT NULL
                );
                CREATE TABLE captures (
                    capture_ref TEXT PRIMARY KEY,
                    context_id TEXT NOT NULL REFERENCES contexts(context_id),
                    digest TEXT NOT NULL,
                    accepted_ids TEXT NOT NULL,
                    superseded_ids TEXT NOT NULL,
                    at TEXT NOT NULL
                );
                CREATE TABLE previews (
                    preview_ref TEXT PRIMARY KEY,
                    context_id TEXT NOT NULL,
                    digest TEXT NOT NULL,
                    counts TEXT NOT NULL,
                    confirmation_phrase TEXT NOT NULL,
                    at TEXT NOT NULL
                );
                CREATE TABLE confirmation_ref_tombstones (
                    confirmation_ref TEXT PRIMARY KEY,
                    at TEXT NOT NULL
                );
                CREATE TABLE forgotten_contexts (
                    context_id TEXT PRIMARY KEY,
                    digest TEXT NOT NULL,
                    at TEXT NOT NULL
                );
                """
            )
            self._connection.execute(
                "INSERT INTO metadata(key,value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            self._connection.execute(
                "INSERT INTO metadata(key,value) VALUES ('index_mode', ?)",
                (mode,),
            )
            if mode == "fts5":
                self._connection.executescript(
                    """
                    CREATE VIRTUAL TABLE poc_record_terms USING fts5(
                        terms, content='records', content_rowid='sequence',
                        tokenize="ascii tokenchars '-_'"
                    );
                    CREATE TRIGGER poc_records_insert AFTER INSERT ON records BEGIN
                        INSERT INTO poc_record_terms(rowid, terms)
                        VALUES (new.sequence, new.terms);
                    END;
                    """
                )
        self.index_mode = mode

    def _probe_fts5(self) -> str:
        try:
            probe = sqlite3.connect(":memory:")
            try:
                probe.execute(
                    "CREATE VIRTUAL TABLE t USING fts5(x, tokenize=\"ascii tokenchars '-_'\")"
                )
            finally:
                probe.close()
            return "fts5"
        except sqlite3.OperationalError:
            return "normalized_scan"

    # -------- lifecycle --------

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._connection.close()
        except Exception:
            pass

    def __enter__(self) -> ContextStore:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _ensure_live(self) -> None:
        if self._closed:
            raise ContextClosedError("context store is closed")
        if self._schema_fenced:
            raise ContextSchemaError("context store is permanently fenced")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
            "+00:00", "Z"
        )

    # -------- public API --------

    @property
    def path(self) -> Path:
        return self._path

    def counts(self) -> dict:
        self._ensure_live()
        return {
            "context_count": self._connection.execute(
                "SELECT COUNT(*) FROM contexts"
            ).fetchone()[0],
            "record_count": self._connection.execute(
                "SELECT COUNT(*) FROM records"
            ).fetchone()[0],
            "capture_count": self._connection.execute(
                "SELECT COUNT(*) FROM captures"
            ).fetchone()[0],
        }

    def recall(
        self,
        *,
        context_id: str | None = None,
        query: str = "",
        activation_ref: str,
        max_bytes: int | None = None,
    ) -> dict:
        self._ensure_live()
        _require_text("activation_ref", activation_ref, max_bytes=MAX_ACTIVATION_REF_BYTES)
        if not isinstance(query, str):
            raise ContextInputError("query must be a string")
        limit = max_bytes if max_bytes is not None else PRODUCTION_MAX_PACK_BYTES
        if type(limit) is not int or limit <= 0 or limit > PRODUCTION_MAX_PACK_BYTES:
            raise ContextInputError("invalid max_bytes")
        empty = serialize_pack([])
        if limit < len(empty.encode("utf-8")):
            raise ContextInputError("max_bytes below the empty-pack ceiling")
        created = context_id is None
        if created:
            allocated = self._create_context()
            context_id = allocated
        else:
            _validate_context_id(context_id)
            row = self._connection.execute(
                "SELECT 1 FROM contexts WHERE context_id = ?", (context_id,)
            ).fetchone()
            if row is None:
                return {
                    "status": "not_found",
                    "created": False,
                    "context_id": context_id,
                    "records": [],
                    "segment": empty,
                    "conflicts": [],
                    "overflow": False,
                    "serialized_bytes": len(empty.encode("utf-8")),
                    "estimated_tokens": len(empty.encode("utf-8")),
                    "authority": "untrusted_context",
                    "record_ids": [],
                    "index_mode": self.index_mode,
                }
        active = [
            dict(row)
            for row in self._connection.execute(
                "SELECT * FROM records WHERE context_id = ? AND active = 1"
                " ORDER BY sequence",
                (context_id,),
            )
        ]
        selected, overflow = self._select_records(active, query, limit)
        segment = serialize_pack(selected)
        conflicts = self._conflict_summary(context_id, active)
        return {
            "status": "ok",
            "created": created,
            "context_id": context_id,
            "records": [_canonical_record(record) for record in selected],
            "segment": segment,
            "conflicts": conflicts,
            "overflow": overflow,
            "serialized_bytes": len(segment.encode("utf-8")),
            "estimated_tokens": len(segment.encode("utf-8")),
            "authority": "untrusted_context",
            "record_ids": [record["id"] for record in selected],
            "index_mode": self.index_mode,
        }

    def capture(
        self,
        context_id: str,
        *,
        records: list[dict],
        capture_ref: str,
    ) -> dict:
        self._ensure_live()
        _validate_context_id(context_id)
        _require_text("capture_ref", capture_ref, max_bytes=MAX_CAPTURE_REF_BYTES)
        if not isinstance(records, list):
            raise ContextInputError("records must be a list")
        if not records:
            raise ContextInputError("records must not be empty")
        if len(records) > MAX_CAPTURE_RECORDS:
            raise ContextInputError(
                f"capture accepts at most {MAX_CAPTURE_RECORDS} records"
            )
        normalized = [_validate_record(record) for record in records]
        canonical = [
            {
                "kind": record["kind"],
                "value": record["value"],
                "source": record["source"],
                "source_ref": record["source_ref"],
                "supersedes_id": record["supersedes_id"],
                "anchors": record["anchors"],
            }
            for record in normalized
        ]
        payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(payload.encode("utf-8")) > MAX_CAPTURE_ARGUMENT_BYTES:
            raise ContextInputError("capture exceeds the capture-argument byte budget")
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            row = self._connection.execute(
                "SELECT 1 FROM contexts WHERE context_id = ?", (context_id,)
            ).fetchone()
            if row is None:
                return {
                    "status": "not_found",
                    "context_id": context_id,
                    "accepted_ids": [],
                    "superseded_ids": [],
                    "duplicate": False,
                }
            existing = self._connection.execute(
                "SELECT * FROM captures WHERE capture_ref = ?", (capture_ref,)
            ).fetchone()
            if existing:
                if existing["context_id"] != context_id or existing["digest"] != digest:
                    raise ContextInvariantError(
                        "capture_ref reused with different contents"
                    )
                return {
                    "status": "ok",
                    "context_id": context_id,
                    "accepted_ids": json.loads(existing["accepted_ids"]),
                    "superseded_ids": json.loads(existing["superseded_ids"]),
                    "duplicate": True,
                }
            accepted: list[str] = []
            superseded: list[str] = []
            for record in normalized:
                predecessor = record["supersedes_id"]
                if predecessor is not None:
                    changed = self._connection.execute(
                        "UPDATE records SET active = 0"
                        " WHERE id = ? AND context_id = ? AND active = 1 AND kind = ?",
                        (predecessor, context_id, record["kind"]),
                    ).rowcount
                    if changed != 1:
                        raise ContextInvariantError(
                            "supersession requires an active same-context, same-kind predecessor"
                        )
                    superseded.append(predecessor)
                    self._connection.execute(
                        "INSERT INTO record_events(record_id, change, at) VALUES (?, 'superseded', ?)",
                        (predecessor, self._now()),
                    )
                record_id = "rec_" + secrets.token_hex(16)
                self._insert_record(record_id, context_id, record, capture_ref=capture_ref)
                accepted.append(record_id)
            self._connection.execute(
                "INSERT INTO captures(capture_ref, context_id, digest, accepted_ids, superseded_ids, at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    capture_ref,
                    context_id,
                    digest,
                    json.dumps(accepted),
                    json.dumps(superseded),
                    self._now(),
                ),
            )
        return {
            "status": "ok",
            "context_id": context_id,
            "accepted_ids": accepted,
            "superseded_ids": superseded,
            "duplicate": False,
        }

    def inspect(
        self,
        context_id: str,
        *,
        activation_ref: str,
        cursor: str | None = None,
        limit: int = 50,
    ) -> dict:
        self._ensure_live()
        _validate_context_id(context_id)
        _require_text("activation_ref", activation_ref, max_bytes=MAX_ACTIVATION_REF_BYTES)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ContextInputError("invalid inspection limit")
        row = self._connection.execute(
            "SELECT * FROM contexts WHERE context_id = ?", (context_id,)
        ).fetchone()
        if row is None:
            return {"status": "not_found", "context_id": context_id}
        start = 0
        if cursor is not None:
            if not isinstance(cursor, str) or not cursor.isdigit():
                raise ContextInputError("invalid inspection cursor")
            start = int(cursor)
        counts = self._connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(active), 0) FROM records WHERE context_id = ?",
            (context_id,),
        ).fetchone()
        capture_count = self._connection.execute(
            "SELECT COUNT(*) FROM captures WHERE context_id = ?", (context_id,)
        ).fetchone()[0]
        metadata = self._connection.execute(
            "SELECT id, kind, source, source_ref, active, supersedes_id, created_at"
            " FROM records WHERE context_id = ?"
            " ORDER BY sequence LIMIT ? OFFSET ?",
            (context_id, limit, start),
        ).fetchall()
        rows = [dict(row) for row in metadata]
        next_cursor = str(start + limit) if len(rows) == limit else None
        return {
            "status": "ok",
            "context": {
                "context_id": context_id,
                "created_at": row["created_at"],
                "record_count": counts[0],
                "active_record_count": counts[1],
                "capture_count": capture_count,
                "index_mode": self.index_mode,
            },
            "record_metadata": rows,
            "next_cursor": next_cursor,
        }

    def preview_forget(self, context_id: str, *, preview_ref: str) -> dict:
        self._ensure_live()
        _validate_context_id(context_id)
        _require_text("preview_ref", preview_ref, max_bytes=MAX_PREVIEW_REF_BYTES)
        row = self._connection.execute(
            "SELECT 1 FROM contexts WHERE context_id = ?", (context_id,)
        ).fetchone()
        if row is None:
            return {"status": "not_found", "context_id": context_id}
        counts = self._connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(active),0) FROM records WHERE context_id = ?",
            (context_id,),
        ).fetchone()
        counts_dict = {"records": counts[0], "active_records": counts[1]}
        state = json.dumps(
            {"context_id": context_id, "counts": counts_dict},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(state.encode("utf-8")).hexdigest()
        phrase = f"forget context {context_id} with digest {digest[:16]}"
        with self._connection:
            existing = self._connection.execute(
                "SELECT * FROM previews WHERE preview_ref = ?", (preview_ref,)
            ).fetchone()
            if existing:
                if (
                    existing["context_id"] != context_id
                    or existing["digest"] != digest
                    or existing["confirmation_phrase"] != phrase
                ):
                    raise ContextInvariantError(
                        "preview_ref reused with different state"
                    )
            else:
                self._connection.execute(
                    "INSERT INTO previews(preview_ref, context_id, digest, counts,"
                    " confirmation_phrase, at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        preview_ref,
                        context_id,
                        digest,
                        json.dumps(counts_dict),
                        phrase,
                        self._now(),
                    ),
                )
        return {
            "status": "ok",
            "context_id": context_id,
            "counts": counts_dict,
            "digest": digest,
            "preview_ref_digest": hashlib.sha256(preview_ref.encode("utf-8")).hexdigest(),
            "confirmation_phrase": phrase,
        }

    def forget(
        self,
        context_id: str,
        *,
        phrase: str,
        source: str,
        confirmation_ref: str,
    ) -> dict:
        self._ensure_live()
        _validate_context_id(context_id)
        if source != "direct_user":
            raise ContextInputError("forget requires source='direct_user'")
        _require_text("phrase", phrase, max_bytes=1024)
        _require_text(
            "confirmation_ref",
            confirmation_ref,
            max_bytes=MAX_CONFIRMATION_REF_BYTES,
        )
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            already = self._connection.execute(
                "SELECT 1 FROM confirmation_ref_tombstones WHERE confirmation_ref = ?",
                (confirmation_ref,),
            ).fetchone()
            if already:
                raise ContextInvariantError("confirmation_ref already used")
            preview = self._connection.execute(
                "SELECT * FROM previews WHERE context_id = ? AND confirmation_phrase = ?"
                " ORDER BY at DESC LIMIT 1",
                (context_id, phrase),
            ).fetchone()
            if preview is None:
                raise ContextInvariantError(
                    "no current preview matches this confirmation phrase"
                )
            if preview["preview_ref"] == confirmation_ref:
                raise ContextInvariantError(
                    "confirmation_ref must differ from preview_ref"
                )
            counts = self._connection.execute(
                "SELECT COUNT(*), COALESCE(SUM(active),0) FROM records WHERE context_id = ?",
                (context_id,),
            ).fetchone()
            state = json.dumps(
                {
                    "context_id": context_id,
                    "counts": {"records": counts[0], "active_records": counts[1]},
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            digest = hashlib.sha256(state.encode("utf-8")).hexdigest()
            if digest != preview["digest"]:
                raise ContextInvariantError(
                    "context state changed since the preview was captured"
                )
            self._connection.execute(
                "INSERT INTO confirmation_ref_tombstones(confirmation_ref, at) VALUES (?, ?)",
                (confirmation_ref, self._now()),
            )
            deleted = self._connection.execute(
                "SELECT COUNT(*) FROM records WHERE context_id = ?", (context_id,)
            ).fetchone()[0]
            self._connection.execute(
                "DELETE FROM record_events WHERE record_id IN"
                " (SELECT id FROM records WHERE context_id = ?)",
                (context_id,),
            )
            self._connection.execute(
                "DELETE FROM records WHERE context_id = ?", (context_id,)
            )
            self._connection.execute(
                "DELETE FROM captures WHERE context_id = ?", (context_id,)
            )
            self._connection.execute(
                "DELETE FROM previews WHERE context_id = ?", (context_id,)
            )
            self._connection.execute(
                "DELETE FROM contexts WHERE context_id = ?", (context_id,)
            )
            tombstoned_at = self._now()
            self._connection.execute(
                "INSERT OR REPLACE INTO forgotten_contexts(context_id, digest, at)"
                " VALUES (?, ?, ?)",
                (context_id, digest, tombstoned_at),
            )
        return {
            "status": "ok",
            "context_id": context_id,
            "deleted": deleted,
            "tombstoned_at": tombstoned_at,
        }

    # -------- internals --------

    def _create_context(self) -> str:
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            for _ in range(8):
                candidate = _new_context_id()
                if self._connection.execute(
                    "SELECT 1 FROM forgotten_contexts WHERE context_id = ?",
                    (candidate,),
                ).fetchone():
                    continue
                try:
                    self._connection.execute(
                        "INSERT INTO contexts(context_id, created_at) VALUES (?, ?)",
                        (candidate, self._now()),
                    )
                except sqlite3.IntegrityError:
                    continue
                return candidate
        raise ContextStorageError("context ID allocation failed")

    def _insert_record(
        self,
        record_id: str,
        context_id: str,
        record: dict,
        *,
        active: bool = True,
        capture_ref: str | None = None,
    ) -> None:
        anchors = json.dumps(record.get("anchors", []), ensure_ascii=False)
        self._connection.execute(
            "INSERT INTO records(id, context_id, kind, value, source, source_ref,"
            " active, supersedes_id, anchors, terms, created_at, capture_ref)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record_id,
                context_id,
                record["kind"],
                record["value"],
                record["source"],
                record["source_ref"],
                int(active),
                record.get("supersedes_id"),
                anchors,
                " ".join(sorted(_terms(record["value"]))),
                self._now(),
                capture_ref,
            ),
        )
        self._connection.execute(
            "INSERT INTO record_events(record_id, change, at) VALUES (?, 'inserted', ?)",
            (record_id, self._now()),
        )

    def _select_records(
        self, active: list[dict], query: str, max_bytes: int
    ) -> tuple[list[dict], bool]:
        positions = {record["id"]: record["sequence"] for record in active}
        mandatory = sorted(
            (record for record in active if record["kind"] in MANDATORY_ORDER),
            key=lambda record: (
                MANDATORY_ORDER[record["kind"]],
                positions[record["id"]],
            ),
        )
        optional = [record for record in active if record["kind"] not in MANDATORY_ORDER]
        query_terms = _terms(query)
        record_terms = {record["id"]: frozenset(record["terms"].split()) for record in active}
        average_length = (
            sum(len(record_terms[record["id"]]) for record in active) / max(1, len(active))
            or 1.0
        )
        document_frequency = {
            term: sum(term in record_terms[record["id"]] for record in active)
            for term in query_terms
        }
        inverse_frequency = {
            term: math.log1p((len(active) - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }
        if query_terms and self.index_mode == "fts5":
            expression = " OR ".join(f'"{term}"' for term in sorted(query_terms))
            matched = {
                row[0]
                for row in self._connection.execute(
                    "SELECT r.id FROM poc_record_terms CROSS JOIN records AS r"
                    " ON r.sequence = poc_record_terms.rowid"
                    " WHERE poc_record_terms MATCH ? AND r.active = 1",
                    (expression,),
                )
            }
        else:
            matched = {record["id"] for record in optional}

        def relevance(record: dict) -> float:
            if record["id"] not in matched:
                return 0.0
            terms = record_terms[record["id"]]
            normalization = 2.2 / (
                1.0 + 1.2 * (0.25 + 0.75 * len(terms) / average_length)
            )
            return (
                sum(inverse_frequency[term] for term in sorted(query_terms & terms))
                * normalization
            )

        selected: list[dict] = []
        empty = serialize_pack([])
        selected_bytes = len(empty.encode("utf-8"))
        record_bytes = {
            record["id"]: len(_record_line(record).encode("utf-8")) for record in active
        }

        def fits(record: dict) -> bool:
            separator = 1 if selected else 0
            return selected_bytes + separator + record_bytes[record["id"]] <= max_bytes

        for record in mandatory:
            if not fits(record):
                return [], True
            selected_bytes += (1 if selected else 0) + record_bytes[record["id"]]
            selected.append(record)
        if query_terms:
            relevance_scores = {record["id"]: relevance(record) for record in optional}
            redundancy = {record["id"]: 0.0 for record in optional}
            while optional:
                optional = [record for record in optional if fits(record)]
                if not optional:
                    break
                pick = min(
                    optional,
                    key=lambda item: (
                        -relevance_scores[item["id"]] * (1.0 - redundancy[item["id"]]),
                        -positions[item["id"]],
                        item["id"],
                    ),
                )
                selected_bytes += (1 if selected else 0) + record_bytes[pick["id"]]
                selected.append(pick)
                optional.remove(pick)
                chosen_terms = record_terms[pick["id"]]
                for item in optional:
                    if relevance_scores[item["id"]] == 0.0:
                        continue
                    terms = record_terms[item["id"]]
                    similarity = len(terms & chosen_terms) / max(
                        1, len(terms | chosen_terms)
                    )
                    redundancy[item["id"]] = max(redundancy[item["id"]], similarity)
        else:
            for record in sorted(
                optional,
                key=lambda item: (-positions[item["id"]], item["id"]),
            ):
                if fits(record):
                    selected_bytes += (1 if selected else 0) + record_bytes[record["id"]]
                    selected.append(record)
        return selected, False

    def _conflict_summary(self, context_id: str, active: list[dict]) -> list[dict]:
        superseded = self._connection.execute(
            "SELECT id, kind FROM records WHERE context_id = ? AND active = 0",
            (context_id,),
        ).fetchall()
        return [
            {"id": row["id"], "kind": row["kind"], "status": "superseded"}
            for row in superseded
        ]


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def _cli_error(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}


def _cli_result(payload: Any) -> dict:
    return {"ok": True, "result": payload}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(
            json.dumps(_cli_error("invalid_arguments", "missing command"), separators=(",", ":")),
            flush=True,
        )
        return 2
    command = args[0]
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise ContextInputError("payload must be a JSON object")
    except (json.JSONDecodeError, ValueError) as error:
        print(
            json.dumps(_cli_error("invalid_arguments", str(error)), separators=(",", ":")),
            flush=True,
        )
        return 2
    store = ContextStore()
    try:
        try:
            if command == "recall":
                result = store.recall(**payload)
            elif command == "capture":
                context_id = payload.pop("context_id")
                result = store.capture(context_id, **payload)
            elif command == "inspect":
                context_id = payload.pop("context_id")
                result = store.inspect(context_id, **payload)
            elif command == "preview_forget":
                context_id = payload.pop("context_id")
                result = store.preview_forget(context_id, **payload)
            elif command == "forget":
                context_id = payload.pop("context_id")
                result = store.forget(context_id, **payload)
            elif command == "counts":
                result = store.counts()
            else:
                raise ContextInputError(f"unknown command: {command}")
            print(
                json.dumps(_cli_result(result), ensure_ascii=False, separators=(",", ":")),
                flush=True,
            )
            return 0
        except ContextEngineError as error:
            for error_type, code, exit_code in ERROR_CODES:
                if isinstance(error, error_type):
                    break
            else:
                code, exit_code = "internal_error", 1
            print(
                json.dumps(_cli_error(code, str(error)), separators=(",", ":")),
                flush=True,
            )
            return exit_code
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
