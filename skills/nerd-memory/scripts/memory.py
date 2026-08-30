#!/usr/bin/env python3
"""Global, user-local behavioral memory backed by SQLite.

The store persists only sanitized, verified behavior episodes. Recall results
are untrusted advice: current action, tool, step, and skill choices always win.
"""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence
import argparse
import copy
import hashlib
import inspect as python_inspect
import json
import math
import os
import re
import sqlite3
import sys
import threading
import time
import unicodedata
import uuid


SCHEMA_FAMILY = "global-behavior-memory"
SCHEMA_VERSION = 1
SCHEMA_TABLES = frozenset(
    {
        "metadata",
        "behavior_episodes",
        "recall_events",
        "forget_previews",
        "trusted_event_tombstones",
    }
)
CONTEXT_FIELDS = ("language", "surface", "project_kind")
CURRENT_FIELDS = ("action", "tools", "steps", "skills")
SOURCE_KINDS = frozenset({"verified_execution", "user_correction"})
FEEDBACK_VALUES = frozenset({"accepted", "corrected", "rejected"})
SEVERITY_VALUES = frozenset({"none", "low", "medium", "high", "critical"})
ABSTAIN_THRESHOLD = 0.60
INVALID_SHARE_THRESHOLD = 0.50
CORRECTION_RETIREMENT_COUNT = 3
DEFAULT_BUSY_TIMEOUT_MS = 5_000
DEFAULT_FORGET_TTL_SECONDS = 300
MAX_JSON_BYTES = 1_000_000
MAX_INSPECT_ITEMS = 100
MAX_RECALL_EVENTS = 1_000
VERIFICATION_TRUST_BOUNDARY = (
    "verified, source_kind, verifier, and evidence_ref are classifications from "
    "the authenticated host; source_agent is provenance only and never proof"
)

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*", re.IGNORECASE)
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@+\-]{0,255}$")
SECRET_PATTERNS = (
    re.compile(r"(?i)(?<![a-z0-9])sk-[a-z0-9_-]{16,}"),
    re.compile(r"(?i)\b(?:ghp|gho|ghu|ghs|ghr)_[a-z0-9]{20,}\b"),
    re.compile(r"(?i)\bgithub_pat_[a-z0-9_]{20,}\b"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@\S+"),
    re.compile(r"(?i)\b(?:xox[baprs]-|glpat-|hf_|npm_)[a-z0-9_-]{16,}\b"),
    re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]{16,}"),
    re.compile(
        r"(?i)(?:password|passwd|token|secret|api[_-]?key|access[_-]?key|"
        r"client[_-]?secret|aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*\S+"
    ),
    re.compile(r"-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----"),
)
EXECUTABLE_MARKERS = (
    "`",
    "$(",
    ";",
    "&&",
    "||",
    "\n",
    "\r",
    "\x00",
)
STOP_CUES = frozenset(
    {
        "a",
        "an",
        "and",
        "authorization",
        "bearer",
        "for",
        "please",
        "redacted",
        "run",
        "the",
        "token",
        "password",
        "with",
    }
)
CUE_ALIASES = {
    "tests": "test",
    "testing": "test",
    "debug": "diagnose",
    "investigate": "diagnose",
    "fix": "implement",
    "build": "implement",
    "docs": "document",
    "documentation": "document",
    "database": "schema",
    "migration": "schema",
    "ui": "browser",
}


class MemoryEngineError(Exception):
    """Base class for expected behavioral-memory failures."""


class MemoryInputError(MemoryEngineError, ValueError):
    """The caller supplied invalid or unsafe input."""


class MemoryInvariantError(MemoryEngineError, RuntimeError):
    """A replay, idempotency, or deletion invariant would be violated."""


class MemoryNotFoundError(MemoryEngineError, LookupError):
    """A requested episode or deletion preview does not exist."""


class MemorySchemaError(MemoryEngineError, RuntimeError):
    """The database is not the active schema family/version."""


class MemoryClosedError(MemoryEngineError, RuntimeError):
    """The store is closed or permanently fenced."""


def default_database_path() -> Path:
    """Return the one configured user-local behavioral database path."""

    explicit = os.environ.get("NERD_MEMORY_DB")
    if explicit:
        return Path(explicit).expanduser()
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "nerd-memory" / "behavior.sqlite3"
    return Path.home() / ".codex" / "nerd-memory" / "behavior.sqlite3"


def _normalise_json(value: Any, *, depth: int = 0) -> Any:
    if depth > 100:
        raise MemoryInputError("JSON input is nested too deeply")
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise MemoryInputError("non-finite numbers are not valid memory data")
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, (list, tuple)):
        return [_normalise_json(item, depth=depth + 1) for item in value]
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise MemoryInputError("JSON object keys must be strings")
            normalised_key = unicodedata.normalize("NFC", key)
            if normalised_key in result:
                raise MemoryInputError("JSON object contains duplicate canonical keys")
            result[normalised_key] = _normalise_json(item, depth=depth + 1)
        return result
    raise MemoryInputError(f"unsupported memory value type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Return deterministic, Unicode-normalized JSON."""

    encoded = json.dumps(
        _normalise_json(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise MemoryInputError("memory JSON exceeds the size limit")
    return encoded


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _utc_now(epoch_seconds: float) -> str:
    return (
        datetime.fromtimestamp(epoch_seconds, timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _parse_utc(name: str, value: Any) -> str:
    text = _require_text(name, value, max_length=64)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise MemoryInputError(f"{name} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise MemoryInputError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _require_text(name: str, value: Any, *, max_length: int = 4096) -> str:
    if not isinstance(value, str):
        raise MemoryInputError(f"{name} must be a string")
    text = unicodedata.normalize("NFC", value).strip()
    if not text:
        raise MemoryInputError(f"{name} must not be empty")
    if len(text) > max_length:
        raise MemoryInputError(f"{name} exceeds the size limit")
    if "\x00" in text:
        raise MemoryInputError(f"{name} contains a null byte")
    return text


def _contains_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def _sanitize_for_cues(value: str) -> str:
    sanitized = unicodedata.normalize("NFC", value)
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(" REDACTED ", sanitized)
    return sanitized


def command_cues(value: str | Sequence[str]) -> list[str]:
    """Extract normalized cues without retaining the source text."""

    if isinstance(value, str):
        text = value
    elif isinstance(value, Sequence):
        if any(not isinstance(item, str) for item in value):
            raise MemoryInputError("command_cues must contain only strings")
        text = " ".join(value)
    else:
        raise MemoryInputError("command cues must be text or a list of strings")
    if len(text.encode("utf-8")) > MAX_JSON_BYTES:
        raise MemoryInputError("command input exceeds the size limit")
    cues: set[str] = set()
    for token in TOKEN_RE.findall(_sanitize_for_cues(text).lower()):
        normalized = CUE_ALIASES.get(token, token)
        if normalized not in STOP_CUES and len(normalized) <= 64:
            cues.add(normalized)
    if not cues:
        raise MemoryInputError("command input produced no safe cues")
    return sorted(cues)


def _require_identifier(name: str, value: Any, *, lower: bool = False) -> str:
    text = _require_text(name, value, max_length=256)
    if _contains_secret(text):
        raise MemoryInputError(f"{name} contains sensitive material")
    if any(marker in text for marker in EXECUTABLE_MARKERS):
        raise MemoryInputError(f"{name} contains executable material")
    if not IDENTIFIER_RE.fullmatch(text):
        raise MemoryInputError(f"{name} must be a declarative identifier")
    return text.lower() if lower else text


def _require_provenance(name: str, value: Any) -> str:
    text = _require_text(name, value, max_length=1024)
    if _contains_secret(text):
        raise MemoryInputError(f"{name} contains sensitive material")
    if any(marker in text for marker in EXECUTABLE_MARKERS):
        raise MemoryInputError(f"{name} contains executable material")
    return text


def _require_identifiers(name: str, value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise MemoryInputError(f"{name} must be an array")
    result = [_require_identifier(f"{name}[{index}]", item, lower=True) for index, item in enumerate(value)]
    if len(result) > 100:
        raise MemoryInputError(f"{name} has too many entries")
    return list(dict.fromkeys(result))


def _require_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise MemoryInputError(f"{name} must be a boolean")
    return value


def _decode_json(value: str) -> Any:
    return json.loads(value)


def _event_ref_digest(event_ref: str) -> str:
    return hashlib.sha256(
        ("nerd-memory-trusted-event\x00" + event_ref).encode("utf-8")
    ).hexdigest()


class BehaviorMemoryStore:
    """One clean global behavioral corpus with deterministic advisory recall."""

    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        *,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not isinstance(busy_timeout_ms, int) or busy_timeout_ms < 1:
            raise MemoryInputError("busy_timeout_ms must be a positive integer")
        self.path = Path(path) if path is not None else default_database_path()
        self.path = self.path.expanduser()
        self._clock = clock
        self._lock = threading.RLock()
        self._closed = False
        self._fenced = False
        self._database_id = ""
        self._file_identity: tuple[int, int] | None = None

        try:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=False)
        except FileExistsError:
            pass
        else:
            os.chmod(self.path.parent, 0o700)
        self._connection = sqlite3.connect(
            self.path,
            timeout=busy_timeout_ms / 1000,
            isolation_level=None,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
        self._connection.execute("PRAGMA foreign_keys=ON")
        try:
            tables = self._table_names()
            if tables:
                self._validate_existing_schema(tables)
            else:
                self._initialize_schema()
            self._enable_wal(busy_timeout_ms)
            self._connection.execute("PRAGMA synchronous=NORMAL")
            self._database_id = self._metadata()["database_id"]
            self._secure_database_files()
            file_stat = self.path.stat()
            self._file_identity = (file_stat.st_dev, file_stat.st_ino)
        except Exception:
            self._connection.close()
            self._closed = True
            raise

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def __enter__(self) -> "BehaviorMemoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._secure_database_files()
                self._connection.close()
                self._closed = True

    def _secure_database_files(self) -> None:
        for path in (
            self.path,
            Path(str(self.path) + "-wal"),
            Path(str(self.path) + "-shm"),
        ):
            if path.exists():
                os.chmod(path, 0o600)

    def _table_names(self) -> set[str]:
        return {
            str(row[0])
            for row in self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        }

    def _metadata(self) -> dict[str, str]:
        try:
            return {
                str(row["key"]): str(row["value"])
                for row in self._connection.execute("SELECT key, value FROM metadata")
            }
        except sqlite3.Error as error:
            raise MemorySchemaError("behavioral memory metadata is unreadable") from error

    def _validate_existing_schema(self, tables: set[str]) -> None:
        if tables != SCHEMA_TABLES:
            raise MemorySchemaError("database table inventory does not match schema family v1")
        metadata = self._metadata()
        if metadata.get("schema_family") != SCHEMA_FAMILY:
            raise MemorySchemaError("database belongs to another schema family")
        if metadata.get("schema_version") != str(SCHEMA_VERSION):
            raise MemorySchemaError("database schema version requires a runtime restart")
        if not metadata.get("database_id"):
            raise MemorySchemaError("database identity is missing")

    def _initialize_schema(self) -> None:
        database_id = str(uuid.uuid4())
        statements = (
            """
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE behavior_episodes (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                episode_id TEXT NOT NULL UNIQUE,
                repository TEXT NOT NULL,
                language TEXT NOT NULL,
                surface TEXT NOT NULL,
                project_kind TEXT NOT NULL,
                command_cues_json TEXT NOT NULL,
                action TEXT NOT NULL,
                tools_json TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                skills_json TEXT NOT NULL,
                output_signals_json TEXT NOT NULL,
                output_valid INTEGER NOT NULL CHECK (output_valid IN (0, 1)),
                output_severity TEXT NOT NULL,
                verified INTEGER NOT NULL CHECK (verified IN (0, 1)),
                verifier TEXT NOT NULL,
                feedback TEXT NOT NULL,
                corrected_tools_json TEXT NOT NULL,
                corrected_steps_json TEXT NOT NULL,
                corrected_skills_json TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                source_agent TEXT NOT NULL,
                evidence_ref TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE recall_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                consumer_agent TEXT NOT NULL,
                repository TEXT NOT NULL,
                language TEXT NOT NULL,
                surface TEXT NOT NULL,
                project_kind TEXT NOT NULL,
                command_cues_json TEXT NOT NULL,
                output_signals_json TEXT NOT NULL,
                outcome TEXT NOT NULL,
                confidence REAL NOT NULL,
                reject_output INTEGER NOT NULL CHECK (reject_output IN (0, 1)),
                source_episode_ids_json TEXT NOT NULL,
                overridden_fields_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE forget_previews (
                preview_id TEXT PRIMARY KEY,
                episode_ids_json TEXT NOT NULL,
                snapshot_digest TEXT NOT NULL,
                confirmation_phrase TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE trusted_event_tombstones (
                event_digest TEXT PRIMARY KEY,
                purpose TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        )
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            tables = self._table_names()
            if tables:
                self._validate_existing_schema(tables)
                self._connection.commit()
                return
            user_version = int(
                self._connection.execute("PRAGMA user_version").fetchone()[0]
            )
            application_id = int(
                self._connection.execute("PRAGMA application_id").fetchone()[0]
            )
            other_objects = int(
                self._connection.execute(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE name NOT LIKE 'sqlite_%'"
                ).fetchone()[0]
            )
            if user_version or application_id or other_objects:
                raise MemorySchemaError(
                    "non-empty database is not global behavioral memory"
                )
            for statement in statements:
                self._connection.execute(statement)
            self._connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                (
                    ("schema_family", SCHEMA_FAMILY),
                    ("schema_version", str(SCHEMA_VERSION)),
                    ("database_id", database_id),
                ),
            )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _enable_wal(self, busy_timeout_ms: int) -> None:
        deadline = time.monotonic() + busy_timeout_ms / 1000
        while True:
            try:
                mode = str(
                    self._connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]
                )
                if mode.lower() != "wal":
                    raise MemorySchemaError("behavioral memory requires WAL mode")
                return
            except sqlite3.OperationalError as error:
                if "locked" not in str(error).lower() or time.monotonic() >= deadline:
                    raise
                time.sleep(0.01)

    def _fence(self, message: str, error: Exception | None = None) -> None:
        self._fenced = True
        if error is None:
            raise MemorySchemaError(message)
        raise MemorySchemaError(message) from error

    def _assert_live(self) -> None:
        if self._closed:
            raise MemoryClosedError("behavioral memory store is closed")
        if self._fenced:
            raise MemorySchemaError("behavioral memory handle is permanently fenced")
        try:
            file_stat = self.path.stat()
            identity = (file_stat.st_dev, file_stat.st_ino)
            if self._file_identity is not None and identity != self._file_identity:
                self._fence("behavioral memory file changed; restart this runtime")
            metadata = self._metadata()
            if (
                metadata.get("schema_family") != SCHEMA_FAMILY
                or metadata.get("schema_version") != str(SCHEMA_VERSION)
                or metadata.get("database_id") != self._database_id
            ):
                self._fence("behavioral memory schema changed; restart this runtime")
        except MemorySchemaError:
            self._fenced = True
            raise
        except (OSError, sqlite3.Error) as error:
            self._fence("behavioral memory cannot verify its live schema", error)

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        with self._lock:
            self._assert_live()
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._assert_live()
                yield
                self._connection.commit()
                self._secure_database_files()
            except Exception:
                self._connection.rollback()
                raise

    def _normalize_episode(
        self,
        *,
        episode_id: str,
        repository: str,
        language: str,
        surface: str,
        project_kind: str,
        action: str,
        tools: Sequence[str],
        steps: Sequence[str],
        skills: Sequence[str],
        output_signals: Sequence[str],
        output_valid: bool,
        output_severity: str,
        verified: bool,
        verifier: str,
        feedback: str,
        source_kind: str,
        source_agent: str,
        evidence_ref: str,
        raw_input: str | None,
        command_cues_value: Sequence[str] | None,
        corrected_tools: Sequence[str],
        corrected_steps: Sequence[str],
        corrected_skills: Sequence[str],
        observed_at: str | None,
    ) -> dict[str, Any]:
        if (raw_input is None) == (command_cues_value is None):
            raise MemoryInputError("provide exactly one of raw_input or command_cues")
        cues = command_cues(raw_input if raw_input is not None else command_cues_value or ())
        source = _require_identifier("source_kind", source_kind, lower=True)
        if source not in SOURCE_KINDS:
            raise MemoryInputError("source_kind is not eligible behavioral evidence")
        feedback_value = _require_identifier("feedback", feedback, lower=True)
        if feedback_value not in FEEDBACK_VALUES:
            raise MemoryInputError("feedback is not supported")
        severity = _require_identifier("output_severity", output_severity, lower=True)
        if severity not in SEVERITY_VALUES:
            raise MemoryInputError("output_severity is not supported")
        is_verified = _require_bool("verified", verified)
        is_valid = _require_bool("output_valid", output_valid)
        if not is_verified:
            raise MemoryInputError("only verified behavior may be recorded")

        normalized_corrected_tools = _require_identifiers(
            "corrected_tools", corrected_tools
        )
        normalized_corrected_steps = _require_identifiers(
            "corrected_steps", corrected_steps
        )
        normalized_corrected_skills = _require_identifiers(
            "corrected_skills", corrected_skills
        )
        replacements = (
            normalized_corrected_tools
            or normalized_corrected_steps
            or normalized_corrected_skills
        )
        if source == "verified_execution":
            if feedback_value == "corrected" or replacements:
                raise MemoryInputError(
                    "verified_execution cannot assert a direct user correction"
                )
            if feedback_value == "accepted" and not is_valid:
                raise MemoryInputError("invalid output cannot be positive workflow evidence")
        else:
            if feedback_value != "corrected" or not replacements or not is_valid:
                raise MemoryInputError(
                    "user_correction requires valid corrected behavioral resources"
                )

        now = _utc_now(self._clock())
        return {
            "episode_id": _require_identifier("episode_id", episode_id),
            "repository": _require_provenance("repository", repository),
            "language": _require_identifier("language", language, lower=True),
            "surface": _require_identifier("surface", surface, lower=True),
            "project_kind": _require_identifier(
                "project_kind", project_kind, lower=True
            ),
            "command_cues": cues,
            "action": _require_identifier("action", action, lower=True),
            "tools": _require_identifiers("tools", tools),
            "steps": _require_identifiers("steps", steps),
            "skills": _require_identifiers("skills", skills),
            "output_signals": _require_identifiers(
                "output_signals", output_signals
            ),
            "output_valid": is_valid,
            "output_severity": severity,
            "verified": is_verified,
            "verifier": _require_identifier("verifier", verifier, lower=True),
            "feedback": feedback_value,
            "corrected_tools": normalized_corrected_tools,
            "corrected_steps": normalized_corrected_steps,
            "corrected_skills": normalized_corrected_skills,
            "source_kind": source,
            "source_agent": _require_identifier(
                "source_agent", source_agent, lower=True
            ),
            "evidence_ref": _require_identifier("evidence_ref", evidence_ref),
            "observed_at": _parse_utc("observed_at", observed_at)
            if observed_at is not None
            else now,
            "created_at": now,
        }

    @staticmethod
    def _episode_identity(episode: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in episode.items()
            if key not in {"sequence", "observed_at", "created_at"}
        }

    @staticmethod
    def _episode_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "sequence": int(row["sequence"]),
            "episode_id": str(row["episode_id"]),
            "repository": str(row["repository"]),
            "language": str(row["language"]),
            "surface": str(row["surface"]),
            "project_kind": str(row["project_kind"]),
            "command_cues": _decode_json(row["command_cues_json"]),
            "action": str(row["action"]),
            "tools": _decode_json(row["tools_json"]),
            "steps": _decode_json(row["steps_json"]),
            "skills": _decode_json(row["skills_json"]),
            "output_signals": _decode_json(row["output_signals_json"]),
            "output_valid": bool(row["output_valid"]),
            "output_severity": str(row["output_severity"]),
            "verified": bool(row["verified"]),
            "verifier": str(row["verifier"]),
            "feedback": str(row["feedback"]),
            "corrected_tools": _decode_json(row["corrected_tools_json"]),
            "corrected_steps": _decode_json(row["corrected_steps_json"]),
            "corrected_skills": _decode_json(row["corrected_skills_json"]),
            "source_kind": str(row["source_kind"]),
            "source_agent": str(row["source_agent"]),
            "evidence_ref": str(row["evidence_ref"]),
            "observed_at": str(row["observed_at"]),
            "created_at": str(row["created_at"]),
        }

    def record(
        self,
        *,
        episode_id: str,
        repository: str,
        language: str,
        surface: str,
        project_kind: str,
        action: str,
        tools: Sequence[str],
        steps: Sequence[str],
        skills: Sequence[str],
        output_signals: Sequence[str],
        output_valid: bool,
        output_severity: str,
        verified: bool,
        verifier: str,
        feedback: str,
        source_kind: str,
        source_agent: str,
        evidence_ref: str,
        raw_input: str | None = None,
        command_cues: Sequence[str] | None = None,
        corrected_tools: Sequence[str] = (),
        corrected_steps: Sequence[str] = (),
        corrected_skills: Sequence[str] = (),
        observed_at: str | None = None,
    ) -> dict[str, Any]:
        """Record host-classified proof; agent labels remain provenance only."""

        normalized = self._normalize_episode(
            episode_id=episode_id,
            repository=repository,
            language=language,
            surface=surface,
            project_kind=project_kind,
            action=action,
            tools=tools,
            steps=steps,
            skills=skills,
            output_signals=output_signals,
            output_valid=output_valid,
            output_severity=output_severity,
            verified=verified,
            verifier=verifier,
            feedback=feedback,
            source_kind=source_kind,
            source_agent=source_agent,
            evidence_ref=evidence_ref,
            raw_input=raw_input,
            command_cues_value=command_cues,
            corrected_tools=corrected_tools,
            corrected_steps=corrected_steps,
            corrected_skills=corrected_skills,
            observed_at=observed_at,
        )
        with self._transaction():
            row = self._connection.execute(
                "SELECT * FROM behavior_episodes WHERE episode_id=?",
                (normalized["episode_id"],),
            ).fetchone()
            if row is not None:
                existing = self._episode_from_row(row)
                if self._episode_identity(existing) != self._episode_identity(normalized):
                    raise MemoryInvariantError(
                        "episode_id already binds different behavioral evidence"
                    )
                return {"episode": existing, "idempotent": True}
            self._connection.execute(
                """
                INSERT INTO behavior_episodes(
                    episode_id, repository, language, surface, project_kind,
                    command_cues_json, action, tools_json, steps_json, skills_json,
                    output_signals_json, output_valid, output_severity, verified,
                    verifier, feedback, corrected_tools_json,
                    corrected_steps_json, corrected_skills_json, source_kind,
                    source_agent, evidence_ref, observed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized["episode_id"],
                    normalized["repository"],
                    normalized["language"],
                    normalized["surface"],
                    normalized["project_kind"],
                    canonical_json(normalized["command_cues"]),
                    normalized["action"],
                    canonical_json(normalized["tools"]),
                    canonical_json(normalized["steps"]),
                    canonical_json(normalized["skills"]),
                    canonical_json(normalized["output_signals"]),
                    int(normalized["output_valid"]),
                    normalized["output_severity"],
                    int(normalized["verified"]),
                    normalized["verifier"],
                    normalized["feedback"],
                    canonical_json(normalized["corrected_tools"]),
                    canonical_json(normalized["corrected_steps"]),
                    canonical_json(normalized["corrected_skills"]),
                    normalized["source_kind"],
                    normalized["source_agent"],
                    normalized["evidence_ref"],
                    normalized["observed_at"],
                    normalized["created_at"],
                ),
            )
            row = self._connection.execute(
                "SELECT * FROM behavior_episodes WHERE episode_id=?",
                (normalized["episode_id"],),
            ).fetchone()
            assert row is not None
            return {"episode": self._episode_from_row(row), "idempotent": False}

    @staticmethod
    def _winner(counter: Counter[Any]) -> tuple[Any | None, int, int, bool]:
        if not counter:
            return None, 0, 0, False
        ranked = sorted(counter.items(), key=lambda item: (-item[1], canonical_json(item[0])))
        tied = len(ranked) > 1 and ranked[0][1] == ranked[1][1]
        return ranked[0][0], ranked[0][1], sum(counter.values()), tied

    def _resource_winner(
        self, episodes: Sequence[Mapping[str, Any]], field: str
    ) -> tuple[list[str], set[str]]:
        corrected_field = f"corrected_{field}"
        counts: Counter[tuple[str, ...]] = Counter()
        source_map: dict[tuple[str, ...], set[str]] = {}
        retired: set[tuple[str, ...]] = set()
        correction_streak = 0
        for episode in episodes:
            corrected = tuple(episode[corrected_field])
            original = tuple(episode[field])
            value = corrected if episode["feedback"] == "corrected" and corrected else original
            if episode["feedback"] == "corrected":
                correction_streak += 1
                if correction_streak >= CORRECTION_RETIREMENT_COUNT:
                    retired.update(item for item in counts if item != value)
            counts[value] += 1
            source_map.setdefault(value, set()).add(str(episode["episode_id"]))
        available = Counter(
            {value: count for value, count in counts.items() if value not in retired}
        )
        winner, _, _, _ = self._winner(available)
        if winner is None:
            return [], set()
        return list(winner), set(source_map.get(winner, set()))

    @staticmethod
    def _validate_current(current: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(current, Mapping):
            raise MemoryInputError("current must be an object")
        unexpected = set(current) - set(CURRENT_FIELDS)
        if unexpected:
            raise MemoryInputError(
                "current contains unsupported fields: " + ", ".join(sorted(unexpected))
            )
        normalized: dict[str, Any] = {}
        if "action" in current:
            action = current["action"]
            if action is not None and not isinstance(action, str):
                raise MemoryInputError("current.action must be text or null")
            normalized["action"] = copy.deepcopy(action)
        for field in ("tools", "steps", "skills"):
            if field in current:
                value = current[field]
                if not isinstance(value, list) or any(
                    not isinstance(item, str) for item in value
                ):
                    raise MemoryInputError(f"current.{field} must be an array of strings")
                normalized[field] = copy.deepcopy(value)
        return normalized

    def recall(
        self,
        *,
        event_id: str,
        raw_input: str,
        repository: str,
        language: str,
        surface: str,
        project_kind: str,
        current: Mapping[str, Any],
        output_signals: Sequence[str],
        consumer_agent: str,
    ) -> dict[str, Any]:
        """Return contextual M3 advice, resolve current choices, and audit once."""

        normalized_event_id = _require_identifier("event_id", event_id)
        cues = command_cues(raw_input)
        normalized_repository = _require_provenance("repository", repository)
        normalized_context = {
            "language": _require_identifier("language", language, lower=True),
            "surface": _require_identifier("surface", surface, lower=True),
            "project_kind": _require_identifier(
                "project_kind", project_kind, lower=True
            ),
        }
        normalized_signals = _require_identifiers("output_signals", output_signals)
        normalized_agent = _require_identifier(
            "consumer_agent", consumer_agent, lower=True
        )
        current_values = self._validate_current(current)

        with self._transaction():
            if self._connection.execute(
                "SELECT 1 FROM recall_events WHERE event_id=?", (normalized_event_id,)
            ).fetchone():
                raise MemoryInvariantError("event_id already has a recall audit")
            rows = self._connection.execute(
                """
                SELECT * FROM behavior_episodes
                WHERE language=? AND surface=? AND project_kind=?
                ORDER BY sequence, episode_id
                """,
                (
                    normalized_context["language"],
                    normalized_context["surface"],
                    normalized_context["project_kind"],
                ),
            ).fetchall()
            episodes = [self._episode_from_row(row) for row in rows]

            positive = [
                episode
                for episode in episodes
                if episode["verified"]
                and episode["output_valid"]
                and episode["feedback"] in {"accepted", "corrected"}
            ]
            cue_set = set(cues)
            action_counts: Counter[str] = Counter()
            action_source_map: dict[str, set[str]] = {}
            for episode in positive:
                overlap = cue_set.intersection(episode["command_cues"])
                if overlap:
                    action_counts[episode["action"]] += len(overlap)
                    action_source_map.setdefault(episode["action"], set()).add(
                        episode["episode_id"]
                    )
            action, action_count, total, tied = self._winner(action_counts)
            confidence = action_count / total if total else 0.0
            abstained = action is None or tied or confidence < ABSTAIN_THRESHOLD

            source_ids = set(action_source_map.get(action, set()))
            tools: list[str] = []
            steps: list[str] = []
            skills: list[str] = []
            if not abstained and action is not None:
                resource_episodes = [
                    episode for episode in positive if episode["action"] == action
                ]
                tools, tool_sources = self._resource_winner(resource_episodes, "tools")
                steps, step_sources = self._resource_winner(resource_episodes, "steps")
                skills, skill_sources = self._resource_winner(resource_episodes, "skills")
                source_ids.update(tool_sources | step_sources | skill_sources)

            reject_output = False
            for signal in normalized_signals:
                compatible = [
                    episode
                    for episode in episodes
                    if episode["verified"] and signal in episode["output_signals"]
                ]
                if compatible:
                    source_ids.update(episode["episode_id"] for episode in compatible)
                    invalid = sum(
                        int(
                            not episode["output_valid"]
                            or episode["feedback"] == "rejected"
                        )
                        for episode in compatible
                    )
                    if invalid / len(compatible) >= INVALID_SHARE_THRESHOLD:
                        reject_output = True

            advice = {
                "action": None if abstained else action,
                "tools": [] if abstained else tools,
                "steps": [] if abstained else steps,
                "step_edges": []
                if abstained
                else [[steps[index], steps[index + 1]] for index in range(len(steps) - 1)],
                "skills": [] if abstained else skills,
                "reject_output": reject_output,
                "abstained": abstained,
                "confidence": confidence,
                "origin": "behavioral_memory_advice",
                "source_episode_ids": sorted(source_ids),
            }
            resolved = copy.deepcopy(advice)
            overridden_fields: list[str] = []
            for field in CURRENT_FIELDS:
                if field not in current_values:
                    continue
                value = current_values[field]
                if value is not None and value != "" and value != []:
                    resolved[field] = copy.deepcopy(value)
                    overridden_fields.append(field)
            if "steps" in overridden_fields:
                resolved_steps = resolved["steps"]
                resolved["step_edges"] = [
                    [resolved_steps[index], resolved_steps[index + 1]]
                    for index in range(len(resolved_steps) - 1)
                ]
            resolved["authority_source"] = "current_request"

            outcome = "rejected" if reject_output else ("abstained" if abstained else "advice")
            created_at = _utc_now(self._clock())
            self._connection.execute(
                """
                INSERT INTO recall_events(
                    event_id, consumer_agent, repository, language, surface,
                    project_kind, command_cues_json, output_signals_json, outcome,
                    confidence, reject_output, source_episode_ids_json,
                    overridden_fields_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_event_id,
                    normalized_agent,
                    normalized_repository,
                    normalized_context["language"],
                    normalized_context["surface"],
                    normalized_context["project_kind"],
                    canonical_json(cues),
                    canonical_json(normalized_signals),
                    outcome,
                    confidence,
                    int(reject_output),
                    canonical_json(sorted(source_ids)),
                    canonical_json(overridden_fields),
                    created_at,
                ),
            )
            self._connection.execute(
                """
                DELETE FROM recall_events
                WHERE sequence NOT IN (
                    SELECT sequence FROM recall_events ORDER BY sequence DESC LIMIT ?
                )
                """,
                (MAX_RECALL_EVENTS,),
            )
            return {
                "audit_event_id": normalized_event_id,
                "advice": advice,
                "resolved_advice": resolved,
                "overridden_fields": overridden_fields,
            }

    @staticmethod
    def _recall_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "sequence": int(row["sequence"]),
            "event_id": str(row["event_id"]),
            "consumer_agent": str(row["consumer_agent"]),
            "repository": str(row["repository"]),
            "language": str(row["language"]),
            "surface": str(row["surface"]),
            "project_kind": str(row["project_kind"]),
            "command_cues": _decode_json(row["command_cues_json"]),
            "output_signals": _decode_json(row["output_signals_json"]),
            "outcome": str(row["outcome"]),
            "confidence": float(row["confidence"]),
            "reject_output": bool(row["reject_output"]),
            "source_episode_ids": _decode_json(row["source_episode_ids_json"]),
            "overridden_fields": _decode_json(row["overridden_fields_json"]),
            "created_at": str(row["created_at"]),
        }

    def inspect(self, *, limit: int = 20) -> dict[str, Any]:
        """Return bounded sanitized summaries and active schema counts."""

        if not isinstance(limit, int) or isinstance(limit, bool) or not 0 <= limit <= MAX_INSPECT_ITEMS:
            raise MemoryInputError(f"limit must be between 0 and {MAX_INSPECT_ITEMS}")
        with self._lock:
            self._assert_live()
            counts = {
                table: int(
                    self._connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                )
                for table in (
                    "behavior_episodes",
                    "recall_events",
                    "forget_previews",
                    "trusted_event_tombstones",
                )
            }
            episode_rows = self._connection.execute(
                "SELECT * FROM behavior_episodes ORDER BY sequence LIMIT ?", (limit,)
            ).fetchall()
            recall_rows = self._connection.execute(
                "SELECT * FROM recall_events ORDER BY sequence LIMIT ?", (limit,)
            ).fetchall()
            previews = [
                {
                    "preview_id": str(row["preview_id"]),
                    "episode_ids": _decode_json(row["episode_ids_json"]),
                    "digest": str(row["snapshot_digest"]),
                    "created_at": str(row["created_at"]),
                    "expires_at": str(row["expires_at"]),
                }
                for row in self._connection.execute(
                    "SELECT * FROM forget_previews ORDER BY created_at LIMIT ?", (limit,)
                )
            ]
            return {
                "schema_family": SCHEMA_FAMILY,
                "schema_version": SCHEMA_VERSION,
                "database_path": str(self.path),
                "counts": counts,
                "episodes": [self._episode_from_row(row) for row in episode_rows],
                "recall_events": [self._recall_from_row(row) for row in recall_rows],
                "forget_previews": previews,
            }

    def _snapshot(self, episode_ids: Sequence[str]) -> tuple[list[dict[str, Any]], str]:
        placeholders = ",".join("?" for _ in episode_ids)
        rows = self._connection.execute(
            f"SELECT * FROM behavior_episodes WHERE episode_id IN ({placeholders}) "
            "ORDER BY episode_id",
            tuple(episode_ids),
        ).fetchall()
        episodes = [self._episode_from_row(row) for row in rows]
        if [episode["episode_id"] for episode in episodes] != sorted(episode_ids):
            raise MemoryNotFoundError("one or more behavior episodes do not exist")
        return episodes, canonical_digest({"episodes": episodes})

    def preview_forget(
        self, episode_ids: Sequence[str], *, ttl_seconds: int = DEFAULT_FORGET_TTL_SECONDS
    ) -> dict[str, Any]:
        """Bind an exact episode snapshot to a short-lived deletion phrase."""

        if not isinstance(episode_ids, (list, tuple)) or not episode_ids:
            raise MemoryInputError("episode_ids must be a non-empty array")
        if len(episode_ids) > 1_000:
            raise MemoryInputError("too many episodes in one forget preview")
        normalized_ids = sorted(
            {_require_identifier("episode_id", value) for value in episode_ids}
        )
        if len(normalized_ids) != len(episode_ids):
            raise MemoryInputError("episode_ids must be unique")
        if not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 3_600:
            raise MemoryInputError("ttl_seconds must be between 1 and 3600")
        with self._transaction():
            _, digest = self._snapshot(normalized_ids)
            preview_id = str(uuid.uuid4())
            phrase = f"forget {len(normalized_ids)} behavior episodes {digest[7:19]}"
            now_epoch = self._clock()
            created_at = _utc_now(now_epoch)
            expires_at = _utc_now(now_epoch + ttl_seconds)
            self._connection.execute(
                """
                INSERT INTO forget_previews(
                    preview_id, episode_ids_json, snapshot_digest,
                    confirmation_phrase, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    preview_id,
                    canonical_json(normalized_ids),
                    digest,
                    phrase,
                    created_at,
                    expires_at,
                ),
            )
            return {
                "preview_id": preview_id,
                "episode_ids": normalized_ids,
                "digest": digest,
                "confirmation_phrase": phrase,
                "created_at": created_at,
                "expires_at": expires_at,
            }

    def forget(
        self,
        preview_id: str,
        phrase: str,
        *,
        source: str,
        event_ref: str,
    ) -> dict[str, Any]:
        """Atomically forget a fresh preview using a fresh direct-user event."""

        normalized_preview_id = _require_identifier("preview_id", preview_id)
        if source != "direct_user":
            raise MemoryInputError("forget requires a direct_user event")
        normalized_event_ref = _require_identifier("event_ref", event_ref)
        if not isinstance(phrase, str) or "\x00" in phrase:
            raise MemoryInputError("phrase must be exact text")
        event_digest = _event_ref_digest(normalized_event_ref)
        with self._transaction():
            if self._connection.execute(
                "SELECT 1 FROM trusted_event_tombstones WHERE event_digest=?",
                (event_digest,),
            ).fetchone():
                raise MemoryInvariantError("trusted direct-user event was already consumed")
            preview = self._connection.execute(
                "SELECT * FROM forget_previews WHERE preview_id=?",
                (normalized_preview_id,),
            ).fetchone()
            if preview is None:
                raise MemoryNotFoundError("forget preview does not exist")
            expires_at = datetime.fromisoformat(
                str(preview["expires_at"]).replace("Z", "+00:00")
            ).timestamp()
            if self._clock() > expires_at:
                raise MemoryInvariantError("forget preview expired")
            if phrase != preview["confirmation_phrase"]:
                raise MemoryInvariantError("forget phrase does not match current preview")
            episode_ids = _decode_json(preview["episode_ids_json"])
            _, current_digest = self._snapshot(episode_ids)
            if current_digest != preview["snapshot_digest"]:
                raise MemoryInvariantError("forget preview no longer matches current evidence")

            deleted_recall_events = 0
            for row in self._connection.execute(
                "SELECT sequence, source_episode_ids_json FROM recall_events"
            ).fetchall():
                sources = set(_decode_json(row["source_episode_ids_json"]))
                if sources.intersection(episode_ids):
                    self._connection.execute(
                        "DELETE FROM recall_events WHERE sequence=?", (row["sequence"],)
                    )
                    deleted_recall_events += 1
            placeholders = ",".join("?" for _ in episode_ids)
            self._connection.execute(
                f"DELETE FROM behavior_episodes WHERE episode_id IN ({placeholders})",
                tuple(episode_ids),
            )
            for row in self._connection.execute(
                "SELECT preview_id, episode_ids_json FROM forget_previews"
            ).fetchall():
                bound_ids = set(_decode_json(row["episode_ids_json"]))
                if bound_ids.intersection(episode_ids):
                    self._connection.execute(
                        "DELETE FROM forget_previews WHERE preview_id=?", (row["preview_id"],)
                    )
            created_at = _utc_now(self._clock())
            self._connection.execute(
                "INSERT INTO trusted_event_tombstones(event_digest, purpose, created_at) "
                "VALUES (?, 'forget', ?)",
                (event_digest, created_at),
            )
            return {
                "deleted_episode_ids": list(episode_ids),
                "deleted_recall_events": deleted_recall_events,
                "event_consumed": True,
                "created_at": created_at,
            }


def _json_argument(name: str, value: str) -> Any:
    if len(value.encode("utf-8")) > MAX_JSON_BYTES:
        raise MemoryInputError(f"{name} exceeds the size limit")
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise MemoryInputError(f"{name} must be valid JSON") from error


def _invoke_object(method: Callable[..., Any], name: str, value: Any) -> Any:
    if not isinstance(value, Mapping):
        raise MemoryInputError(f"{name} must be a JSON object")
    signature = python_inspect.signature(method)
    allowed = set(signature.parameters)
    unknown = set(value) - allowed
    if unknown:
        raise MemoryInputError(
            f"{name} contains unsupported fields: " + ", ".join(sorted(unknown))
        )
    try:
        return method(**value)
    except TypeError as error:
        raise MemoryInputError(f"{name} does not satisfy the command contract") from error


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise MemoryInputError(message)


def _build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Global behavioral memory runtime")
    parser.add_argument("--db", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)

    record = commands.add_parser("record", help="record one verified behavior episode")
    record.add_argument("--episode", required=True, metavar="JSON_OBJECT")

    recall = commands.add_parser("recall", help="recall contextual behavioral advice")
    recall.add_argument("--request", required=True, metavar="JSON_OBJECT")

    inspect_command = commands.add_parser("inspect", help="inspect bounded summaries")
    inspect_command.add_argument("--limit", type=int, default=20)

    preview = commands.add_parser("preview-forget", help="preview exact episode deletion")
    preview.add_argument("--episode-ids", required=True, metavar="JSON_ARRAY")
    preview.add_argument("--ttl-seconds", type=int, default=DEFAULT_FORGET_TTL_SECONDS)

    forget = commands.add_parser("forget", help="apply one trusted deletion preview")
    forget.add_argument("--request", required=True, metavar="JSON_OBJECT")
    return parser


def _run_command(store: BehaviorMemoryStore, arguments: Any) -> Any:
    if arguments.command == "record":
        return _invoke_object(
            store.record, "--episode", _json_argument("--episode", arguments.episode)
        )
    if arguments.command == "recall":
        return _invoke_object(
            store.recall, "--request", _json_argument("--request", arguments.request)
        )
    if arguments.command == "inspect":
        return store.inspect(limit=arguments.limit)
    if arguments.command == "preview-forget":
        episode_ids = _json_argument("--episode-ids", arguments.episode_ids)
        return store.preview_forget(episode_ids, ttl_seconds=arguments.ttl_seconds)
    if arguments.command == "forget":
        return _invoke_object(
            store.forget, "--request", _json_argument("--request", arguments.request)
        )
    raise MemoryInputError("unknown memory command")


ERROR_CODES: tuple[tuple[type[BaseException], str, int], ...] = (
    (MemoryNotFoundError, "not_found", 4),
    (MemorySchemaError, "restart_required", 3),
    (MemoryClosedError, "closed", 3),
    (MemoryInvariantError, "invariant_violation", 3),
    (MemoryInputError, "invalid_input", 2),
    (sqlite3.Error, "storage_error", 6),
)


def _emit_json(value: Any, *, stream: Any = sys.stdout) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
    stream.flush()


def main(argv: Sequence[str] | None = None) -> int:
    store: BehaviorMemoryStore | None = None
    try:
        arguments = _build_parser().parse_args(argv)
        store = BehaviorMemoryStore(arguments.db)
        _emit_json(_run_command(store, arguments))
        return 0
    except KeyboardInterrupt:
        _emit_json(
            {
                "ok": False,
                "error": {
                    "code": "interrupted",
                    "type": "KeyboardInterrupt",
                    "message": "interrupted",
                },
            },
            stream=sys.stderr,
        )
        return 130
    except Exception as error:
        for error_type, code, exit_code in ERROR_CODES:
            if isinstance(error, error_type):
                _emit_json(
                    {
                        "ok": False,
                        "error": {
                            "code": code,
                            "type": type(error).__name__,
                            "message": str(error),
                        },
                    },
                    stream=sys.stderr,
                )
                return exit_code
        _emit_json(
            {
                "ok": False,
                "error": {
                    "code": "internal_error",
                    "type": type(error).__name__,
                    "message": "unexpected memory engine failure",
                },
            },
            stream=sys.stderr,
        )
        return 1
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
