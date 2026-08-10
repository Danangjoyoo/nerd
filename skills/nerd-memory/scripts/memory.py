#!/usr/bin/env python3
"""A local, confirmation-gated memory evidence store.

The store deliberately separates five states:

* observations are inert evidence;
* consolidated patterns are candidates;
* promoted patterns may influence a proposal;
* an exact, expiring, one-use grant may consume that proposal.
* a denied proposal is inert until an independently confirmed refinement.

Memory confirmation is never action authorization.  The returned
``memory_gate_only`` flag makes that boundary explicit to callers.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence
import argparse
import copy
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
import unicodedata
import uuid


PATTERN_TYPES = (
    "goal",
    "task",
    "action",
    "result",
    "boundary",
    "verification",
    "routing",
)
ENDPOINT_TYPES = frozenset(
    {
        "discuss",
        "ideate",
        "explore",
        "diagnose",
        "review",
        "specify",
        "document",
        "plan",
        "execute",
        "monitor",
        "abstain",
    }
)
ENDPOINT_FIELDS = frozenset({"endpoint", *PATTERN_TYPES})
LIST_PATTERN_TYPES = frozenset(
    {"task", "action", "boundary", "verification", "routing"}
)
ELIGIBLE_SOURCES = frozenset({"direct_user", "user_correction"})
INERT_SOURCES = frozenset({"agent_inference"})
OBSERVATION_SOURCES = ELIGIBLE_SOURCES | INERT_SOURCES
OPERATIONS = frozenset({"fill", "append", "prepend"})
DENIAL_RESOLUTIONS = frozenset({"agent_mistake", "human_forgot"})
DEFAULT_MIN_EPISODES = 3
DEFAULT_GRANT_TTL_SECONDS = 300
MAX_JSON_BYTES = 1_000_000
SCHEMA_VERSION = 8
BASELINE_ATTESTATION_EFFECT = (
    "provenance only; does not confirm memory or authorize action"
)
_VERSION_FENCED_TABLES = (
    "consents",
    "consent_events",
    "observations",
    "patterns",
    "pattern_evidence",
    "forgotten_patterns",
    "proposals",
    "confirmation_events",
    "confirmation_ref_tombstones",
    "denials",
    "split_proposals",
    "split_parent_bindings",
    "proposal_patterns",
)

_VOLATILE_SPLIT_SCOPE_KEYS = frozenset(
    {
        "episode_id",
        "message_id",
        "proposal_id",
        "request_id",
        "session_id",
        "thread_id",
        "timestamp",
        "turn_id",
    }
)
_VOLATILE_SPLIT_SCOPE_KEYS_COMPACT = frozenset(
    item.replace("_", "") for item in _VOLATILE_SPLIT_SCOPE_KEYS
)


class MemoryEngineError(Exception):
    """Base class for expected memory-engine failures."""


class MemoryInputError(MemoryEngineError, ValueError):
    """The caller supplied invalid or unsafe input."""


class MemoryInvariantError(MemoryEngineError, RuntimeError):
    """A safety or lifecycle invariant would be violated."""


class MemoryBaselineCollisionError(MemoryInvariantError):
    """A purportedly explicit baseline overlaps memory-derived material."""

    def __init__(self, message: str, collisions: Sequence[Mapping[str, Any]]) -> None:
        super().__init__(message)
        self.collisions = copy.deepcopy(list(collisions))


class MemoryNotFoundError(MemoryEngineError, LookupError):
    """A requested memory object does not exist."""


class MemoryConsentError(MemoryInvariantError):
    """The namespace has no active, explicit memory consent."""


def _utc_now(epoch_seconds: float | None = None) -> str:
    if epoch_seconds is None:
        epoch_seconds = time.time()
    return (
        datetime.fromtimestamp(epoch_seconds, timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _normalise_json(value: Any, *, depth: int = 0) -> Any:
    """Return a canonicalisable JSON value, rejecting ambiguous input."""

    if depth > 100:
        raise MemoryInputError("JSON input is nested too deeply")
    if value is None or isinstance(value, bool) or isinstance(value, int):
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
    """Encode JSON deterministically after Unicode and value validation."""

    normalised = _normalise_json(value)
    encoded = json.dumps(
        normalised,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise MemoryInputError("memory JSON exceeds the size limit")
    return encoded


def canonical_hash(value: Any) -> str:
    """Return a SHA-256 digest of the canonical JSON representation."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _confirmation_ref_digest(confirmation_ref: str) -> str:
    return hashlib.sha256(
        ("nerd-memory-confirmation-ref\x00" + confirmation_ref).encode("utf-8")
    ).hexdigest()


def _decode_json(value: str) -> Any:
    return json.loads(value)


def _require_text(name: str, value: Any, *, max_length: int = 4096) -> str:
    if not isinstance(value, str):
        raise MemoryInputError(f"{name} must be a string")
    result = unicodedata.normalize("NFC", value).strip()
    if not result:
        raise MemoryInputError(f"{name} must not be empty")
    if len(result) > max_length:
        raise MemoryInputError(f"{name} exceeds the size limit")
    if "\x00" in result:
        raise MemoryInputError(f"{name} contains a null byte")
    return result


_SECRET_PATTERNS = (
    re.compile(r"(?i)(?<![a-z0-9])sk-[a-z0-9_-]{16,}"),
    re.compile(r"(?i)(?<![a-z0-9])gh(?:p|o|u|s|r)_[a-z0-9]{20,}"),
    re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(
        r"(?i)\b(?:password|passwd|pwd|api[_ -]?key|access[_ -]?token|"
        r"refresh[_ -]?token|client[_ -]?secret)\s*[:=]\s*[^\s,;]{4,}"
    ),
    re.compile(r"(?i)\b(?:bearer|basic)\s+[a-z0-9._~+/=-]{12,}"),
    re.compile(r"\beyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:]+:[^\s/@]+@"),
)


def _reject_sensitive(*values: Any) -> None:
    text = "\n".join(canonical_json(value) for value in values)
    if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
        raise MemoryInputError("sensitive credential material cannot be persisted")


def _normalise_scope(scope: Any) -> dict[str, Any]:
    if scope is None:
        return {}
    normalised = _normalise_json(scope)
    if not isinstance(normalised, dict):
        raise MemoryInputError("scope must be a JSON object")
    return normalised


def _normalise_triggers(triggers: Any) -> list[str]:
    if triggers is None:
        return []
    if not isinstance(triggers, (list, tuple)):
        raise MemoryInputError("triggers must be a list of strings")
    result: list[str] = []
    seen: set[str] = set()
    for trigger in triggers:
        text = _require_text("trigger", trigger, max_length=256).casefold()
        if text not in seen:
            seen.add(text)
            result.append(text)
    result.sort()
    return result


def _validate_pattern_value(pattern_type: str, value: Any, operation: str) -> Any:
    normalised = _normalise_json(value)
    if normalised is None:
        raise MemoryInputError("pattern value must not be null")
    if pattern_type == "routing":
        if operation != "fill":
            raise MemoryInputError(
                "routing profiles must use fill so learned execution stacks are not composed"
            )
        if not isinstance(normalised, list) or not normalised:
            raise MemoryInputError(
                "routing pattern value must be a non-empty list of route profiles"
            )
        if len(normalised) > 8:
            raise MemoryInputError(
                "routing pattern may contain at most 8 ordered profiles"
            )
        routes: list[dict[str, Any]] = []
        seen: set[str] = set()
        agents_seen: set[str] = set()
        identifier = re.compile(
            r"^[a-z0-9](?:[a-z0-9._:+-]*[a-z0-9])?$"
        )
        for route in normalised:
            if not isinstance(route, dict) or set(route) != {
                "agent",
                "skills",
                "tools",
                "mcp_servers",
            }:
                raise MemoryInputError(
                    "each routing profile needs exactly agent, skills, tools, and mcp_servers"
                )
            agent = _require_text("routing agent", route["agent"], max_length=128).casefold()
            if not identifier.fullmatch(agent):
                raise MemoryInputError(
                    "routing agent must be a stable lowercase identifier"
                )
            if ".." in agent:
                raise MemoryInputError(
                    "routing agent must not contain path-like traversal"
                )
            if agent in agents_seen:
                raise MemoryInputError(
                    "routing pattern may contain only one atomic profile per agent"
                )
            agents_seen.add(agent)

            profile: dict[str, Any] = {"agent": agent}
            for field, label in (
                ("skills", "skill"),
                ("tools", "tool"),
                ("mcp_servers", "MCP server"),
            ):
                raw_identifiers = route[field]
                if not isinstance(raw_identifiers, list):
                    raise MemoryInputError(f"routing {field} must be a list")
                if len(raw_identifiers) > 16:
                    raise MemoryInputError(
                        f"routing {field} may contain at most 16 identifiers"
                    )
                identifiers: list[str] = []
                identifiers_seen: set[str] = set()
                for raw_identifier in raw_identifiers:
                    item = _require_text(
                        f"routing {label}", raw_identifier, max_length=128
                    )
                    if field == "skills" and item.startswith("$"):
                        item = item[1:]
                    item = item.casefold()
                    if not identifier.fullmatch(item):
                        raise MemoryInputError(
                            f"routing {label} must be a stable lowercase identifier"
                        )
                    if ".." in item:
                        raise MemoryInputError(
                            f"routing {label} must not contain path-like traversal"
                        )
                    if item in identifiers_seen:
                        raise MemoryInputError(
                            f"routing profile contains a duplicate {label}"
                        )
                    identifiers_seen.add(item)
                    identifiers.append(item)
                profile[field] = sorted(identifiers)
            if sum(
                len(profile[field])
                for field in ("skills", "tools", "mcp_servers")
            ) > 24:
                raise MemoryInputError(
                    "routing profile may contain at most 24 total capabilities"
                )
            if not any(profile[field] for field in ("skills", "tools", "mcp_servers")):
                raise MemoryInputError(
                    "routing profile must name at least one skill, tool, or MCP server"
                )
            profile_hash = canonical_json(profile)
            if profile_hash in seen:
                raise MemoryInputError("routing pattern contains a duplicate profile")
            seen.add(profile_hash)
            routes.append(profile)
        normalised = routes
    if pattern_type in LIST_PATTERN_TYPES:
        if not isinstance(normalised, list) or not normalised:
            raise MemoryInputError(f"{pattern_type} pattern value must be a non-empty list")
    elif operation != "fill":
        raise MemoryInputError(f"{operation} is only valid for list-valued patterns")
    if normalised == "":
        raise MemoryInputError("pattern value must not be empty")
    return normalised


def _decode_stored_pattern_value(
    pattern_type: str,
    value_json: str,
    operation: str,
) -> Any:
    try:
        value = _decode_json(value_json)
    except (ValueError, TypeError) as error:
        raise MemoryInvariantError("persisted pattern value is invalid JSON") from error
    if pattern_type != "routing":
        return value
    try:
        validated = _validate_pattern_value(pattern_type, value, operation)
    except MemoryInputError as error:
        raise MemoryInvariantError(
            "persisted routing profile violates the atomic route contract"
        ) from error
    if canonical_json(validated) != value_json:
        raise MemoryInvariantError(
            "persisted routing profile is not in canonical atomic form"
        )
    return validated


def _scope_matches(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(key in actual and _scope_matches(value, actual[key]) for key, value in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return canonical_json(expected) == canonical_json(actual)
    return canonical_json(expected) == canonical_json(actual)


def _scopes_overlap(left: Any, right: Any) -> bool:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return canonical_json(left) == canonical_json(right)
    for key in left.keys() & right.keys():
        left_value = left[key]
        right_value = right[key]
        if isinstance(left_value, dict) and isinstance(right_value, dict):
            if not _scopes_overlap(left_value, right_value):
                return False
        elif canonical_json(left_value) != canonical_json(right_value):
            return False
    return True


def _triggers_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    if not left or not right:
        return True
    return bool(set(left) & set(right))


def _trigger_score(triggers: Sequence[str], input_text: str) -> int | None:
    if not triggers:
        return 0
    haystack = unicodedata.normalize("NFC", input_text).casefold()
    scores: list[int] = []
    for trigger in triggers:
        pieces = [re.escape(piece) for piece in trigger.split()]
        expression = r"(?<!\w)" + r"\s+".join(pieces) + r"(?!\w)"
        if re.search(expression, haystack, flags=re.UNICODE):
            scores.append(len(trigger))
    return max(scores) if scores else None


def _scope_specificity(value: Any) -> int:
    if isinstance(value, dict):
        return sum(1 + _scope_specificity(item) for item in value.values())
    if isinstance(value, list):
        return sum(_scope_specificity(item) for item in value)
    return 1


def _contains_volatile_split_scope_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            compact_key = re.sub(r"[^a-z0-9]", "", key.casefold())
            if compact_key in _VOLATILE_SPLIT_SCOPE_KEYS_COMPACT:
                return True
            if _contains_volatile_split_scope_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_volatile_split_scope_key(item) for item in value)
    return False


def default_store_path() -> Path:
    configured = os.environ.get("NERD_MEMORY_DB")
    if configured and configured.strip():
        return Path(configured).expanduser()
    codex_home = os.environ.get("CODEX_HOME")
    root = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return root / "nerd-memory" / "memory.sqlite3"


class MemoryStore:
    """SQLite-backed evidence, pattern, proposal, and grant state."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        grant_ttl_seconds: int = DEFAULT_GRANT_TTL_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(grant_ttl_seconds, int) or not 1 <= grant_ttl_seconds <= 3600:
            raise MemoryInputError("grant_ttl_seconds must be between 1 and 3600")
        self.grant_ttl_seconds = grant_ttl_seconds
        self._clock = clock or time.time
        self._lock = threading.RLock()
        self._closed = False
        raw_path = os.fspath(path)
        self.path: Path | str
        if raw_path == ":memory:":
            self.path = raw_path
        else:
            db_path = Path(raw_path).expanduser()
            self._prepare_store_file(db_path)
            self.path = db_path
        self._connection = sqlite3.connect(
            os.fspath(self.path),
            timeout=10.0,
            isolation_level=None,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.create_function(
            "nerd_memory_runtime_version",
            0,
            lambda: SCHEMA_VERSION,
            deterministic=True,
        )
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 10000")
        self._connection.execute("PRAGMA journal_mode = DELETE")
        self._connection.execute("PRAGMA synchronous = FULL")
        self._connection.execute("PRAGMA secure_delete = ON")
        try:
            self._initialise_schema()
        except BaseException:
            if self._connection.in_transaction:
                self._connection.rollback()
            self._connection.close()
            raise
        self._enforce_store_mode()

    @staticmethod
    def _prepare_store_file(path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise MemoryInputError("memory database must not be a symbolic link")
        if not path.parent.exists():
            path.parent.mkdir(parents=True, mode=0o700)
            try:
                path.parent.chmod(0o700)
            except OSError as error:
                raise MemoryInputError("cannot secure memory database directory") from error
        if not path.parent.is_dir():
            raise MemoryInputError("memory database parent is not a directory")
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags, 0o600)
            os.close(descriptor)
            path.chmod(0o600)
        except OSError as error:
            raise MemoryInputError("cannot create a private memory database") from error

    def _enforce_store_mode(self) -> None:
        if isinstance(self.path, Path):
            try:
                self.path.chmod(0o600)
            except OSError as error:
                raise MemoryInputError("cannot secure memory database permissions") from error

    def _initialise_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS consents (
            namespace TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
            consent_ref TEXT NOT NULL,
            enabled_at TEXT,
            disabled_at TEXT,
            revision INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS consent_events (
            event_id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
            consent_ref TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS observations (
            observation_id TEXT PRIMARY KEY,
            observation_hash TEXT NOT NULL UNIQUE,
            namespace TEXT NOT NULL,
            episode_id TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            pattern_key TEXT NOT NULL,
            value_json TEXT NOT NULL,
            value_hash TEXT NOT NULL,
            scope_json TEXT NOT NULL,
            triggers_json TEXT NOT NULL,
            operation TEXT NOT NULL,
            source TEXT NOT NULL,
            eligible INTEGER NOT NULL CHECK (eligible IN (0, 1)),
            evidence_ref TEXT NOT NULL,
            observed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS patterns (
            pattern_id TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL UNIQUE,
            namespace TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            pattern_key TEXT NOT NULL,
            value_json TEXT NOT NULL,
            value_hash TEXT NOT NULL,
            scope_json TEXT NOT NULL,
            triggers_json TEXT NOT NULL,
            operation TEXT NOT NULL,
            status TEXT NOT NULL,
            support_episodes INTEGER NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            promoted_at TEXT,
            activation_reason TEXT NOT NULL DEFAULT 'consolidated',
            parent_pattern_id TEXT,
            split_id TEXT
        );

        CREATE TABLE IF NOT EXISTS pattern_evidence (
            pattern_id TEXT NOT NULL REFERENCES patterns(pattern_id) ON DELETE CASCADE,
            observation_id TEXT NOT NULL REFERENCES observations(observation_id) ON DELETE CASCADE,
            PRIMARY KEY (pattern_id, observation_id)
        );

        CREATE TABLE IF NOT EXISTS forgotten_patterns (
            fingerprint TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            pattern_id TEXT NOT NULL,
            forgotten_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS proposals (
            proposal_id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            episode_id TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            context_hash TEXT NOT NULL,
            baseline_hash TEXT NOT NULL,
            baseline_source TEXT,
            baseline_ref TEXT,
            baseline_collisions_json TEXT NOT NULL DEFAULT '[]',
            consent_revision INTEGER NOT NULL,
            endpoint_json TEXT NOT NULL,
            diff_json TEXT NOT NULL,
            pattern_bindings_json TEXT NOT NULL,
            memory_influenced INTEGER NOT NULL CHECK (memory_influenced IN (0, 1)),
            status TEXT NOT NULL,
            proposal_hash TEXT NOT NULL,
            confirmation_phrase TEXT,
            expires_at REAL NOT NULL,
            grant_digest TEXT,
            grant_expires_at REAL,
            created_at TEXT NOT NULL,
            confirmed_at TEXT,
            confirmation_source TEXT,
            confirmation_ref TEXT,
            consumed_at TEXT,
            invalid_reason TEXT
        );

        CREATE TABLE IF NOT EXISTS confirmation_events (
            namespace TEXT NOT NULL,
            confirmation_ref TEXT NOT NULL,
            proposal_id TEXT NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (namespace, confirmation_ref)
        );

        CREATE TABLE IF NOT EXISTS confirmation_ref_tombstones (
            ref_digest TEXT PRIMARY KEY,
            used_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS denials (
            denial_id TEXT PRIMARY KEY,
            proposal_id TEXT NOT NULL UNIQUE,
            proposal_hash TEXT NOT NULL,
            namespace TEXT NOT NULL,
            episode_id TEXT NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL,
            denial_ref TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at REAL NOT NULL,
            resolution TEXT,
            resolution_source TEXT,
            resolution_ref TEXT,
            resolved_at TEXT,
            invalid_reason TEXT
        );

        CREATE TABLE IF NOT EXISTS split_proposals (
            split_id TEXT PRIMARY KEY,
            denial_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            episode_id TEXT NOT NULL,
            proposal_id TEXT NOT NULL,
            proposal_hash TEXT NOT NULL,
            consent_revision INTEGER NOT NULL,
            input_hash TEXT NOT NULL,
            context_hash TEXT NOT NULL,
            specs_json TEXT NOT NULL,
            parent_bindings_json TEXT NOT NULL,
            unselected_bindings_json TEXT NOT NULL,
            status TEXT NOT NULL,
            split_hash TEXT NOT NULL,
            confirmation_phrase TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at REAL NOT NULL,
            confirmed_at TEXT,
            confirmation_source TEXT,
            confirmation_ref TEXT,
            invalid_reason TEXT
        );

        CREATE TABLE IF NOT EXISTS split_parent_bindings (
            split_id TEXT NOT NULL,
            parent_pattern_id TEXT NOT NULL,
            parent_revision INTEGER NOT NULL,
            parent_hash TEXT NOT NULL,
            PRIMARY KEY (split_id, parent_pattern_id)
        );

        CREATE TABLE IF NOT EXISTS proposal_patterns (
            proposal_id TEXT NOT NULL REFERENCES proposals(proposal_id) ON DELETE CASCADE,
            pattern_id TEXT NOT NULL REFERENCES patterns(pattern_id) ON DELETE CASCADE,
            pattern_revision INTEGER NOT NULL,
            pattern_hash TEXT NOT NULL,
            PRIMARY KEY (proposal_id, pattern_id)
        );

        CREATE INDEX IF NOT EXISTS observations_namespace_idx
            ON observations(namespace, eligible, pattern_type, pattern_key);
        CREATE INDEX IF NOT EXISTS patterns_lookup_idx
            ON patterns(namespace, status, pattern_type);
        CREATE INDEX IF NOT EXISTS proposals_episode_idx
            ON proposals(namespace, episode_id, status);
        CREATE INDEX IF NOT EXISTS denials_namespace_idx
            ON denials(namespace, status, created_at);
        CREATE INDEX IF NOT EXISTS split_proposals_denial_idx
            ON split_proposals(denial_id, status, created_at);
        CREATE INDEX IF NOT EXISTS split_parent_pattern_idx
            ON split_parent_bindings(parent_pattern_id, split_id);
        """
        with self._lock:
            self._connection.executescript("BEGIN EXCLUSIVE;\n" + schema)
            self._drop_version_fences(self._connection)
            current = self._connection.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
            previous_version = int(current["value"]) if current is not None else 0
            if previous_version > SCHEMA_VERSION:
                raise MemoryInvariantError("memory database schema is newer than this engine")
            proposal_columns = {
                row["name"]
                for row in self._connection.execute(
                    "PRAGMA table_info(proposals)"
                ).fetchall()
            }
            migrated = previous_version < SCHEMA_VERSION
            if "confirmation_source" not in proposal_columns:
                self._connection.execute(
                    "ALTER TABLE proposals ADD COLUMN confirmation_source TEXT"
                )
                migrated = True
            if "confirmation_ref" not in proposal_columns:
                self._connection.execute(
                    "ALTER TABLE proposals ADD COLUMN confirmation_ref TEXT"
                )
                migrated = True
            if "baseline_source" not in proposal_columns:
                self._connection.execute(
                    "ALTER TABLE proposals ADD COLUMN baseline_source TEXT"
                )
                migrated = True
            if "baseline_ref" not in proposal_columns:
                self._connection.execute(
                    "ALTER TABLE proposals ADD COLUMN baseline_ref TEXT"
                )
                migrated = True
            if "baseline_collisions_json" not in proposal_columns:
                self._connection.execute(
                    "ALTER TABLE proposals ADD COLUMN baseline_collisions_json "
                    "TEXT NOT NULL DEFAULT '[]'"
                )
                migrated = True
            pattern_columns = {
                row["name"]
                for row in self._connection.execute(
                    "PRAGMA table_info(patterns)"
                ).fetchall()
            }
            if "activation_reason" not in pattern_columns:
                self._connection.execute(
                    "ALTER TABLE patterns ADD COLUMN activation_reason TEXT "
                    "NOT NULL DEFAULT 'consolidated'"
                )
                migrated = True
            if "parent_pattern_id" not in pattern_columns:
                self._connection.execute(
                    "ALTER TABLE patterns ADD COLUMN parent_pattern_id TEXT"
                )
                migrated = True
            if "split_id" not in pattern_columns:
                self._connection.execute(
                    "ALTER TABLE patterns ADD COLUMN split_id TEXT"
                )
                migrated = True
            if previous_version < 5:
                for observation in self._connection.execute(
                    "SELECT observation_id, value_json, operation "
                    "FROM observations WHERE pattern_type = 'routing'"
                ).fetchall():
                    try:
                        _decode_stored_pattern_value(
                            "routing",
                            observation["value_json"],
                            observation["operation"],
                        )
                    except (MemoryEngineError, ValueError, TypeError, json.JSONDecodeError):
                        self._connection.execute(
                            "UPDATE observations SET eligible = 0 "
                            "WHERE observation_id = ?",
                            (observation["observation_id"],),
                        )
                migration_time = _utc_now(self._clock())
                for pattern in self._connection.execute(
                    "SELECT pattern_id, value_json, operation "
                    "FROM patterns WHERE pattern_type = 'routing'"
                ).fetchall():
                    try:
                        _decode_stored_pattern_value(
                            "routing",
                            pattern["value_json"],
                            pattern["operation"],
                        )
                    except (MemoryEngineError, ValueError, TypeError, json.JSONDecodeError):
                        self._connection.execute(
                            """
                            UPDATE patterns
                            SET status = 'contested', revision = revision + 1,
                                updated_at = ?
                            WHERE pattern_id = ?
                            """,
                            (migration_time, pattern["pattern_id"]),
                        )
            if migrated:
                self._connection.execute(
                    """
                    UPDATE proposals
                    SET status = 'invalidated', grant_digest = NULL,
                        grant_expires_at = NULL,
                        invalid_reason = 'schema_migrated'
                    WHERE status IN (
                        'pending_confirmation', 'confirmed',
                        'memory_free', 'memory_conflict'
                    )
                    """
                )
                self._connection.execute(
                    """
                    UPDATE split_proposals
                    SET status = 'invalidated', invalid_reason = 'schema_migrated'
                    WHERE status = 'pending_confirmation'
                    """
                )
                self._connection.execute(
                    """
                    UPDATE denials
                    SET status = 'invalidated', invalid_reason = 'schema_migrated'
                    WHERE status IN ('needs_diagnosis', 'split_pending')
                    """
                )
            existing_confirmations = self._connection.execute(
                """
                SELECT confirmation_ref, created_at FROM confirmation_events
                ORDER BY created_at
                """
            ).fetchall()
            self._connection.executemany(
                """
                INSERT OR IGNORE INTO confirmation_ref_tombstones(ref_digest, used_at)
                VALUES (?, ?)
                """,
                (
                    (
                        _confirmation_ref_digest(row["confirmation_ref"]),
                        row["created_at"],
                    )
                    for row in existing_confirmations
                ),
            )
            self._connection.execute(
                "INSERT INTO metadata(key, value) VALUES('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(SCHEMA_VERSION),),
            )
            self._install_version_fences(self._connection)
            self._connection.commit()

    @staticmethod
    def _version_fence_name(table: str, operation: str) -> str:
        return f"nerd_memory_version_fence_{table}_{operation.casefold()}"

    @classmethod
    def _drop_version_fences(cls, connection: sqlite3.Connection) -> None:
        for table in _VERSION_FENCED_TABLES:
            for operation in ("INSERT", "UPDATE", "DELETE"):
                connection.execute(
                    f"DROP TRIGGER IF EXISTS {cls._version_fence_name(table, operation)}"
                )

    @classmethod
    def _install_version_fences(cls, connection: sqlite3.Connection) -> None:
        for table in _VERSION_FENCED_TABLES:
            for operation in ("INSERT", "UPDATE", "DELETE"):
                trigger_name = cls._version_fence_name(table, operation)
                connection.execute(
                    f"""
                    CREATE TRIGGER {trigger_name}
                    BEFORE {operation} ON {table}
                    WHEN nerd_memory_runtime_version() != COALESCE(
                        (
                            SELECT CAST(value AS INTEGER)
                            FROM metadata WHERE key = 'schema_version'
                        ),
                        -1
                    )
                    BEGIN
                        SELECT RAISE(
                            ABORT,
                            'nerd-memory runtime schema version mismatch'
                        );
                    END
                    """
                )

    @staticmethod
    def _require_current_schema(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None or int(row["value"]) != SCHEMA_VERSION:
            raise MemoryInvariantError(
                "memory runtime schema version changed; restart this runtime"
            )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        self._ensure_open()
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._require_current_schema(self._connection)
                yield self._connection
            except BaseException:
                self._connection.rollback()
                raise
            else:
                self._connection.commit()
                self._enforce_store_mode()

    def _ensure_open(self) -> None:
        if self._closed:
            raise MemoryInvariantError("memory store is closed")

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True
                self._enforce_store_mode()

    def __enter__(self) -> "MemoryStore":
        self._ensure_open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _require_enabled(self, namespace: str, connection: sqlite3.Connection) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM consents WHERE namespace = ?", (namespace,)
        ).fetchone()
        if row is None or not bool(row["enabled"]):
            raise MemoryConsentError("explicit memory consent is not enabled for this namespace")
        return row

    @staticmethod
    def _claim_trusted_event_ref(
        connection: sqlite3.Connection,
        event_ref: str,
        used_at: str,
    ) -> None:
        ref_digest = _confirmation_ref_digest(event_ref)
        used = connection.execute(
            "SELECT ref_digest FROM confirmation_ref_tombstones WHERE ref_digest = ?",
            (ref_digest,),
        ).fetchone()
        if used is not None:
            raise MemoryInvariantError(
                "trusted event was already used in this memory store"
            )
        connection.execute(
            "INSERT INTO confirmation_ref_tombstones(ref_digest, used_at) VALUES (?, ?)",
            (ref_digest, used_at),
        )

    @staticmethod
    def _invalidate_namespace_routing_state(
        connection: sqlite3.Connection,
        namespace: str,
        reason: str,
        *,
        except_split_id: str | None = None,
    ) -> None:
        split_filter = ""
        parameters: tuple[Any, ...] = (namespace,)
        if except_split_id is not None:
            split_filter = " AND split_id != ?"
            parameters = (namespace, except_split_id)
        pending = connection.execute(
            """
            SELECT denial_id FROM split_proposals
            WHERE namespace = ? AND status = 'pending_confirmation'
            """
            + split_filter,
            parameters,
        ).fetchall()
        for row in pending:
            connection.execute(
                """
                UPDATE denials
                SET status = 'needs_diagnosis', invalid_reason = ?
                WHERE denial_id = ? AND status = 'split_pending'
                """,
                (reason, row["denial_id"]),
            )
        connection.execute(
            """
            UPDATE split_proposals
            SET status = 'invalidated', invalid_reason = ?
            WHERE namespace = ? AND status = 'pending_confirmation'
            """
            + split_filter,
            (reason, *parameters),
        )
        connection.execute(
            """
            UPDATE proposals
            SET status = 'invalidated', grant_digest = NULL,
                grant_expires_at = NULL, invalid_reason = ?
            WHERE namespace = ? AND status IN (
                'pending_confirmation', 'confirmed',
                'memory_free', 'memory_conflict'
            )
            """,
            (reason, namespace),
        )

    def enable(self, namespace: str, *, consent_ref: str) -> dict[str, Any]:
        namespace = _require_text("namespace", namespace, max_length=512)
        consent_ref = _require_text("consent_ref", consent_ref, max_length=2048)
        _reject_sensitive(consent_ref)
        now = _utc_now(self._clock())
        event_id = "evt_" + uuid.uuid4().hex
        with self._transaction() as connection:
            connection.execute(
                """
                INSERT INTO consents(
                    namespace, enabled, consent_ref, enabled_at, disabled_at, revision
                ) VALUES (?, 1, ?, ?, NULL, 1)
                ON CONFLICT(namespace) DO UPDATE SET
                    enabled = 1,
                    consent_ref = excluded.consent_ref,
                    enabled_at = excluded.enabled_at,
                    disabled_at = NULL,
                    revision = consents.revision + 1
                """,
                (namespace, consent_ref, now),
            )
            connection.execute(
                "INSERT INTO consent_events VALUES (?, ?, 1, ?, ?)",
                (event_id, namespace, consent_ref, now),
            )
            connection.execute(
                """
                UPDATE proposals
                SET status = 'invalidated', grant_digest = NULL,
                    grant_expires_at = NULL, invalid_reason = 'consent_revision_changed'
                WHERE namespace = ? AND status IN (
                    'pending_confirmation', 'confirmed',
                    'memory_free', 'memory_conflict'
                )
                """,
                (namespace,),
            )
            connection.execute(
                """
                UPDATE split_proposals
                SET status = 'invalidated', invalid_reason = 'consent_revision_changed'
                WHERE namespace = ? AND status = 'pending_confirmation'
                """,
                (namespace,),
            )
            connection.execute(
                """
                UPDATE denials
                SET status = 'invalidated', invalid_reason = 'consent_revision_changed'
                WHERE namespace = ? AND status IN ('needs_diagnosis', 'split_pending')
                """,
                (namespace,),
            )
            row = connection.execute(
                "SELECT * FROM consents WHERE namespace = ?", (namespace,)
            ).fetchone()
        assert row is not None
        return {
            "namespace": namespace,
            "enabled": True,
            "consent_ref": row["consent_ref"],
            "enabled_at": row["enabled_at"],
            "revision": row["revision"],
        }

    def disable(self, namespace: str, *, consent_ref: str) -> dict[str, Any]:
        namespace = _require_text("namespace", namespace, max_length=512)
        consent_ref = _require_text("consent_ref", consent_ref, max_length=2048)
        _reject_sensitive(consent_ref)
        now = _utc_now(self._clock())
        event_id = "evt_" + uuid.uuid4().hex
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM consents WHERE namespace = ?", (namespace,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory namespace was not found")
            connection.execute(
                """
                UPDATE consents
                SET enabled = 0, consent_ref = ?, disabled_at = ?, revision = revision + 1
                WHERE namespace = ?
                """,
                (consent_ref, now, namespace),
            )
            connection.execute(
                "INSERT INTO consent_events VALUES (?, ?, 0, ?, ?)",
                (event_id, namespace, consent_ref, now),
            )
            connection.execute(
                """
                UPDATE proposals
                SET status = 'invalidated', grant_digest = NULL,
                    grant_expires_at = NULL, invalid_reason = 'consent_disabled'
                WHERE namespace = ? AND status IN (
                    'pending_confirmation', 'confirmed',
                    'memory_free', 'memory_conflict'
                )
                """,
                (namespace,),
            )
            connection.execute(
                """
                UPDATE split_proposals
                SET status = 'invalidated', invalid_reason = 'consent_disabled'
                WHERE namespace = ? AND status = 'pending_confirmation'
                """,
                (namespace,),
            )
            connection.execute(
                """
                UPDATE denials
                SET status = 'invalidated', invalid_reason = 'consent_disabled'
                WHERE namespace = ? AND status IN ('needs_diagnosis', 'split_pending')
                """,
                (namespace,),
            )
        return {
            "namespace": namespace,
            "enabled": False,
            "consent_ref": consent_ref,
            "disabled_at": now,
        }

    def consent_status(self, namespace: str) -> dict[str, Any]:
        namespace = _require_text("namespace", namespace, max_length=512)
        self._ensure_open()
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM consents WHERE namespace = ?", (namespace,)
            ).fetchone()
        if row is None:
            return {"namespace": namespace, "enabled": False, "configured": False}
        return {
            "namespace": namespace,
            "enabled": bool(row["enabled"]),
            "configured": True,
            "consent_ref": row["consent_ref"],
            "enabled_at": row["enabled_at"],
            "disabled_at": row["disabled_at"],
            "revision": row["revision"],
        }

    # Short alias for callers and the CLI protocol.
    status = consent_status

    def observe(
        self,
        *,
        namespace: str,
        episode_id: str,
        pattern_type: str,
        pattern_key: str,
        value: Any,
        scope: Mapping[str, Any] | None = None,
        triggers: Sequence[str] | None = None,
        operation: str = "fill",
        source: str,
        evidence_ref: str,
    ) -> dict[str, Any]:
        namespace = _require_text("namespace", namespace, max_length=512)
        episode_id = _require_text("episode_id", episode_id, max_length=1024)
        pattern_type = _require_text("pattern_type", pattern_type, max_length=64).casefold()
        if pattern_type not in PATTERN_TYPES:
            raise MemoryInputError(f"pattern_type must be one of: {', '.join(PATTERN_TYPES)}")
        pattern_key = _require_text("pattern_key", pattern_key, max_length=512)
        operation = _require_text("operation", operation, max_length=32).casefold()
        if operation not in OPERATIONS:
            raise MemoryInputError(f"operation must be one of: {', '.join(sorted(OPERATIONS))}")
        source = _require_text("source", source, max_length=64).casefold()
        if source not in OBSERVATION_SOURCES:
            raise MemoryInputError("source is not eligible for memory ingestion")
        evidence_ref = _require_text("evidence_ref", evidence_ref, max_length=2048)
        scope_value = _normalise_scope(scope)
        trigger_values = _normalise_triggers(triggers)
        value = _validate_pattern_value(pattern_type, value, operation)
        _reject_sensitive(pattern_key, value, scope_value, trigger_values, evidence_ref)

        eligible = source in ELIGIBLE_SOURCES
        observed_at = _utc_now(self._clock())
        value_hash = canonical_hash(value)
        identity = {
            "namespace": namespace,
            "episode_id": episode_id,
            "pattern_type": pattern_type,
            "pattern_key": pattern_key,
            "value": value,
            "scope": scope_value,
            "triggers": trigger_values,
            "operation": operation,
            "source": source,
            "evidence_ref": evidence_ref,
        }
        observation_hash = canonical_hash(identity)
        observation_id = "obs_" + observation_hash[:32]
        observation_fingerprint = self._pattern_fingerprint(
            namespace,
            pattern_type,
            pattern_key,
            value,
            scope_value,
            trigger_values,
            operation,
        )
        with self._transaction() as connection:
            self._require_enabled(namespace, connection)
            if connection.execute(
                "SELECT fingerprint FROM forgotten_patterns WHERE fingerprint = ?",
                (observation_fingerprint,),
            ).fetchone() is not None:
                raise MemoryInvariantError(
                    "this exact memory pattern was forgotten and cannot be re-observed"
                )
            connection.execute(
                """
                INSERT OR IGNORE INTO observations(
                    observation_id, observation_hash, namespace, episode_id,
                    pattern_type, pattern_key, value_json, value_hash, scope_json,
                    triggers_json, operation, source, eligible, evidence_ref, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    observation_hash,
                    namespace,
                    episode_id,
                    pattern_type,
                    pattern_key,
                    canonical_json(value),
                    value_hash,
                    canonical_json(scope_value),
                    canonical_json(trigger_values),
                    operation,
                    source,
                    int(eligible),
                    evidence_ref,
                    observed_at,
                ),
            )
            row = connection.execute(
                "SELECT * FROM observations WHERE observation_hash = ?",
                (observation_hash,),
            ).fetchone()
            # A correction is explicit counter-evidence, so it suspends conflicting
            # active guidance immediately; callers need not race a later consolidation.
            if source == "user_correction":
                active_patterns = connection.execute(
                    """
                    SELECT * FROM patterns
                    WHERE namespace = ? AND pattern_type = ? AND pattern_key = ?
                      AND status IN ('candidate', 'confirmed')
                    """,
                    (namespace, pattern_type, pattern_key),
                ).fetchall()
                for pattern in active_patterns:
                    if pattern["fingerprint"] == observation_fingerprint:
                        continue
                    if not _scopes_overlap(
                        _decode_json(pattern["scope_json"]), scope_value
                    ):
                        continue
                    if not _triggers_overlap(
                        _decode_json(pattern["triggers_json"]), trigger_values
                    ):
                        continue
                    connection.execute(
                        """
                        UPDATE patterns
                        SET status = 'contested', revision = revision + 1,
                            updated_at = ?
                        WHERE pattern_id = ?
                        """,
                        (observed_at, pattern["pattern_id"]),
                    )
                    self._invalidate_pattern_proposals(
                        connection, pattern["pattern_id"], "pattern_corrected"
                    )
        assert row is not None
        return self._observation_dict(row)

    @staticmethod
    def _observation_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "observation_id": row["observation_id"],
            "namespace": row["namespace"],
            "episode_id": row["episode_id"],
            "pattern_type": row["pattern_type"],
            "pattern_key": row["pattern_key"],
            "value": _decode_json(row["value_json"]),
            "scope": _decode_json(row["scope_json"]),
            "triggers": _decode_json(row["triggers_json"]),
            "operation": row["operation"],
            "source": row["source"],
            "eligible": bool(row["eligible"]),
            "evidence_ref": row["evidence_ref"],
            "observed_at": row["observed_at"],
        }

    @staticmethod
    def _pattern_fingerprint(
        namespace: str,
        pattern_type: str,
        pattern_key: str,
        value: Any,
        scope: Any,
        triggers: Any,
        operation: str,
    ) -> str:
        return canonical_hash(
            {
                "namespace": namespace,
                "pattern_type": pattern_type,
                "pattern_key": pattern_key,
                "value": value,
                "scope": scope,
                "triggers": triggers,
                "operation": operation,
            }
        )

    @staticmethod
    def _pattern_material_hash(row: sqlite3.Row | Mapping[str, Any]) -> str:
        def get(name: str) -> Any:
            return row[name]

        value = _decode_json(get("value_json")) if isinstance(get("value_json"), str) else get("value_json")
        scope = _decode_json(get("scope_json")) if isinstance(get("scope_json"), str) else get("scope_json")
        triggers = _decode_json(get("triggers_json")) if isinstance(get("triggers_json"), str) else get("triggers_json")
        return canonical_hash(
            {
                "pattern_id": get("pattern_id"),
                "namespace": get("namespace"),
                "pattern_type": get("pattern_type"),
                "pattern_key": get("pattern_key"),
                "value": value,
                "scope": scope,
                "triggers": triggers,
                "operation": get("operation"),
                "status": get("status"),
                "support_episodes": get("support_episodes"),
                "revision": get("revision"),
                "activation_reason": get("activation_reason"),
                "parent_pattern_id": get("parent_pattern_id"),
                "split_id": get("split_id"),
            }
        )

    @staticmethod
    def _pattern_evidence(
        connection: sqlite3.Connection,
        pattern_id: str,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT observations.observation_id, observations.episode_id,
                   observations.source, observations.evidence_ref,
                   observations.observed_at
            FROM pattern_evidence
            JOIN observations USING(observation_id)
            WHERE pattern_evidence.pattern_id = ?
            ORDER BY observations.observed_at, observations.observation_id
            """,
            (pattern_id,),
        ).fetchall()
        return [
            {
                "observation_id": item["observation_id"],
                "episode_id": item["episode_id"],
                "source": item["source"],
                "evidence_ref": item["evidence_ref"],
                "observed_at": item["observed_at"],
            }
            for item in rows
        ]

    @staticmethod
    def _pattern_contradictions(
        connection: sqlite3.Connection,
        pattern: sqlite3.Row,
    ) -> list[dict[str, Any]]:
        pattern_scope = _decode_json(pattern["scope_json"])
        pattern_triggers = _decode_json(pattern["triggers_json"])
        rows = connection.execute(
            """
            SELECT * FROM observations
            WHERE namespace = ? AND pattern_type = ? AND pattern_key = ?
              AND eligible = 1
            ORDER BY observed_at, observation_id
            """,
            (
                pattern["namespace"],
                pattern["pattern_type"],
                pattern["pattern_key"],
            ),
        ).fetchall()
        contradictions: list[dict[str, Any]] = []
        for item in rows:
            if (
                item["value_hash"] == pattern["value_hash"]
                and item["scope_json"] == pattern["scope_json"]
                and item["triggers_json"] == pattern["triggers_json"]
                and item["operation"] == pattern["operation"]
            ):
                continue
            item_scope = _decode_json(item["scope_json"])
            item_triggers = _decode_json(item["triggers_json"])
            if not _scopes_overlap(pattern_scope, item_scope):
                continue
            if not _triggers_overlap(pattern_triggers, item_triggers):
                continue
            contradictions.append(
                {
                    "observation_id": item["observation_id"],
                    "episode_id": item["episode_id"],
                    "source": item["source"],
                    "evidence_ref": item["evidence_ref"],
                    "value": _decode_json(item["value_json"]),
                    "scope": item_scope,
                    "triggers": item_triggers,
                    "operation": item["operation"],
                    "observed_at": item["observed_at"],
                }
            )
        return contradictions

    @classmethod
    def _pattern_dict(
        cls,
        row: sqlite3.Row,
        connection: sqlite3.Connection,
    ) -> dict[str, Any]:
        evidence = cls._pattern_evidence(connection, row["pattern_id"])
        contradictions = cls._pattern_contradictions(connection, row)
        return {
            "pattern_id": row["pattern_id"],
            "namespace": row["namespace"],
            "pattern_type": row["pattern_type"],
            "pattern_key": row["pattern_key"],
            "value": _decode_json(row["value_json"]),
            "scope": _decode_json(row["scope_json"]),
            "triggers": _decode_json(row["triggers_json"]),
            "operation": row["operation"],
            "status": row["status"],
            "support_episodes": row["support_episodes"],
            "revision": row["revision"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "promoted_at": row["promoted_at"],
            "activation_reason": row["activation_reason"],
            "parent_pattern_id": row["parent_pattern_id"],
            "split_id": row["split_id"],
            "support_episode_ids": sorted(
                {item["episode_id"] for item in evidence}
            ),
            "evidence": evidence,
            "contradictions": contradictions,
        }

    def _invalidate_pattern_proposals(
        self,
        connection: sqlite3.Connection,
        pattern_id: str,
        reason: str,
    ) -> None:
        connection.execute(
            """
            UPDATE proposals
            SET status = 'invalidated', grant_digest = NULL,
                grant_expires_at = NULL, invalid_reason = ?
            WHERE proposal_id IN (
                SELECT proposal_id FROM proposal_patterns WHERE pattern_id = ?
            ) AND status IN (
                'pending_confirmation', 'confirmed', 'memory_conflict'
            )
            """,
            (reason, pattern_id),
        )
        connection.execute(
            """
            UPDATE denials
            SET status = 'needs_diagnosis', invalid_reason = ?
            WHERE status = 'split_pending' AND denial_id IN (
                SELECT denial_id FROM split_proposals
                WHERE status = 'pending_confirmation' AND split_id IN (
                    SELECT split_id FROM split_parent_bindings
                    WHERE parent_pattern_id = ?
                )
            )
            """,
            (reason, pattern_id),
        )
        connection.execute(
            """
            UPDATE split_proposals
            SET status = 'invalidated', invalid_reason = ?
            WHERE status = 'pending_confirmation' AND split_id IN (
                SELECT split_id FROM split_parent_bindings
                WHERE parent_pattern_id = ?
            )
            """,
            (reason, pattern_id),
        )

    def consolidate(
        self,
        namespace: str,
        *,
        min_episodes: int = DEFAULT_MIN_EPISODES,
    ) -> list[dict[str, Any]]:
        namespace = _require_text("namespace", namespace, max_length=512)
        if not isinstance(min_episodes, int) or min_episodes < 1:
            raise MemoryInputError("min_episodes must be a positive integer")
        now = _utc_now(self._clock())
        with self._transaction() as connection:
            self._require_enabled(namespace, connection)
            observations = connection.execute(
                """
                SELECT * FROM observations
                WHERE namespace = ? AND eligible = 1
                ORDER BY observed_at, observation_id
                """,
                (namespace,),
            ).fetchall()
            forgotten_fingerprints = {
                row["fingerprint"]
                for row in connection.execute(
                    "SELECT fingerprint FROM forgotten_patterns WHERE namespace = ?",
                    (namespace,),
                ).fetchall()
            }

            groups: dict[str, dict[str, Any]] = {}
            for row in observations:
                try:
                    value = _decode_stored_pattern_value(
                        row["pattern_type"],
                        row["value_json"],
                        row["operation"],
                    )
                except (MemoryEngineError, ValueError, TypeError, json.JSONDecodeError):
                    connection.execute(
                        "UPDATE observations SET eligible = 0 WHERE observation_id = ?",
                        (row["observation_id"],),
                    )
                    continue
                scope = _decode_json(row["scope_json"])
                triggers = _decode_json(row["triggers_json"])
                fingerprint = self._pattern_fingerprint(
                    namespace,
                    row["pattern_type"],
                    row["pattern_key"],
                    value,
                    scope,
                    triggers,
                    row["operation"],
                )
                if fingerprint in forgotten_fingerprints:
                    continue
                group = groups.setdefault(
                    fingerprint,
                    {
                        "fingerprint": fingerprint,
                        "namespace": namespace,
                        "pattern_type": row["pattern_type"],
                        "pattern_key": row["pattern_key"],
                        "value": value,
                        "value_hash": row["value_hash"],
                        "scope": scope,
                        "triggers": triggers,
                        "operation": row["operation"],
                        "episodes": set(),
                        "observation_ids": [],
                        "sources": set(),
                    },
                )
                group["episodes"].add(row["episode_id"])
                group["observation_ids"].append(row["observation_id"])
                group["sources"].add(row["source"])

            touched_ids: list[str] = []
            for group in groups.values():
                support = len(group["episodes"])
                if support < min_episodes:
                    continue
                pattern_id = "pat_" + group["fingerprint"][:32]
                existing = connection.execute(
                    "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
                ).fetchone()
                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO patterns(
                            pattern_id, fingerprint, namespace, pattern_type,
                            pattern_key, value_json, value_hash, scope_json,
                            triggers_json, operation, status, support_episodes,
                            revision, created_at, updated_at, promoted_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate', ?, 1, ?, ?, NULL)
                        """,
                        (
                            pattern_id,
                            group["fingerprint"],
                            namespace,
                            group["pattern_type"],
                            group["pattern_key"],
                            canonical_json(group["value"]),
                            group["value_hash"],
                            canonical_json(group["scope"]),
                            canonical_json(group["triggers"]),
                            group["operation"],
                            support,
                            now,
                            now,
                        ),
                    )
                elif existing["support_episodes"] != support:
                    connection.execute(
                        """
                        UPDATE patterns
                        SET support_episodes = ?, revision = revision + 1, updated_at = ?
                        WHERE pattern_id = ?
                        """,
                        (support, now, pattern_id),
                    )
                    self._invalidate_pattern_proposals(
                        connection, pattern_id, "pattern_revision_changed"
                    )
                connection.execute(
                    "DELETE FROM pattern_evidence WHERE pattern_id = ?", (pattern_id,)
                )
                connection.executemany(
                    "INSERT INTO pattern_evidence(pattern_id, observation_id) VALUES (?, ?)",
                    ((pattern_id, item) for item in group["observation_ids"]),
                )
                touched_ids.append(pattern_id)

            active_patterns = connection.execute(
                """
                SELECT * FROM patterns
                WHERE namespace = ? AND status IN ('candidate', 'confirmed')
                """,
                (namespace,),
            ).fetchall()
            for pattern in active_patterns:
                pattern_scope = _decode_json(pattern["scope_json"])
                pattern_triggers = _decode_json(pattern["triggers_json"])
                conflict = False
                for group in groups.values():
                    if group["fingerprint"] == pattern["fingerprint"]:
                        continue
                    if group["pattern_type"] != pattern["pattern_type"]:
                        continue
                    if group["pattern_key"] != pattern["pattern_key"]:
                        continue
                    if not _scopes_overlap(pattern_scope, group["scope"]):
                        continue
                    if not _triggers_overlap(pattern_triggers, group["triggers"]):
                        continue
                    independent_support = len(group["episodes"])
                    correction = "user_correction" in group["sources"]
                    if correction or independent_support >= min_episodes:
                        conflict = True
                        break
                if conflict:
                    connection.execute(
                        """
                        UPDATE patterns
                        SET status = 'contested', revision = revision + 1, updated_at = ?
                        WHERE pattern_id = ?
                        """,
                        (now, pattern["pattern_id"]),
                    )
                    self._invalidate_pattern_proposals(
                        connection, pattern["pattern_id"], "pattern_contested"
                    )

            if not touched_ids:
                return []
            placeholders = ",".join("?" for _ in touched_ids)
            rows = connection.execute(
                f"""
                SELECT * FROM patterns WHERE pattern_id IN ({placeholders})
                ORDER BY CASE pattern_type
                    WHEN 'goal' THEN 1 WHEN 'task' THEN 2 WHEN 'action' THEN 3
                    WHEN 'result' THEN 4 WHEN 'boundary' THEN 5
                    WHEN 'verification' THEN 6 WHEN 'routing' THEN 7 ELSE 99 END,
                    pattern_key, pattern_id
                """,
                tuple(touched_ids),
            ).fetchall()
            result = [self._pattern_dict(row, connection) for row in rows]
        return result

    def list_patterns(self, namespace: str) -> list[dict[str, Any]]:
        namespace = _require_text("namespace", namespace, max_length=512)
        self._ensure_open()
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT * FROM patterns WHERE namespace = ?
                ORDER BY CASE pattern_type
                    WHEN 'goal' THEN 1 WHEN 'task' THEN 2 WHEN 'action' THEN 3
                    WHEN 'result' THEN 4 WHEN 'boundary' THEN 5
                    WHEN 'verification' THEN 6 WHEN 'routing' THEN 7 ELSE 99 END,
                    pattern_key, pattern_id
                """,
                (namespace,),
            ).fetchall()
            result = [self._pattern_dict(row, self._connection) for row in rows]
        return result

    def get_pattern(self, pattern_id: str) -> dict[str, Any]:
        pattern_id = _require_text("pattern_id", pattern_id, max_length=128)
        self._ensure_open()
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory pattern was not found")
            result = self._pattern_dict(row, self._connection)
        return result

    @classmethod
    def _promotion_preview_dict(
        cls,
        row: sqlite3.Row,
        connection: sqlite3.Connection,
        consent_revision: int,
    ) -> dict[str, Any]:
        evidence = cls._pattern_evidence(connection, row["pattern_id"])
        topology_rows = connection.execute(
            """
            SELECT * FROM patterns
            WHERE namespace = ? AND pattern_type = ?
              AND status IN ('candidate', 'confirmed')
            ORDER BY pattern_id
            """,
            (row["namespace"], row["pattern_type"]),
        ).fetchall()
        route_context = [
            {
                "pattern_id": item["pattern_id"],
                "status": item["status"],
                "pattern_key": item["pattern_key"],
                "value": _decode_json(item["value_json"]),
                "scope": _decode_json(item["scope_json"]),
                "triggers": _decode_json(item["triggers_json"]),
                "operation": item["operation"],
                "pattern_hash": cls._pattern_material_hash(item),
            }
            for item in topology_rows
        ]
        decision_hash = canonical_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "operation": "promote",
                "namespace": row["namespace"],
                "consent_revision": consent_revision,
                "pattern_id": row["pattern_id"],
                "pattern_hash": cls._pattern_material_hash(row),
                "evidence_hash": canonical_hash(evidence),
                "routing_topology_hash": canonical_hash(route_context),
            }
        )
        return {
            "operation": "promote",
            "namespace": row["namespace"],
            "target": cls._pattern_dict(row, connection),
            "routing_context": route_context,
            "decision_hash": decision_hash,
            "confirmation_phrase": (
                f"confirm promote {row['pattern_id']} {decision_hash[:12]}"
            ),
            "effect": (
                "memory write only; future matching proposals may recommend this pattern "
                "but still require their own confirmation"
            ),
        }

    def preview_promote(self, pattern_id: str) -> dict[str, Any]:
        pattern_id = _require_text("pattern_id", pattern_id, max_length=128)
        self._ensure_open()
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory pattern was not found")
            consent = self._require_enabled(row["namespace"], self._connection)
            if row["status"] != "candidate":
                raise MemoryInvariantError(
                    "only an uncontested candidate can be previewed for promotion"
                )
            _decode_stored_pattern_value(
                row["pattern_type"],
                row["value_json"],
                row["operation"],
            )
            result = self._promotion_preview_dict(
                row,
                self._connection,
                consent["revision"],
            )
        return result

    def promote(
        self,
        pattern_id: str,
        confirmation: str,
        *,
        source: str,
        confirmation_ref: str,
    ) -> dict[str, Any]:
        pattern_id = _require_text("pattern_id", pattern_id, max_length=128)
        if not isinstance(confirmation, str):
            raise MemoryInvariantError("promotion confirmation phrase must match exactly")
        source = _require_text("source", source, max_length=64).casefold()
        if source != "direct_user":
            raise MemoryInvariantError(
                "only a declared direct-user event may promote a memory pattern"
            )
        confirmation_ref = _require_text(
            "confirmation_ref", confirmation_ref, max_length=2048
        )
        _reject_sensitive(confirmation_ref)
        now = _utc_now(self._clock())
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory pattern was not found")
            consent = self._require_enabled(row["namespace"], connection)
            if row["status"] != "candidate":
                raise MemoryInvariantError("only an uncontested candidate can be promoted")
            _decode_stored_pattern_value(
                row["pattern_type"],
                row["value_json"],
                row["operation"],
            )
            preview = self._promotion_preview_dict(
                row,
                connection,
                consent["revision"],
            )
            if not hmac.compare_digest(
                confirmation,
                preview["confirmation_phrase"],
            ):
                raise MemoryInvariantError(
                    "promotion confirmation phrase must match exact current preview"
                )
            self._claim_trusted_event_ref(connection, confirmation_ref, now)
            connection.execute(
                """
                UPDATE patterns
                SET status = 'confirmed', revision = revision + 1,
                    promoted_at = ?, updated_at = ?
                WHERE pattern_id = ?
                """,
                (now, now, pattern_id),
            )
            self._invalidate_namespace_routing_state(
                connection,
                row["namespace"],
                "routing_pattern_promoted",
            )
            row = connection.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
            ).fetchone()
            assert row is not None
            result = self._pattern_dict(row, connection)
            result["memory_write_only"] = True
            result["fresh_proposal_required"] = True
        return result

    @staticmethod
    def _apply_pattern(current: Any, value: Any, operation: str, pattern_type: str) -> Any | None:
        if pattern_type == "routing":
            try:
                validated = _validate_pattern_value(
                    pattern_type,
                    value,
                    operation,
                )
            except MemoryEngineError:
                return None
            if canonical_json(validated) != canonical_json(value):
                return None
            value = validated
        if operation == "fill":
            empty = current is None or (pattern_type in LIST_PATTERN_TYPES and current == [])
            return copy.deepcopy(value) if empty else None
        if pattern_type not in LIST_PATTERN_TYPES or not isinstance(current, list):
            return None
        additions = [
            copy.deepcopy(item)
            for item in value
            if canonical_json(item) not in {canonical_json(existing) for existing in current}
        ]
        if not additions:
            return None
        if operation == "append":
            return copy.deepcopy(current) + additions
        if operation == "prepend":
            return additions + copy.deepcopy(current)
        return None

    @staticmethod
    def _memory_conflicts(bindings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        by_field: dict[str, list[dict[str, Any]]] = {}
        for binding in bindings:
            if binding.get("role") != "conflict_candidate":
                continue
            by_field.setdefault(str(binding["field"]), []).append(
                {
                    "pattern_id": binding["pattern_id"],
                    "revision": binding["revision"],
                    "candidate_effect": binding["candidate_effect"],
                    "support_episodes": binding["support_episodes"],
                    "evidence_sample": binding["evidence_sample"],
                }
            )
        return [
            {
                "field": field,
                "reason": "equally_applicable_patterns_disagree",
                "candidates": sorted(
                    candidates,
                    key=lambda item: (canonical_json(item["candidate_effect"]), item["pattern_id"]),
                ),
            }
            for field, candidates in sorted(by_field.items())
        ]

    @staticmethod
    def _memory_value_overlaps(
        field: str,
        current: Any,
        remembered: Any,
    ) -> bool:
        if canonical_json(current) == canonical_json(remembered):
            return True
        if field == "routing" and isinstance(current, list) and isinstance(remembered, list):
            current_agents = {
                item.get("agent") for item in current if isinstance(item, dict)
            }
            remembered_agents = {
                item.get("agent") for item in remembered if isinstance(item, dict)
            }
            if (current_agents - {None}) & (remembered_agents - {None}):
                return True
            for capability_field in ("skills", "tools", "mcp_servers"):
                current_capabilities = {
                    capability
                    for item in current
                    if isinstance(item, dict)
                    for capability in item.get(capability_field, [])
                    if isinstance(capability, str)
                }
                remembered_capabilities = {
                    capability
                    for item in remembered
                    if isinstance(item, dict)
                    for capability in item.get(capability_field, [])
                    if isinstance(capability, str)
                }
                if current_capabilities & remembered_capabilities:
                    return True
            return False
        if field in LIST_PATTERN_TYPES and isinstance(current, list) and isinstance(remembered, list):
            current_items = {canonical_json(item) for item in current}
            remembered_items = {canonical_json(item) for item in remembered}
            return bool(current_items & remembered_items)
        return False

    @staticmethod
    def _baseline_memory_collisions(
        connection: sqlite3.Connection,
        namespace: str,
        baseline: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        matched: dict[str, set[str]] = {}
        for observation in connection.execute(
            """
            SELECT observation_id, pattern_type, value_json
            FROM observations WHERE namespace = ?
            """,
            (namespace,),
        ).fetchall():
            field = observation["pattern_type"]
            if field not in PATTERN_TYPES:
                continue
            current = baseline.get(field)
            if current is None or current == []:
                continue
            try:
                observed = _decode_json(observation["value_json"])
            except (ValueError, TypeError) as error:
                raise MemoryInvariantError(
                    "persisted observation value is invalid JSON"
                ) from error
            if MemoryStore._memory_value_overlaps(field, current, observed):
                matched.setdefault(field, set()).add(
                    observation["observation_id"]
                )
        for pattern in connection.execute(
            """
            SELECT pattern_id, pattern_type, value_json
            FROM patterns WHERE namespace = ?
            """,
            (namespace,),
        ).fetchall():
            field = pattern["pattern_type"]
            current = baseline.get(field)
            if current is None or current == []:
                continue
            remembered = _decode_json(pattern["value_json"])
            if MemoryStore._memory_value_overlaps(field, current, remembered):
                matched.setdefault(field, set()).add(pattern["pattern_id"])
        for proposal in connection.execute(
            """
            SELECT proposal_id, diff_json FROM proposals
            WHERE namespace = ? AND memory_influenced = 1
            """,
            (namespace,),
        ).fetchall():
            try:
                changes = _decode_json(proposal["diff_json"])
            except (ValueError, TypeError) as error:
                raise MemoryInvariantError(
                    "persisted proposal diff is invalid JSON"
                ) from error
            if not isinstance(changes, list):
                raise MemoryInvariantError("persisted proposal diff is invalid")
            for change in changes:
                if not isinstance(change, dict) or not {
                    "field",
                    "after",
                } <= set(change):
                    raise MemoryInvariantError("persisted proposal diff is invalid")
                field = change["field"]
                if field not in PATTERN_TYPES:
                    continue
                current = baseline.get(field)
                if current is None or current == []:
                    continue
                if MemoryStore._memory_value_overlaps(
                    field,
                    current,
                    change["after"],
                ):
                    matched.setdefault(field, set()).add(proposal["proposal_id"])
        for split in connection.execute(
            """
            SELECT split_id, specs_json FROM split_proposals
            WHERE namespace = ?
            """,
            (namespace,),
        ).fetchall():
            try:
                specs = _decode_json(split["specs_json"])
            except (ValueError, TypeError) as error:
                raise MemoryInvariantError(
                    "persisted split specification is invalid JSON"
                ) from error
            if not isinstance(specs, list):
                raise MemoryInvariantError("persisted split specification is invalid")
            for spec in specs:
                if not isinstance(spec, dict):
                    raise MemoryInvariantError("persisted split specification is invalid")
                exception = spec.get("exception")
                if not isinstance(exception, dict):
                    raise MemoryInvariantError("persisted split specification is invalid")
                field = exception.get("field")
                if field not in PATTERN_TYPES or "value" not in exception:
                    raise MemoryInvariantError("persisted split specification is invalid")
                current = baseline.get(field)
                if current is None or current == []:
                    continue
                if MemoryStore._memory_value_overlaps(
                    field,
                    current,
                    exception["value"],
                ):
                    matched.setdefault(field, set()).add(split["split_id"])
        result: list[dict[str, Any]] = []
        for field, sources in sorted(matched.items()):
            ordered_sources = sorted(sources)
            result.append(
                {
                    "field": field,
                    "memory_sources": ordered_sources[:8],
                    "memory_source_count": len(ordered_sources),
                }
            )
        return result

    @staticmethod
    def _baseline_attestation_payload(
        source: str | None,
        event_ref: str | None,
    ) -> dict[str, str] | None:
        if source is None and event_ref is None:
            return None
        if source != "direct_user" or not isinstance(event_ref, str) or not event_ref:
            raise MemoryInvariantError(
                "persisted baseline attestation is incomplete or untrusted"
            )
        return {
            "source": source,
            "ref_digest": _confirmation_ref_digest(event_ref),
            "effect": BASELINE_ATTESTATION_EFFECT,
        }

    def propose(
        self,
        *,
        namespace: str,
        episode_id: str,
        input_text: str,
        context: Mapping[str, Any],
        baseline: Mapping[str, Any],
        baseline_source: str | None = None,
        baseline_ref: str | None = None,
    ) -> dict[str, Any]:
        namespace = _require_text("namespace", namespace, max_length=512)
        episode_id = _require_text("episode_id", episode_id, max_length=1024)
        if not isinstance(input_text, str):
            raise MemoryInputError("input_text must be a string")
        input_text = unicodedata.normalize("NFC", input_text)
        if len(input_text) > 200_000:
            raise MemoryInputError("input_text exceeds the size limit")
        context_value = _normalise_scope(context)
        baseline_value = _normalise_json(baseline)
        if not isinstance(baseline_value, dict):
            raise MemoryInputError("baseline must be a JSON object")
        unknown_fields = sorted(set(baseline_value) - ENDPOINT_FIELDS)
        if unknown_fields:
            raise MemoryInputError(
                "baseline contains fields outside the endpoint schema: "
                + ", ".join(unknown_fields)
            )
        if "endpoint" in baseline_value:
            endpoint = _require_text(
                "endpoint", baseline_value["endpoint"], max_length=32
            ).casefold()
            if endpoint not in ENDPOINT_TYPES:
                raise MemoryInputError("baseline endpoint is not a supported Nerd route")
            baseline_value["endpoint"] = endpoint
        for pattern_type in PATTERN_TYPES:
            if pattern_type not in baseline_value:
                continue
            current_value = baseline_value[pattern_type]
            if current_value is None or (
                pattern_type in LIST_PATTERN_TYPES and current_value == []
            ):
                continue
            baseline_value[pattern_type] = _validate_pattern_value(
                pattern_type,
                current_value,
                "fill",
            )
        if (baseline_source is None) != (baseline_ref is None):
            raise MemoryInputError(
                "baseline_source and baseline_ref must be supplied together"
            )
        if baseline_source is not None:
            baseline_source = _require_text(
                "baseline_source", baseline_source, max_length=64
            ).casefold()
            if baseline_source != "direct_user":
                raise MemoryInvariantError(
                    "only a declared direct-user event may attest an explicit baseline"
                )
            baseline_ref = _require_text(
                "baseline_ref", baseline_ref, max_length=2048
            )
        baseline_attestation = self._baseline_attestation_payload(
            baseline_source,
            baseline_ref,
        )
        _reject_sensitive(
            input_text,
            context_value,
            baseline_value,
            baseline_ref,
        )
        proposed = copy.deepcopy(baseline_value)
        proposed.setdefault("endpoint", "abstain")
        for pattern_type in PATTERN_TYPES:
            proposed.setdefault(pattern_type, [] if pattern_type in LIST_PATTERN_TYPES else None)

        now_epoch = self._clock()
        now = _utc_now(now_epoch)
        expires_epoch = now_epoch + self.grant_ttl_seconds
        expires_at = _utc_now(expires_epoch)
        proposal_id = "prp_" + uuid.uuid4().hex
        binding_specs: list[tuple[sqlite3.Row, str, str, Any]] = []
        memory_diff: list[dict[str, Any]] = []
        bindings: list[dict[str, Any]] = []
        with self._transaction() as connection:
            consent = self._require_enabled(namespace, connection)
            baseline_collisions = self._baseline_memory_collisions(
                connection,
                namespace,
                baseline_value,
            )
            if baseline_collisions and baseline_attestation is None:
                raise MemoryBaselineCollisionError(
                    "explicit baseline overlaps memory-derived material "
                    f"{canonical_json(baseline_collisions)}; a unique direct-user "
                    "baseline attestation is required",
                    baseline_collisions,
                )
            if baseline_attestation is not None:
                assert baseline_ref is not None
                self._claim_trusted_event_ref(connection, baseline_ref, now)
            rows = connection.execute(
                """
                SELECT * FROM patterns
                WHERE namespace = ? AND status = 'confirmed'
                ORDER BY pattern_type, pattern_key, pattern_id
                """,
                (namespace,),
            ).fetchall()

            by_type: dict[str, list[tuple[tuple[int, int], sqlite3.Row]]] = {
                item: [] for item in PATTERN_TYPES
            }
            for row in rows:
                try:
                    _decode_stored_pattern_value(
                        row["pattern_type"],
                        row["value_json"],
                        row["operation"],
                    )
                except (MemoryEngineError, ValueError, TypeError, json.JSONDecodeError):
                    connection.execute(
                        """
                        UPDATE patterns
                        SET status = 'contested', revision = revision + 1,
                            updated_at = ?
                        WHERE pattern_id = ?
                        """,
                        (now, row["pattern_id"]),
                    )
                    self._invalidate_pattern_proposals(
                        connection,
                        row["pattern_id"],
                        "invalid_persisted_routing_profile",
                    )
                    continue
                scope_value = _decode_json(row["scope_json"])
                if not _scope_matches(scope_value, context_value):
                    continue
                triggers_value = _decode_json(row["triggers_json"])
                trigger_score = _trigger_score(triggers_value, input_text)
                if trigger_score is None:
                    continue
                by_type[row["pattern_type"]].append(
                    ((_scope_specificity(scope_value), trigger_score), row)
                )

            for pattern_type in PATTERN_TYPES:
                # A current, explicit field is authoritative.  Even append/prepend
                # memories must not broaden it under the guise of composition.
                if proposed[pattern_type] is not None and proposed[pattern_type] != []:
                    continue
                choices = by_type[pattern_type]
                if not choices:
                    continue
                best_rank = max(rank for rank, _ in choices)
                finalists = [row for rank, row in choices if rank == best_rank]
                effects: dict[str, list[sqlite3.Row]] = {}
                for row in finalists:
                    after = self._apply_pattern(
                        proposed[pattern_type],
                        _decode_json(row["value_json"]),
                        row["operation"],
                        pattern_type,
                    )
                    if after is not None:
                        effects.setdefault(canonical_json(after), []).append(row)
                if len(effects) > 1:
                    for effect_json, effect_rows in effects.items():
                        effect = _decode_json(effect_json)
                        for effect_row in effect_rows:
                            binding_specs.append(
                                (
                                    effect_row,
                                    "conflict_candidate",
                                    pattern_type,
                                    effect,
                                )
                            )
                    continue
                if not effects:
                    continue
                effect_json, effect_rows = next(iter(effects.items()))
                after = _decode_json(effect_json)
                before = copy.deepcopy(proposed[pattern_type])
                proposed[pattern_type] = after
                chosen = sorted(effect_rows, key=lambda item: item["pattern_id"])[0]
                binding_specs.append((chosen, "applied", pattern_type, after))
                memory_diff.append(
                    {
                        "field": pattern_type,
                        "before": before,
                        "after": copy.deepcopy(after),
                        "operation": chosen["operation"],
                        "pattern_id": chosen["pattern_id"],
                        "pattern_revision": chosen["revision"],
                    }
                )

            for row, role, field, candidate_effect in binding_specs:
                material_hash = self._pattern_material_hash(row)
                evidence = self._pattern_evidence(connection, row["pattern_id"])
                if len(evidence) <= 6:
                    evidence_sample = evidence
                else:
                    evidence_sample = evidence[:3] + evidence[-3:]
                bindings.append(
                    {
                        "pattern_id": row["pattern_id"],
                        "role": role,
                        "field": field,
                        "candidate_effect": copy.deepcopy(candidate_effect),
                        "revision": row["revision"],
                        "pattern_hash": material_hash,
                        "support_episodes": row["support_episodes"],
                        "evidence_hash": canonical_hash(evidence),
                        "evidence_sample": evidence_sample,
                    }
                )

            memory_conflicts = self._memory_conflicts(bindings)
            memory_influenced = bool(memory_diff or memory_conflicts)
            if memory_conflicts:
                status = "memory_conflict"
            elif memory_diff:
                status = "pending_confirmation"
            else:
                status = "memory_free"
            hash_payload = {
                "schema_version": SCHEMA_VERSION,
                "proposal_id": proposal_id,
                "namespace": namespace,
                "consent_revision": consent["revision"],
                "episode_id": episode_id,
                "input_hash": canonical_hash(input_text),
                "context_hash": canonical_hash(context_value),
                "baseline_hash": canonical_hash(baseline_value),
                "baseline_attestation": baseline_attestation,
                "baseline_collisions": baseline_collisions,
                "proposed_endpoint": proposed,
                "memory_diff": memory_diff,
                "pattern_bindings": bindings,
                "memory_conflicts": memory_conflicts,
                "memory_influenced": memory_influenced,
                "expires_at": expires_at,
            }
            proposal_hash = canonical_hash(hash_payload)
            confirmation_phrase = (
                f"confirm {proposal_id} {proposal_hash[:12]}"
                if status == "pending_confirmation"
                else None
            )

            # A new rendering of the same task supersedes every unconsumed rendering.
            connection.execute(
                """
                UPDATE proposals
                SET status = 'invalidated', grant_digest = NULL,
                    grant_expires_at = NULL, invalid_reason = 'proposal_superseded'
                WHERE namespace = ? AND episode_id = ?
                  AND status IN (
                      'pending_confirmation', 'confirmed', 'memory_conflict', 'memory_free'
                  )
                """,
                (namespace, episode_id),
            )
            connection.execute(
                """
                INSERT INTO proposals(
                    proposal_id, namespace, episode_id, input_hash, context_hash,
                    baseline_hash, baseline_source, baseline_ref,
                    baseline_collisions_json,
                    consent_revision, endpoint_json, diff_json,
                    pattern_bindings_json,
                    memory_influenced, status, proposal_hash, confirmation_phrase,
                    expires_at, grant_digest, grant_expires_at, created_at, confirmed_at,
                    consumed_at, invalid_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                          NULL, NULL, ?, NULL, NULL, ?)
                """,
                (
                    proposal_id,
                    namespace,
                    episode_id,
                    hash_payload["input_hash"],
                    hash_payload["context_hash"],
                    hash_payload["baseline_hash"],
                    baseline_source,
                    baseline_ref,
                    canonical_json(baseline_collisions),
                    consent["revision"],
                    canonical_json(proposed),
                    canonical_json(memory_diff),
                    canonical_json(bindings),
                    int(memory_influenced),
                    status,
                    proposal_hash,
                    confirmation_phrase,
                    expires_epoch,
                    now,
                    (
                        "equally_applicable_patterns_disagree"
                        if memory_conflicts
                        else None
                    ),
                ),
            )
            connection.executemany(
                """
                INSERT INTO proposal_patterns(
                    proposal_id, pattern_id, pattern_revision, pattern_hash
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    (
                        proposal_id,
                        item["pattern_id"],
                        item["revision"],
                        item["pattern_hash"],
                    )
                    for item in bindings
                ),
            )
            row = connection.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
        assert row is not None
        return self._proposal_dict(row)

    @staticmethod
    def _proposal_hash_from_row(row: sqlite3.Row) -> str:
        bindings = _decode_json(row["pattern_bindings_json"])
        return canonical_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "proposal_id": row["proposal_id"],
                "namespace": row["namespace"],
                "consent_revision": row["consent_revision"],
                "episode_id": row["episode_id"],
                "input_hash": row["input_hash"],
                "context_hash": row["context_hash"],
                "baseline_hash": row["baseline_hash"],
                "baseline_attestation": MemoryStore._baseline_attestation_payload(
                    row["baseline_source"], row["baseline_ref"]
                ),
                "baseline_collisions": _decode_json(
                    row["baseline_collisions_json"]
                ),
                "proposed_endpoint": _decode_json(row["endpoint_json"]),
                "memory_diff": _decode_json(row["diff_json"]),
                "pattern_bindings": bindings,
                "memory_conflicts": MemoryStore._memory_conflicts(bindings),
                "memory_influenced": bool(row["memory_influenced"]),
                "expires_at": _utc_now(row["expires_at"]),
            }
        )

    @staticmethod
    def _proposal_dict(row: sqlite3.Row) -> dict[str, Any]:
        bindings = _decode_json(row["pattern_bindings_json"])
        result = {
            "proposal_id": row["proposal_id"],
            "namespace": row["namespace"],
            "episode_id": row["episode_id"],
            "status": row["status"],
            "memory_influenced": bool(row["memory_influenced"]),
            "proposed_endpoint": _decode_json(row["endpoint_json"]),
            "memory_diff": _decode_json(row["diff_json"]),
            "pattern_bindings": bindings,
            "memory_conflicts": MemoryStore._memory_conflicts(bindings),
            "baseline_attestation": (
                {
                    "source": row["baseline_source"],
                    "ref": row["baseline_ref"],
                    "effect": BASELINE_ATTESTATION_EFFECT,
                }
                if row["baseline_source"] is not None
                else None
            ),
            "baseline_collisions": _decode_json(
                row["baseline_collisions_json"]
            ),
            "proposal_hash": row["proposal_hash"],
            "confirmation_phrase": row["confirmation_phrase"],
            "created_at": row["created_at"],
            "expires_at": _utc_now(row["expires_at"]),
            "confirmed_at": row["confirmed_at"],
            "confirmation_source": row["confirmation_source"],
            "confirmation_ref": row["confirmation_ref"],
            "consumed_at": row["consumed_at"],
        }
        if row["grant_expires_at"] is not None:
            result["grant_expires_at"] = _utc_now(row["grant_expires_at"])
        if row["invalid_reason"] is not None:
            result["invalid_reason"] = row["invalid_reason"]
        return result

    def get_proposal(self, proposal_id: str) -> dict[str, Any]:
        proposal_id = _require_text("proposal_id", proposal_id, max_length=128)
        self._ensure_open()
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
        if row is None:
            raise MemoryNotFoundError("memory proposal was not found")
        return self._proposal_dict(row)

    def _validate_proposal_integrity(
        self, connection: sqlite3.Connection, row: sqlite3.Row
    ) -> None:
        # Reconstruct the row-bound hash without trusting client-returned dictionaries.
        bindings = _decode_json(row["pattern_bindings_json"])
        consent = connection.execute(
            "SELECT revision FROM consents WHERE namespace = ?", (row["namespace"],)
        ).fetchone()
        if consent is None:
            raise MemoryInvariantError("proposal consent binding no longer exists")
        if consent["revision"] != row["consent_revision"]:
            raise MemoryInvariantError("proposal consent revision changed")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "proposal_id": row["proposal_id"],
            "namespace": row["namespace"],
            "consent_revision": row["consent_revision"],
            "episode_id": row["episode_id"],
            "input_hash": row["input_hash"],
            "context_hash": row["context_hash"],
            "baseline_hash": row["baseline_hash"],
            "baseline_attestation": self._baseline_attestation_payload(
                row["baseline_source"], row["baseline_ref"]
            ),
            "baseline_collisions": _decode_json(
                row["baseline_collisions_json"]
            ),
            "proposed_endpoint": _decode_json(row["endpoint_json"]),
            "memory_diff": _decode_json(row["diff_json"]),
            "pattern_bindings": bindings,
            "memory_conflicts": self._memory_conflicts(bindings),
            "memory_influenced": bool(row["memory_influenced"]),
            "expires_at": _utc_now(row["expires_at"]),
        }
        actual_hash = canonical_hash(payload)
        if not hmac.compare_digest(actual_hash, row["proposal_hash"]):
            raise MemoryInvariantError("proposal integrity check failed")
        for binding in bindings:
            pattern = connection.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?",
                (binding["pattern_id"],),
            ).fetchone()
            if pattern is None or pattern["status"] != "confirmed":
                raise MemoryInvariantError("a proposal pattern is no longer active")
            if pattern["revision"] != binding["revision"]:
                raise MemoryInvariantError("a proposal pattern revision changed")
            if not hmac.compare_digest(
                self._pattern_material_hash(pattern), binding["pattern_hash"]
            ):
                raise MemoryInvariantError("a proposal pattern integrity check failed")
            evidence = self._pattern_evidence(connection, binding["pattern_id"])
            if not hmac.compare_digest(
                canonical_hash(evidence), binding["evidence_hash"]
            ):
                raise MemoryInvariantError("proposal evidence lineage changed")
            support_episodes = len({item["episode_id"] for item in evidence})
            if support_episodes != binding["support_episodes"]:
                raise MemoryInvariantError("proposal evidence support changed")

    def confirm(
        self,
        proposal_id: str,
        confirmation: str,
        *,
        source: str,
        confirmation_ref: str,
    ) -> dict[str, Any]:
        proposal_id = _require_text("proposal_id", proposal_id, max_length=128)
        if not isinstance(confirmation, str):
            raise MemoryInvariantError("confirmation must exactly match the proposal phrase")
        source = _require_text("source", source, max_length=64).casefold()
        if source != "direct_user":
            raise MemoryInvariantError(
                "only a declared direct-user event may confirm a memory proposal"
            )
        confirmation_ref = _require_text(
            "confirmation_ref", confirmation_ref, max_length=2048
        )
        _reject_sensitive(confirmation_ref)
        now_epoch = self._clock()
        now = _utc_now(now_epoch)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory proposal was not found")
            self._require_enabled(row["namespace"], connection)
            if row["status"] != "pending_confirmation" or not bool(row["memory_influenced"]):
                raise MemoryInvariantError("proposal is not awaiting memory confirmation")
            if now_epoch > row["expires_at"]:
                raise MemoryInvariantError("memory proposal has expired")
            expected = row["confirmation_phrase"]
            if expected is None or not hmac.compare_digest(confirmation, expected):
                raise MemoryInvariantError("confirmation must exactly match the proposal phrase")
            self._validate_proposal_integrity(connection, row)
            confirmation_ref_digest = _confirmation_ref_digest(confirmation_ref)
            used_event = connection.execute(
                """
                SELECT ref_digest FROM confirmation_ref_tombstones
                WHERE ref_digest = ?
                """,
                (confirmation_ref_digest,),
            ).fetchone()
            if used_event is not None:
                raise MemoryInvariantError(
                    "confirmation event was already used in this memory store"
                )
            # The stable prefix prevents an opaque token beginning with "-" from
            # being misparsed as a CLI option when passed as the next argument.
            grant_token = "gnt_" + secrets.token_urlsafe(32)
            grant_digest = hashlib.sha256(
                (row["proposal_hash"] + "\x00" + grant_token).encode("utf-8")
            ).hexdigest()
            expires_at = now_epoch + self.grant_ttl_seconds
            connection.execute(
                """
                UPDATE proposals
                SET status = 'confirmed', grant_digest = ?, grant_expires_at = ?,
                    confirmed_at = ?, confirmation_source = ?, confirmation_ref = ?
                WHERE proposal_id = ? AND status = 'pending_confirmation'
                """,
                (
                    grant_digest,
                    expires_at,
                    now,
                    source,
                    confirmation_ref,
                    proposal_id,
                ),
            )
            connection.execute(
                """
                INSERT INTO confirmation_ref_tombstones(ref_digest, used_at)
                VALUES (?, ?)
                """,
                (confirmation_ref_digest, now),
            )
            connection.execute(
                """
                INSERT INTO confirmation_events(
                    namespace, confirmation_ref, proposal_id, source, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["namespace"],
                    confirmation_ref,
                    proposal_id,
                    source,
                    now,
                ),
            )
        return {
            "proposal_id": proposal_id,
            "status": "confirmed",
            "proposal_hash": row["proposal_hash"],
            "grant_token": grant_token,
            "grant_expires_at": _utc_now(expires_at),
            "memory_gate_only": True,
            "confirmation_source": source,
            "confirmation_ref": confirmation_ref,
        }

    def consume(self, proposal_id: str, grant_token: str | None) -> dict[str, Any]:
        proposal_id = _require_text("proposal_id", proposal_id, max_length=128)
        now_epoch = self._clock()
        now = _utc_now(now_epoch)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory proposal was not found")
            self._require_enabled(row["namespace"], connection)
            memory_influenced = bool(row["memory_influenced"])
            if memory_influenced:
                if row["status"] != "confirmed":
                    raise MemoryInvariantError("memory-influenced proposal has no consumable grant")
                if (
                    row["confirmation_source"] != "direct_user"
                    or not row["confirmation_ref"]
                ):
                    raise MemoryInvariantError(
                        "memory proposal has no trusted confirmation event"
                    )
                if not isinstance(grant_token, str) or not grant_token:
                    raise MemoryInvariantError("an exact one-use grant token is required")
                if now_epoch > row["expires_at"]:
                    raise MemoryInvariantError("memory proposal has expired")
                if row["grant_expires_at"] is None or now_epoch > row["grant_expires_at"]:
                    raise MemoryInvariantError("memory grant has expired")
                expected_digest = hashlib.sha256(
                    (row["proposal_hash"] + "\x00" + grant_token).encode("utf-8")
                ).hexdigest()
                if row["grant_digest"] is None or not hmac.compare_digest(
                    expected_digest, row["grant_digest"]
                ):
                    raise MemoryInvariantError("grant token does not match this proposal")
                self._validate_proposal_integrity(connection, row)
                expected_status = "confirmed"
            else:
                if row["status"] != "memory_free":
                    raise MemoryInvariantError("proposal is no longer consumable")
                if grant_token is not None:
                    raise MemoryInvariantError("memory-free proposals do not accept grant tokens")
                if now_epoch > row["expires_at"]:
                    raise MemoryInvariantError("memory proposal has expired")
                self._validate_proposal_integrity(connection, row)
                expected_status = "memory_free"
            cursor = connection.execute(
                """
                UPDATE proposals
                SET status = 'consumed', grant_digest = NULL,
                    grant_expires_at = NULL, consumed_at = ?
                WHERE proposal_id = ? AND status = ?
                """,
                (now, proposal_id, expected_status),
            )
            if cursor.rowcount != 1:
                raise MemoryInvariantError("proposal was already consumed or invalidated")
            endpoint = _decode_json(row["endpoint_json"])
            memory_diff = _decode_json(row["diff_json"])
        return {
            "proposal_id": proposal_id,
            "proposal_hash": row["proposal_hash"],
            "endpoint": endpoint,
            "memory_diff": memory_diff,
            "memory_gate_passed": memory_influenced,
            "memory_gate_only": memory_influenced,
        }

    def _denial_dict(
        self,
        row: sqlite3.Row,
        connection: sqlite3.Connection,
    ) -> dict[str, Any]:
        if row["status"] == "forgotten":
            result = {
                "denial_id": row["denial_id"],
                "proposal_id": row["proposal_id"],
                "proposal_hash": row["proposal_hash"],
                "namespace": row["namespace"],
                "episode_id": row["episode_id"],
                "status": "forgotten",
                "source": row["source"],
                "denial_ref": "[forgotten]",
                "created_at": row["created_at"],
                "expires_at": _utc_now(row["expires_at"]),
                "resolution": None,
                "resolution_source": None,
                "resolution_ref": None,
                "resolved_at": row["resolved_at"],
                "applied_bindings": [],
                "denied_endpoint": None,
                "memory_blind_baseline": None,
                "memory_mutated": False,
            }
            if row["invalid_reason"] is not None:
                result["invalid_reason"] = row["invalid_reason"]
            return result

        proposal = None
        proposal = connection.execute(
            """
            SELECT pattern_bindings_json, endpoint_json, diff_json
            FROM proposals WHERE proposal_id = ?
            """,
            (row["proposal_id"],),
        ).fetchone()
        bindings = (
            _decode_json(proposal["pattern_bindings_json"])
            if proposal is not None
            else []
        )
        applied = [item for item in bindings if item.get("role") == "applied"]
        denied_endpoint = (
            _decode_json(proposal["endpoint_json"])
            if proposal is not None
            else None
        )
        memory_blind_baseline = copy.deepcopy(denied_endpoint)
        if proposal is not None and isinstance(memory_blind_baseline, dict):
            for change in reversed(_decode_json(proposal["diff_json"])):
                memory_blind_baseline[change["field"]] = copy.deepcopy(
                    change["before"]
                )
        resolution_phrases = {
            resolution: (
                f"resolve {row['denial_id']} {resolution.replace('_', '-')}"
            )
            for resolution in sorted(DENIAL_RESOLUTIONS)
        }
        result = {
            "denial_id": row["denial_id"],
            "proposal_id": row["proposal_id"],
            "proposal_hash": row["proposal_hash"],
            "namespace": row["namespace"],
            "episode_id": row["episode_id"],
            "status": row["status"],
            "source": row["source"],
            "denial_ref": row["denial_ref"],
            "created_at": row["created_at"],
            "expires_at": _utc_now(row["expires_at"]),
            "resolution": row["resolution"],
            "resolution_source": row["resolution_source"],
            "resolution_ref": row["resolution_ref"],
            "resolved_at": row["resolved_at"],
            "possibilities": [
                "agent_mistake",
                "human_forgot",
                "route_too_generic",
            ],
            "possibility_effects": {
                "agent_mistake": "rebuild the memory-blind route; memory stays unchanged",
                "human_forgot": "keep memory; the denied proposal stays dead",
                "route_too_generic": (
                    "draft a stricter exception and confirm it separately"
                ),
            },
            "resolution_phrases": resolution_phrases,
            "applied_bindings": applied,
            "denied_endpoint": denied_endpoint,
            "memory_blind_baseline": memory_blind_baseline,
            "memory_mutated": row["status"] == "split_applied",
        }
        if row["invalid_reason"] is not None:
            result["invalid_reason"] = row["invalid_reason"]
        return result

    def deny(
        self,
        proposal_id: str,
        *,
        source: str,
        denial_ref: str,
    ) -> dict[str, Any]:
        proposal_id = _require_text("proposal_id", proposal_id, max_length=128)
        source = _require_text("source", source, max_length=64).casefold()
        if source != "direct_user":
            raise MemoryInvariantError(
                "only a declared direct-user event may deny a memory proposal"
            )
        denial_ref = _require_text("denial_ref", denial_ref, max_length=2048)
        _reject_sensitive(denial_ref)
        now_epoch = self._clock()
        now = _utc_now(now_epoch)
        expires_at = now_epoch + self.grant_ttl_seconds
        denial_id = "dny_" + uuid.uuid4().hex
        with self._transaction() as connection:
            proposal = connection.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?",
                (proposal_id,),
            ).fetchone()
            if proposal is None:
                raise MemoryNotFoundError("memory proposal was not found")
            self._require_enabled(proposal["namespace"], connection)
            if proposal["status"] not in {"pending_confirmation", "confirmed"}:
                raise MemoryInvariantError(
                    "only an unconsumed memory recommendation may be denied"
                )
            if not bool(proposal["memory_influenced"]):
                raise MemoryInvariantError("memory-free proposals have no memory recommendation")
            if now_epoch > proposal["expires_at"]:
                raise MemoryInvariantError("memory proposal has expired")
            bindings = _decode_json(proposal["pattern_bindings_json"])
            if self._memory_conflicts(bindings) or not _decode_json(
                proposal["diff_json"]
            ):
                raise MemoryInvariantError(
                    "conflicts and empty routes are resolved without denial learning"
                )
            self._validate_proposal_integrity(connection, proposal)
            if connection.execute(
                "SELECT denial_id FROM denials WHERE proposal_id = ?",
                (proposal_id,),
            ).fetchone() is not None:
                raise MemoryInvariantError("memory proposal was already denied")
            self._claim_trusted_event_ref(connection, denial_ref, now)
            cursor = connection.execute(
                """
                UPDATE proposals
                SET status = 'denied', grant_digest = NULL,
                    grant_expires_at = NULL, invalid_reason = 'user_denied'
                WHERE proposal_id = ? AND status IN ('pending_confirmation', 'confirmed')
                """,
                (proposal_id,),
            )
            if cursor.rowcount != 1:
                raise MemoryInvariantError("memory proposal changed before denial")
            connection.execute(
                """
                INSERT INTO denials(
                    denial_id, proposal_id, proposal_hash, namespace, episode_id,
                    status, source, denial_ref, created_at, expires_at,
                    resolution, resolution_source, resolution_ref, resolved_at,
                    invalid_reason
                ) VALUES (?, ?, ?, ?, ?, 'needs_diagnosis', ?, ?, ?, ?,
                          NULL, NULL, NULL, NULL, NULL)
                """,
                (
                    denial_id,
                    proposal_id,
                    proposal["proposal_hash"],
                    proposal["namespace"],
                    proposal["episode_id"],
                    source,
                    denial_ref,
                    now,
                    expires_at,
                ),
            )
            row = connection.execute(
                "SELECT * FROM denials WHERE denial_id = ?", (denial_id,)
            ).fetchone()
            assert row is not None
            result = self._denial_dict(row, connection)
        return result

    def get_denial(self, denial_id: str) -> dict[str, Any]:
        denial_id = _require_text("denial_id", denial_id, max_length=128)
        self._ensure_open()
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM denials WHERE denial_id = ?", (denial_id,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory denial was not found")
            result = self._denial_dict(row, self._connection)
        return result

    def resolve_denial(
        self,
        denial_id: str,
        *,
        resolution: str,
        confirmation: str,
        source: str,
        resolution_ref: str,
    ) -> dict[str, Any]:
        denial_id = _require_text("denial_id", denial_id, max_length=128)
        resolution = _require_text("resolution", resolution, max_length=64).casefold()
        if resolution not in DENIAL_RESOLUTIONS:
            raise MemoryInputError(
                "resolution must be agent_mistake or human_forgot"
            )
        if not isinstance(confirmation, str):
            raise MemoryInvariantError("denial resolution phrase must match exactly")
        source = _require_text("source", source, max_length=64).casefold()
        if source != "direct_user":
            raise MemoryInvariantError(
                "only a declared direct-user event may resolve a denial"
            )
        resolution_ref = _require_text(
            "resolution_ref", resolution_ref, max_length=2048
        )
        _reject_sensitive(resolution_ref)
        expected = f"resolve {denial_id} {resolution.replace('_', '-')}"
        if not hmac.compare_digest(confirmation, expected):
            raise MemoryInvariantError("denial resolution phrase must match exactly")
        now_epoch = self._clock()
        now = _utc_now(now_epoch)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM denials WHERE denial_id = ?", (denial_id,)
            ).fetchone()
            if row is None:
                raise MemoryNotFoundError("memory denial was not found")
            self._require_enabled(row["namespace"], connection)
            if row["status"] not in {"needs_diagnosis", "split_pending"}:
                raise MemoryInvariantError("memory denial is no longer awaiting resolution")
            if now_epoch > row["expires_at"]:
                raise MemoryInvariantError("memory denial has expired")
            self._claim_trusted_event_ref(connection, resolution_ref, now)
            connection.execute(
                """
                UPDATE split_proposals
                SET status = 'invalidated', invalid_reason = 'denial_resolved_without_split'
                WHERE denial_id = ? AND status = 'pending_confirmation'
                """,
                (denial_id,),
            )
            connection.execute(
                """
                UPDATE denials
                SET status = 'resolved', resolution = ?, resolution_source = ?,
                    resolution_ref = ?, resolved_at = ?, invalid_reason = NULL
                WHERE denial_id = ?
                """,
                (resolution, source, resolution_ref, now, denial_id),
            )
            row = connection.execute(
                "SELECT * FROM denials WHERE denial_id = ?", (denial_id,)
            ).fetchone()
            assert row is not None
            result = self._denial_dict(row, connection)
        result["fresh_proposal_required"] = True
        result["memory_mutated"] = False
        return result

    @staticmethod
    def _split_hash_from_row(row: sqlite3.Row) -> str:
        return canonical_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "split_id": row["split_id"],
                "denial_id": row["denial_id"],
                "namespace": row["namespace"],
                "episode_id": row["episode_id"],
                "proposal_id": row["proposal_id"],
                "proposal_hash": row["proposal_hash"],
                "consent_revision": row["consent_revision"],
                "input_hash": row["input_hash"],
                "context_hash": row["context_hash"],
                "specs": _decode_json(row["specs_json"]),
                "parent_bindings": _decode_json(row["parent_bindings_json"]),
                "unselected_bindings": _decode_json(
                    row["unselected_bindings_json"]
                ),
                "expires_at": _utc_now(row["expires_at"]),
            }
        )

    @staticmethod
    def _split_dict(row: sqlite3.Row) -> dict[str, Any]:
        if row["status"] == "forgotten":
            result = {
                "split_id": row["split_id"],
                "denial_id": row["denial_id"],
                "namespace": row["namespace"],
                "episode_id": row["episode_id"],
                "proposal_id": row["proposal_id"],
                "proposal_hash": row["proposal_hash"],
                "status": "forgotten",
                "parent_fallbacks": [],
                "exceptions": [],
                "parent_bindings": [],
                "unselected_bindings": [],
                "split_hash": row["split_hash"],
                "created_at": row["created_at"],
                "expires_at": _utc_now(row["expires_at"]),
                "confirmed_at": row["confirmed_at"],
                "confirmation_source": None,
                "confirmation_ref": None,
                "effect": (
                    "inert tombstone only; no memory or action transition is available"
                ),
            }
            if row["invalid_reason"] is not None:
                result["invalid_reason"] = row["invalid_reason"]
            return result

        specs = _decode_json(row["specs_json"])
        result = {
            "split_id": row["split_id"],
            "denial_id": row["denial_id"],
            "namespace": row["namespace"],
            "episode_id": row["episode_id"],
            "proposal_id": row["proposal_id"],
            "proposal_hash": row["proposal_hash"],
            "status": row["status"],
            "resolution": "route_too_generic",
            "parent_fallbacks": [item["parent_fallback"] for item in specs],
            "exceptions": [item["exception"] for item in specs],
            "parent_bindings": _decode_json(row["parent_bindings_json"]),
            "unselected_bindings": _decode_json(row["unselected_bindings_json"]),
            "split_hash": row["split_hash"],
            "confirmation_phrase": row["confirmation_phrase"],
            "created_at": row["created_at"],
            "expires_at": _utc_now(row["expires_at"]),
            "confirmed_at": row["confirmed_at"],
            "confirmation_source": row["confirmation_source"],
            "confirmation_ref": row["confirmation_ref"],
            "effect": (
                "memory write only; the denied action stays dead and a fresh proposal is required"
            ),
        }
        if row["invalid_reason"] is not None:
            result["invalid_reason"] = row["invalid_reason"]
        return result

    def propose_split(
        self,
        denial_id: str,
        *,
        input_text: str,
        context: Mapping[str, Any],
        splits: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        denial_id = _require_text("denial_id", denial_id, max_length=128)
        if not isinstance(input_text, str):
            raise MemoryInputError("input_text must be a string")
        input_value = unicodedata.normalize("NFC", input_text)
        if len(input_value) > 200_000:
            raise MemoryInputError("input_text exceeds the size limit")
        context_value = _normalise_scope(context)
        split_values = _normalise_json(splits)
        if (
            not isinstance(split_values, list)
            or not 1 <= len(split_values) <= len(PATTERN_TYPES)
        ):
            raise MemoryInputError(
                f"splits must contain between one and {len(PATTERN_TYPES)} branches"
            )
        _reject_sensitive(input_value, context_value, split_values)
        now_epoch = self._clock()
        now = _utc_now(now_epoch)
        expires_epoch = now_epoch + self.grant_ttl_seconds
        split_id = "spt_" + uuid.uuid4().hex

        with self._transaction() as connection:
            denial = connection.execute(
                "SELECT * FROM denials WHERE denial_id = ?", (denial_id,)
            ).fetchone()
            if denial is None:
                raise MemoryNotFoundError("memory denial was not found")
            if denial["status"] not in {"needs_diagnosis", "split_pending"}:
                raise MemoryInvariantError("memory denial is not eligible for a split")
            if now_epoch > denial["expires_at"]:
                raise MemoryInvariantError("memory denial has expired")
            consent = self._require_enabled(denial["namespace"], connection)
            proposal = connection.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?",
                (denial["proposal_id"],),
            ).fetchone()
            if proposal is None or proposal["proposal_hash"] != denial["proposal_hash"]:
                raise MemoryInvariantError("denied proposal binding is unavailable")
            if proposal["status"] != "denied":
                raise MemoryInvariantError("source proposal is not denied")
            if canonical_hash(input_value) != proposal["input_hash"]:
                raise MemoryInputError("split input does not match the denied proposal")
            if canonical_hash(context_value) != proposal["context_hash"]:
                raise MemoryInputError("split context does not match the denied proposal")
            self._validate_proposal_integrity(connection, proposal)

            applied = [
                item
                for item in _decode_json(proposal["pattern_bindings_json"])
                if item.get("role") == "applied"
            ]
            applied_by_id = {item["pattern_id"]: item for item in applied}
            selected_ids: set[str] = set()
            validated_specs: list[dict[str, Any]] = []
            parent_bindings: list[dict[str, Any]] = []

            for raw_spec in split_values:
                if not isinstance(raw_spec, dict) or set(raw_spec) != {
                    "parent_pattern_id",
                    "exception_scope",
                    "exception_value",
                }:
                    raise MemoryInputError(
                        "each split needs exactly parent_pattern_id, exception_scope, and exception_value"
                    )
                parent_id = _require_text(
                    "parent_pattern_id", raw_spec["parent_pattern_id"], max_length=128
                )
                if parent_id in selected_ids:
                    raise MemoryInputError("a parent pattern may appear only once per split")
                binding = applied_by_id.get(parent_id)
                if binding is None:
                    raise MemoryInputError(
                        "split target was not an applied pattern in the denied proposal"
                    )
                parent = connection.execute(
                    "SELECT * FROM patterns WHERE pattern_id = ?", (parent_id,)
                ).fetchone()
                if parent is None or parent["status"] != "confirmed":
                    raise MemoryInvariantError("split parent is no longer active")
                if parent["revision"] != binding["revision"]:
                    raise MemoryInvariantError("split parent revision changed")
                if not hmac.compare_digest(
                    self._pattern_material_hash(parent), binding["pattern_hash"]
                ):
                    raise MemoryInvariantError("split parent integrity check failed")

                parent_scope = _decode_json(parent["scope_json"])
                exception_scope = _normalise_scope(raw_spec["exception_scope"])
                if _contains_volatile_split_scope_key(exception_scope):
                    raise MemoryInputError(
                        "split scope must use stable context, not request or session identifiers"
                    )
                if not _scope_matches(parent_scope, exception_scope):
                    raise MemoryInputError("exception scope broadens the recorded parent")
                if canonical_json(parent_scope) == canonical_json(exception_scope):
                    raise MemoryInputError("exception scope must strictly specialize the parent")
                if _scope_specificity(exception_scope) <= _scope_specificity(parent_scope):
                    raise MemoryInputError("exception scope is not more specific than the parent")
                if not _scope_matches(exception_scope, context_value):
                    raise MemoryInputError("exception scope does not match the denied case")

                pattern_type = parent["pattern_type"]
                operation = parent["operation"]
                exception_value = _validate_pattern_value(
                    pattern_type, raw_spec["exception_value"], operation
                )
                parent_value = _decode_json(parent["value_json"])
                if canonical_json(exception_value) == canonical_json(parent_value):
                    raise MemoryInputError("exception must change the parent recommendation")
                triggers = _decode_json(parent["triggers_json"])
                trigger_score = _trigger_score(triggers, input_value)
                if trigger_score is None:
                    raise MemoryInputError("inherited parent triggers do not match the denied case")

                key_suffix = canonical_hash(
                    {"parent_pattern_id": parent_id, "scope": exception_scope}
                )[:16]
                suffix = f"::exception::{key_suffix}"
                child_key = parent["pattern_key"][: 512 - len(suffix)] + suffix
                child_fingerprint = self._pattern_fingerprint(
                    denial["namespace"],
                    pattern_type,
                    child_key,
                    exception_value,
                    exception_scope,
                    triggers,
                    operation,
                )
                child_id = "pat_" + child_fingerprint[:32]
                if connection.execute(
                    "SELECT pattern_id FROM patterns WHERE fingerprint = ? OR pattern_id = ?",
                    (child_fingerprint, child_id),
                ).fetchone() is not None:
                    raise MemoryInvariantError("the proposed exception pattern already exists")
                if connection.execute(
                    "SELECT fingerprint FROM forgotten_patterns WHERE fingerprint = ?",
                    (child_fingerprint,),
                ).fetchone() is not None:
                    raise MemoryInvariantError(
                        "the proposed exception pattern was previously forgotten"
                    )

                new_rank = (_scope_specificity(exception_scope), trigger_score)
                for active in connection.execute(
                    """
                    SELECT * FROM patterns
                    WHERE namespace = ? AND pattern_type = ? AND status = 'confirmed'
                    """,
                    (denial["namespace"], pattern_type),
                ).fetchall():
                    if active["pattern_id"] == parent_id:
                        continue
                    active_scope = _decode_json(active["scope_json"])
                    if not _scope_matches(active_scope, context_value):
                        continue
                    active_trigger_score = _trigger_score(
                        _decode_json(active["triggers_json"]), input_value
                    )
                    if active_trigger_score is None:
                        continue
                    active_rank = (
                        _scope_specificity(active_scope),
                        active_trigger_score,
                    )
                    if active_rank >= new_rank:
                        raise MemoryInputError(
                            "exception would be shadowed by or clash with an active route"
                        )

                evidence = self._pattern_evidence(connection, parent_id)
                if len(evidence) <= 6:
                    evidence_sample = evidence
                else:
                    evidence_sample = evidence[:3] + evidence[-3:]
                parent_binding = {
                    "pattern_id": parent_id,
                    "revision": parent["revision"],
                    "pattern_hash": self._pattern_material_hash(parent),
                    "support_episodes": len(
                        {item["episode_id"] for item in evidence}
                    ),
                    "evidence_hash": canonical_hash(evidence),
                    "evidence_sample": evidence_sample,
                }
                parent_bindings.append(parent_binding)
                validated_specs.append(
                    {
                        "parent_fallback": {
                            "pattern_id": parent_id,
                            "field": pattern_type,
                            "pattern_key": parent["pattern_key"],
                            "value": parent_value,
                            "scope": parent_scope,
                            "triggers": triggers,
                            "operation": operation,
                            "effect": "remains the fallback outside the exception scope",
                        },
                        "exception": {
                            "pattern_id": child_id,
                            "field": pattern_type,
                            "pattern_key": child_key,
                            "value": exception_value,
                            "scope": exception_scope,
                            "triggers": triggers,
                            "operation": operation,
                            "parent_pattern_id": parent_id,
                            "activation_reason": "explicit_split",
                            "effect": "wins over the parent by strict scope specificity",
                        },
                    }
                )
                selected_ids.add(parent_id)

            unselected = [
                item for item in applied if item["pattern_id"] not in selected_ids
            ]
            hash_payload = {
                "schema_version": SCHEMA_VERSION,
                "split_id": split_id,
                "denial_id": denial_id,
                "namespace": denial["namespace"],
                "episode_id": denial["episode_id"],
                "proposal_id": denial["proposal_id"],
                "proposal_hash": denial["proposal_hash"],
                "consent_revision": consent["revision"],
                "input_hash": proposal["input_hash"],
                "context_hash": proposal["context_hash"],
                "specs": validated_specs,
                "parent_bindings": parent_bindings,
                "unselected_bindings": unselected,
                "expires_at": _utc_now(expires_epoch),
            }
            split_hash = canonical_hash(hash_payload)
            confirmation_phrase = f"confirm split {split_id} {split_hash[:12]}"
            connection.execute(
                """
                UPDATE split_proposals
                SET status = 'invalidated', invalid_reason = 'split_superseded'
                WHERE denial_id = ? AND status = 'pending_confirmation'
                """,
                (denial_id,),
            )
            connection.execute(
                """
                INSERT INTO split_proposals(
                    split_id, denial_id, namespace, episode_id, proposal_id,
                    proposal_hash, consent_revision, input_hash, context_hash,
                    specs_json, parent_bindings_json, unselected_bindings_json,
                    status, split_hash, confirmation_phrase, created_at, expires_at,
                    confirmed_at, confirmation_source, confirmation_ref, invalid_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                          'pending_confirmation', ?, ?, ?, ?, NULL, NULL, NULL, NULL)
                """,
                (
                    split_id,
                    denial_id,
                    denial["namespace"],
                    denial["episode_id"],
                    denial["proposal_id"],
                    denial["proposal_hash"],
                    consent["revision"],
                    proposal["input_hash"],
                    proposal["context_hash"],
                    canonical_json(validated_specs),
                    canonical_json(parent_bindings),
                    canonical_json(unselected),
                    split_hash,
                    confirmation_phrase,
                    now,
                    expires_epoch,
                ),
            )
            connection.executemany(
                """
                INSERT INTO split_parent_bindings(
                    split_id, parent_pattern_id, parent_revision, parent_hash
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    (
                        split_id,
                        item["pattern_id"],
                        item["revision"],
                        item["pattern_hash"],
                    )
                    for item in parent_bindings
                ),
            )
            connection.execute(
                """
                UPDATE denials
                SET status = 'split_pending', invalid_reason = NULL
                WHERE denial_id = ?
                """,
                (denial_id,),
            )
            row = connection.execute(
                "SELECT * FROM split_proposals WHERE split_id = ?", (split_id,)
            ).fetchone()
            assert row is not None
            result = self._split_dict(row)
        return result

    def get_split(self, split_id: str) -> dict[str, Any]:
        split_id = _require_text("split_id", split_id, max_length=128)
        self._ensure_open()
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM split_proposals WHERE split_id = ?", (split_id,)
            ).fetchone()
        if row is None:
            raise MemoryNotFoundError("memory split proposal was not found")
        return self._split_dict(row)

    def confirm_split(
        self,
        split_id: str,
        confirmation: str,
        *,
        source: str,
        confirmation_ref: str,
    ) -> dict[str, Any]:
        split_id = _require_text("split_id", split_id, max_length=128)
        if not isinstance(confirmation, str):
            raise MemoryInvariantError("split confirmation phrase must match exactly")
        source = _require_text("source", source, max_length=64).casefold()
        if source != "direct_user":
            raise MemoryInvariantError(
                "only a declared direct-user event may confirm a memory split"
            )
        confirmation_ref = _require_text(
            "confirmation_ref", confirmation_ref, max_length=2048
        )
        _reject_sensitive(confirmation_ref)
        now_epoch = self._clock()
        now = _utc_now(now_epoch)
        with self._transaction() as connection:
            split = connection.execute(
                "SELECT * FROM split_proposals WHERE split_id = ?", (split_id,)
            ).fetchone()
            if split is None:
                raise MemoryNotFoundError("memory split proposal was not found")
            if split["status"] != "pending_confirmation":
                raise MemoryInvariantError("memory split is not awaiting confirmation")
            if now_epoch > split["expires_at"]:
                raise MemoryInvariantError("memory split proposal has expired")
            consent = self._require_enabled(split["namespace"], connection)
            if consent["revision"] != split["consent_revision"]:
                raise MemoryInvariantError("memory split consent revision changed")
            denial = connection.execute(
                "SELECT * FROM denials WHERE denial_id = ?", (split["denial_id"],)
            ).fetchone()
            if denial is None or denial["status"] != "split_pending":
                raise MemoryInvariantError("memory denial no longer permits this split")
            source_proposal = connection.execute(
                "SELECT * FROM proposals WHERE proposal_id = ?",
                (split["proposal_id"],),
            ).fetchone()
            if (
                source_proposal is None
                or source_proposal["status"] != "denied"
                or source_proposal["proposal_hash"] != split["proposal_hash"]
                or source_proposal["input_hash"] != split["input_hash"]
                or source_proposal["context_hash"] != split["context_hash"]
            ):
                raise MemoryInvariantError("denied source proposal is no longer intact")
            self._validate_proposal_integrity(connection, source_proposal)
            if not hmac.compare_digest(confirmation, split["confirmation_phrase"]):
                raise MemoryInvariantError("split confirmation phrase must match exactly")
            if not hmac.compare_digest(
                self._split_hash_from_row(split), split["split_hash"]
            ):
                raise MemoryInvariantError("memory split integrity check failed")

            specs = _decode_json(split["specs_json"])
            bindings = {
                item["pattern_id"]: item
                for item in _decode_json(split["parent_bindings_json"])
            }
            for spec in specs:
                parent_id = spec["parent_fallback"]["pattern_id"]
                binding = bindings[parent_id]
                parent = connection.execute(
                    "SELECT * FROM patterns WHERE pattern_id = ?", (parent_id,)
                ).fetchone()
                if parent is None or parent["status"] != "confirmed":
                    raise MemoryInvariantError("memory split parent is no longer active")
                if parent["revision"] != binding["revision"]:
                    raise MemoryInvariantError("memory split parent revision changed")
                if not hmac.compare_digest(
                    self._pattern_material_hash(parent), binding["pattern_hash"]
                ):
                    raise MemoryInvariantError("memory split parent integrity changed")
                evidence = self._pattern_evidence(connection, parent_id)
                if not hmac.compare_digest(
                    canonical_hash(evidence), binding["evidence_hash"]
                ):
                    raise MemoryInvariantError("memory split parent evidence changed")
                child = spec["exception"]
                if connection.execute(
                    "SELECT pattern_id FROM patterns WHERE pattern_id = ?",
                    (child["pattern_id"],),
                ).fetchone() is not None:
                    raise MemoryInvariantError("memory split child already exists")
                child_fingerprint = self._pattern_fingerprint(
                    split["namespace"],
                    child["field"],
                    child["pattern_key"],
                    child["value"],
                    child["scope"],
                    child["triggers"],
                    child["operation"],
                )
                if connection.execute(
                    "SELECT fingerprint FROM forgotten_patterns WHERE fingerprint = ?",
                    (child_fingerprint,),
                ).fetchone() is not None:
                    raise MemoryInvariantError("memory split child was forgotten")

            self._claim_trusted_event_ref(connection, confirmation_ref, now)

            self._invalidate_namespace_routing_state(
                connection,
                split["namespace"],
                "routing_split_applied",
                except_split_id=split_id,
            )

            created_ids: list[str] = []
            for spec in specs:
                parent = spec["parent_fallback"]
                child = spec["exception"]
                value = child["value"]
                value_hash = canonical_hash(value)
                observation_identity = {
                    "namespace": split["namespace"],
                    "episode_id": split["episode_id"],
                    "pattern_type": child["field"],
                    "pattern_key": child["pattern_key"],
                    "value": value,
                    "scope": child["scope"],
                    "triggers": child["triggers"],
                    "operation": child["operation"],
                    "source": "user_correction",
                    "evidence_ref": confirmation_ref,
                }
                observation_hash = canonical_hash(observation_identity)
                observation_id = "obs_" + observation_hash[:32]
                connection.execute(
                    """
                    INSERT INTO observations(
                        observation_id, observation_hash, namespace, episode_id,
                        pattern_type, pattern_key, value_json, value_hash, scope_json,
                        triggers_json, operation, source, eligible, evidence_ref,
                        observed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              'user_correction', 1, ?, ?)
                    """,
                    (
                        observation_id,
                        observation_hash,
                        split["namespace"],
                        split["episode_id"],
                        child["field"],
                        child["pattern_key"],
                        canonical_json(value),
                        value_hash,
                        canonical_json(child["scope"]),
                        canonical_json(child["triggers"]),
                        child["operation"],
                        confirmation_ref,
                        now,
                    ),
                )
                fingerprint = self._pattern_fingerprint(
                    split["namespace"],
                    child["field"],
                    child["pattern_key"],
                    value,
                    child["scope"],
                    child["triggers"],
                    child["operation"],
                )
                expected_id = "pat_" + fingerprint[:32]
                if expected_id != child["pattern_id"]:
                    raise MemoryInvariantError("memory split child identifier changed")
                connection.execute(
                    """
                    INSERT INTO patterns(
                        pattern_id, fingerprint, namespace, pattern_type,
                        pattern_key, value_json, value_hash, scope_json,
                        triggers_json, operation, status, support_episodes,
                        revision, created_at, updated_at, promoted_at,
                        activation_reason, parent_pattern_id, split_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', 1,
                              1, ?, ?, ?, 'explicit_split', ?, ?)
                    """,
                    (
                        child["pattern_id"],
                        fingerprint,
                        split["namespace"],
                        child["field"],
                        child["pattern_key"],
                        canonical_json(value),
                        value_hash,
                        canonical_json(child["scope"]),
                        canonical_json(child["triggers"]),
                        child["operation"],
                        now,
                        now,
                        now,
                        parent["pattern_id"],
                        split_id,
                    ),
                )
                connection.execute(
                    "INSERT INTO pattern_evidence(pattern_id, observation_id) VALUES (?, ?)",
                    (child["pattern_id"], observation_id),
                )
                created_ids.append(child["pattern_id"])

            connection.execute(
                """
                UPDATE split_proposals
                SET status = 'applied', confirmed_at = ?, confirmation_source = ?,
                    confirmation_ref = ?, invalid_reason = NULL
                WHERE split_id = ? AND status = 'pending_confirmation'
                """,
                (now, source, confirmation_ref, split_id),
            )
            connection.execute(
                """
                UPDATE denials
                SET status = 'split_applied', resolution = 'route_too_generic',
                    resolution_source = ?, resolution_ref = ?, resolved_at = ?,
                    invalid_reason = NULL
                WHERE denial_id = ?
                """,
                (source, confirmation_ref, now, split["denial_id"]),
            )
            split = connection.execute(
                "SELECT * FROM split_proposals WHERE split_id = ?", (split_id,)
            ).fetchone()
            assert split is not None
            created_patterns = [
                self._pattern_dict(
                    connection.execute(
                        "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
                    ).fetchone(),
                    connection,
                )
                for pattern_id in created_ids
            ]
            result = self._split_dict(split)
        result["created_patterns"] = created_patterns
        result["memory_write_only"] = True
        result["fresh_proposal_required"] = True
        return result

    @staticmethod
    def _redact_forgotten_lineage(
        connection: sqlite3.Connection,
        namespace: str,
        target_ids: Sequence[str],
        proposal_ids: Sequence[str],
    ) -> None:
        targets = set(target_ids)
        deleted_proposals = set(proposal_ids)
        rows = connection.execute(
            "SELECT * FROM split_proposals WHERE namespace = ?",
            (namespace,),
        ).fetchall()
        redacted_split_ids: list[str] = []
        redacted_denial_ids: set[str] = set()
        for row in rows:
            specs = _decode_json(row["specs_json"])
            unselected = _decode_json(row["unselected_bindings_json"])
            references_target = any(
                item["parent_fallback"]["pattern_id"] in targets
                or item["exception"]["pattern_id"] in targets
                for item in specs
            ) or any(item["pattern_id"] in targets for item in unselected)
            if not references_target and row["proposal_id"] not in deleted_proposals:
                continue
            redacted_split_ids.append(row["split_id"])
            redacted_denial_ids.add(row["denial_id"])
            tombstone_hash = canonical_hash(
                {"split_id": row["split_id"], "status": "forgotten"}
            )
            connection.execute(
                """
                UPDATE split_proposals
                SET specs_json = '[]', parent_bindings_json = '[]',
                    unselected_bindings_json = '[]', status = 'forgotten',
                    split_hash = ?, confirmation_phrase = '[forgotten]',
                    confirmation_source = NULL, confirmation_ref = NULL,
                    invalid_reason = 'pattern_forgotten'
                WHERE split_id = ?
                """,
                (tombstone_hash, row["split_id"]),
            )
        if redacted_split_ids:
            placeholders = ",".join("?" for _ in redacted_split_ids)
            connection.execute(
                f"DELETE FROM split_parent_bindings WHERE split_id IN ({placeholders})",
                tuple(redacted_split_ids),
            )
        if deleted_proposals:
            placeholders = ",".join("?" for _ in deleted_proposals)
            rows = connection.execute(
                f"SELECT denial_id FROM denials WHERE proposal_id IN ({placeholders})",
                tuple(deleted_proposals),
            ).fetchall()
            redacted_denial_ids.update(row["denial_id"] for row in rows)
        for denial_id in redacted_denial_ids:
            connection.execute(
                """
                UPDATE denials
                SET status = 'forgotten', denial_ref = '[forgotten]',
                    resolution = NULL, resolution_source = NULL,
                    resolution_ref = NULL, invalid_reason = 'pattern_forgotten'
                WHERE denial_id = ?
                """,
                (denial_id,),
            )

    @classmethod
    def _forget_preview_dict(
        cls,
        connection: sqlite3.Connection,
        pattern_id: str,
        consent_revision: int,
    ) -> tuple[dict[str, Any], list[sqlite3.Row], list[str], list[str]]:
        target_rows = connection.execute(
            """
            WITH RECURSIVE targets(pattern_id) AS (
                SELECT ?
                UNION
                SELECT patterns.pattern_id
                FROM patterns JOIN targets
                  ON patterns.parent_pattern_id = targets.pattern_id
            )
            SELECT patterns.*
            FROM patterns JOIN targets USING(pattern_id)
            ORDER BY patterns.pattern_id
            """,
            (pattern_id,),
        ).fetchall()
        if not target_rows:
            raise MemoryNotFoundError("memory pattern was not found")
        namespace = target_rows[0]["namespace"]
        target_ids = [row["pattern_id"] for row in target_rows]
        placeholders = ",".join("?" for _ in target_ids)
        observation_rows = connection.execute(
            f"""
            SELECT DISTINCT observations.observation_id
            FROM observations
            JOIN patterns
              ON observations.namespace = patterns.namespace
             AND observations.pattern_type = patterns.pattern_type
             AND observations.pattern_key = patterns.pattern_key
             AND observations.value_hash = patterns.value_hash
             AND observations.scope_json = patterns.scope_json
             AND observations.triggers_json = patterns.triggers_json
             AND observations.operation = patterns.operation
            WHERE patterns.pattern_id IN ({placeholders})
            ORDER BY observations.observation_id
            """,
            tuple(target_ids),
        ).fetchall()
        proposal_rows = connection.execute(
            f"""
            SELECT DISTINCT proposals.*
            FROM proposals JOIN proposal_patterns USING(proposal_id)
            WHERE proposal_patterns.pattern_id IN ({placeholders})
            ORDER BY proposals.proposal_id
            """,
            tuple(target_ids),
        ).fetchall()
        observation_ids = [row["observation_id"] for row in observation_rows]
        proposal_ids = [row["proposal_id"] for row in proposal_rows]
        proposal_bindings = [
            {
                "proposal_id": row["proposal_id"],
                "proposal_hash": row["proposal_hash"],
                "status": row["status"],
                "grant_digest": row["grant_digest"],
                "grant_expires_at": row["grant_expires_at"],
            }
            for row in proposal_rows
        ]
        target_set = set(target_ids)
        proposal_set = set(proposal_ids)
        split_ids: list[str] = []
        split_bindings: list[dict[str, Any]] = []
        denial_ids: set[str] = set()
        for split in connection.execute(
            "SELECT * FROM split_proposals WHERE namespace = ? ORDER BY split_id",
            (namespace,),
        ).fetchall():
            specs = _decode_json(split["specs_json"])
            unselected = _decode_json(split["unselected_bindings_json"])
            references_target = any(
                item["parent_fallback"]["pattern_id"] in target_set
                or item["exception"]["pattern_id"] in target_set
                for item in specs
            ) or any(item["pattern_id"] in target_set for item in unselected)
            if references_target or split["proposal_id"] in proposal_set:
                split_ids.append(split["split_id"])
                denial_ids.add(split["denial_id"])
                split_bindings.append(
                    {
                        "split_id": split["split_id"],
                        "denial_id": split["denial_id"],
                        "status": split["status"],
                        "split_hash": split["split_hash"],
                        "confirmation_ref_digest": (
                            _confirmation_ref_digest(split["confirmation_ref"])
                            if split["confirmation_ref"] is not None
                            else None
                        ),
                    }
                )
        if proposal_ids:
            proposal_placeholders = ",".join("?" for _ in proposal_ids)
            denial_ids.update(
                row["denial_id"]
                for row in connection.execute(
                    f"SELECT denial_id FROM denials "
                    f"WHERE proposal_id IN ({proposal_placeholders})",
                    tuple(proposal_ids),
                ).fetchall()
            )
        denial_bindings: list[dict[str, Any]] = []
        if denial_ids:
            denial_placeholders = ",".join("?" for _ in denial_ids)
            denial_bindings = [
                {
                    "denial_id": row["denial_id"],
                    "proposal_id": row["proposal_id"],
                    "proposal_hash": row["proposal_hash"],
                    "status": row["status"],
                    "denial_ref_digest": _confirmation_ref_digest(
                        row["denial_ref"]
                    ),
                    "resolution": row["resolution"],
                    "resolution_ref_digest": (
                        _confirmation_ref_digest(row["resolution_ref"])
                        if row["resolution_ref"] is not None
                        else None
                    ),
                }
                for row in connection.execute(
                    f"SELECT * FROM denials "
                    f"WHERE denial_id IN ({denial_placeholders}) "
                    "ORDER BY denial_id",
                    tuple(sorted(denial_ids)),
                ).fetchall()
            ]

        binding_targets: list[dict[str, Any]] = []
        cascade: list[dict[str, Any]] = []
        for row in target_rows:
            evidence = cls._pattern_evidence(connection, row["pattern_id"])
            binding_targets.append(
                {
                    "pattern_id": row["pattern_id"],
                    "pattern_hash": cls._pattern_material_hash(row),
                    "evidence_hash": canonical_hash(evidence),
                }
            )
            cascade.append(
                {
                    "pattern_id": row["pattern_id"],
                    "pattern_type": row["pattern_type"],
                    "pattern_key": row["pattern_key"],
                    "value": _decode_json(row["value_json"]),
                    "scope": _decode_json(row["scope_json"]),
                    "triggers": _decode_json(row["triggers_json"]),
                    "operation": row["operation"],
                    "status": row["status"],
                    "parent_pattern_id": row["parent_pattern_id"],
                    "evidence_count": len(evidence),
                }
            )
        backup_limitation = (
            "local forgetting cannot erase backups, exported copies, or external systems"
        )
        decision_hash = canonical_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "operation": "forget",
                "namespace": namespace,
                "consent_revision": consent_revision,
                "root_pattern_id": pattern_id,
                "targets": binding_targets,
                "observation_ids": observation_ids,
                "proposals": proposal_bindings,
                "splits": split_bindings,
                "denials": denial_bindings,
                "backup_limitation": backup_limitation,
            }
        )
        preview = {
            "operation": "forget",
            "namespace": namespace,
            "root_pattern_id": pattern_id,
            "cascade": cascade,
            "deleted_patterns": len(target_ids),
            "matching_observations": len(observation_ids),
            "bound_proposals": len(proposal_ids),
            "dependent_proposals": [
                {
                    "proposal_id": item["proposal_id"],
                    "status": item["status"],
                    "has_live_grant": item["grant_digest"] is not None,
                }
                for item in proposal_bindings
            ],
            "redacted_splits": len(split_ids),
            "dependent_splits": [
                {
                    "split_id": item["split_id"],
                    "status": item["status"],
                }
                for item in split_bindings
            ],
            "redacted_denials": len(denial_bindings),
            "dependent_denials": [
                {
                    "denial_id": item["denial_id"],
                    "status": item["status"],
                }
                for item in denial_bindings
            ],
            "decision_hash": decision_hash,
            "confirmation_phrase": (
                f"confirm forget {pattern_id} {decision_hash[:12]}"
            ),
            "effect": (
                "deletes the exact pattern lineage, direct evidence, and bound "
                "proposals; destroys their grants; redacts dependent refinement "
                "history; and tombstones the forgotten fingerprints"
            ),
            "backup_limitation": backup_limitation,
        }
        return preview, target_rows, observation_ids, proposal_ids

    def preview_forget(self, pattern_id: str) -> dict[str, Any]:
        pattern_id = _require_text("pattern_id", pattern_id, max_length=128)
        self._ensure_open()
        with self._lock:
            pattern = self._connection.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
            ).fetchone()
            if pattern is None:
                raise MemoryNotFoundError("memory pattern was not found")
            consent = self._require_enabled(pattern["namespace"], self._connection)
            preview, _, _, _ = self._forget_preview_dict(
                self._connection,
                pattern_id,
                consent["revision"],
            )
        return preview

    def forget(
        self,
        pattern_id: str,
        confirmation: str,
        *,
        source: str,
        confirmation_ref: str,
    ) -> dict[str, Any]:
        pattern_id = _require_text("pattern_id", pattern_id, max_length=128)
        if not isinstance(confirmation, str):
            raise MemoryInvariantError("forget confirmation phrase must match exactly")
        source = _require_text("source", source, max_length=64).casefold()
        if source != "direct_user":
            raise MemoryInvariantError(
                "only a declared direct-user event may forget a memory pattern"
            )
        confirmation_ref = _require_text(
            "confirmation_ref", confirmation_ref, max_length=2048
        )
        _reject_sensitive(confirmation_ref)
        now = _utc_now(self._clock())
        with self._transaction() as connection:
            pattern = connection.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,)
            ).fetchone()
            if pattern is None:
                raise MemoryNotFoundError("memory pattern was not found")
            consent = self._require_enabled(pattern["namespace"], connection)
            preview, target_rows, observation_ids, proposal_ids = (
                self._forget_preview_dict(
                    connection,
                    pattern_id,
                    consent["revision"],
                )
            )
            if not hmac.compare_digest(
                confirmation,
                preview["confirmation_phrase"],
            ):
                raise MemoryInvariantError(
                    "forget confirmation phrase must match exact current preview"
                )
            self._claim_trusted_event_ref(connection, confirmation_ref, now)
            target_ids = [row["pattern_id"] for row in target_rows]
            connection.executemany(
                """
                INSERT OR IGNORE INTO forgotten_patterns(
                    fingerprint, namespace, pattern_id, forgotten_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    (
                        row["fingerprint"],
                        pattern["namespace"],
                        row["pattern_id"],
                        now,
                    )
                    for row in target_rows
                ),
            )
            for target_id in target_ids:
                self._invalidate_pattern_proposals(
                    connection, target_id, "pattern_forgotten"
                )
            self._redact_forgotten_lineage(
                connection,
                pattern["namespace"],
                target_ids,
                proposal_ids,
            )
            target_placeholders = ",".join("?" for _ in target_ids)
            if proposal_ids:
                placeholders = ",".join("?" for _ in proposal_ids)
                connection.execute(
                    f"DELETE FROM proposals WHERE proposal_id IN ({placeholders})",
                    tuple(proposal_ids),
                )
            connection.execute(
                f"DELETE FROM patterns WHERE pattern_id IN ({target_placeholders})",
                tuple(target_ids),
            )
            deleted_observations = 0
            if observation_ids:
                placeholders = ",".join("?" for _ in observation_ids)
                cursor = connection.execute(
                    f"""
                    DELETE FROM observations
                    WHERE observation_id IN ({placeholders})
                      AND NOT EXISTS (
                          SELECT 1 FROM pattern_evidence
                          WHERE pattern_evidence.observation_id = observations.observation_id
                      )
                    """,
                    tuple(observation_ids),
                )
                deleted_observations = cursor.rowcount
        return {
            "pattern_id": pattern_id,
            "namespace": pattern["namespace"],
            "deleted_pattern_ids": target_ids,
            "deleted_patterns": len(target_ids),
            "deleted_observations": deleted_observations,
            "deleted_proposals": len(proposal_ids),
            "memory_write_only": True,
            "fresh_proposal_required": True,
        }


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise MemoryInputError(message)


def _json_argument(name: str, value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise MemoryInputError(f"{name} must contain valid JSON") from error


def _build_parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(
        prog="nerd-memory",
        description="Local evidence-backed memory with exact confirmation gates.",
    )
    parser.add_argument(
        "--db",
        default=os.fspath(default_store_path()),
        help="SQLite store path (default: NERD_MEMORY_DB or CODEX_HOME).",
    )
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_JsonArgumentParser)

    enable = commands.add_parser("enable")
    enable.add_argument("--namespace", required=True)
    enable.add_argument("--consent-ref", required=True)

    disable = commands.add_parser("disable")
    disable.add_argument("--namespace", required=True)
    disable.add_argument("--consent-ref", required=True)

    status = commands.add_parser("status")
    status.add_argument("--namespace", required=True)

    observe = commands.add_parser(
        "observe",
        description=(
            "Append one typed observation. JSON strings need JSON quotes; "
            "task/action/boundary/verification values are non-empty arrays; "
            "routing is an ordered array of atomic agent capability profiles."
        ),
    )
    observe.add_argument("--namespace", required=True)
    observe.add_argument("--episode-id", required=True)
    observe.add_argument("--pattern-type", required=True, choices=PATTERN_TYPES)
    observe.add_argument("--pattern-key", required=True)
    observe.add_argument(
        "--value",
        required=True,
        metavar="JSON",
        help="Complete JSON pattern value.",
    )
    observe.add_argument(
        "--scope",
        default="{}",
        metavar="JSON_OBJECT",
        help="Exact applicability object (default: {}).",
    )
    observe.add_argument(
        "--triggers",
        default="[]",
        metavar="JSON_ARRAY",
        help="Literal trigger strings (default: []).",
    )
    observe.add_argument("--operation", default="fill", choices=sorted(OPERATIONS))
    observe.add_argument(
        "--source",
        required=True,
        choices=sorted(OBSERVATION_SOURCES),
        help="Declared trusted-event provenance class.",
    )
    observe.add_argument("--evidence-ref", required=True)

    consolidate = commands.add_parser("consolidate")
    consolidate.add_argument("--namespace", required=True)
    consolidate.add_argument("--min-episodes", type=int, default=DEFAULT_MIN_EPISODES)

    list_parser = commands.add_parser("list", aliases=["list-patterns"])
    list_parser.add_argument("--namespace", required=True)

    preview_promote = commands.add_parser("preview-promote")
    preview_promote.add_argument("--pattern-id", required=True)

    promote = commands.add_parser(
        "promote",
        description="Promote the exact current preview from a trusted direct-user event.",
    )
    promote.add_argument("--pattern-id", required=True)
    promote.add_argument("--phrase", required=True)
    promote.add_argument("--source", required=True, choices=("direct_user",))
    promote.add_argument("--confirmation-ref", required=True)

    propose = commands.add_parser(
        "propose",
        description=(
            "Construct a persisted endpoint proposal. CONTEXT and BASELINE are "
            "complete JSON objects; raw input is hashed, not persisted."
        ),
    )
    propose.add_argument("--namespace", required=True)
    propose.add_argument("--episode-id", required=True)
    propose.add_argument("--input-text", required=True)
    propose.add_argument("--context", required=True, metavar="JSON_OBJECT")
    propose.add_argument("--baseline", required=True, metavar="JSON_OBJECT")
    propose.add_argument(
        "--baseline-source",
        choices=("direct_user",),
        help=(
            "Attest that an explicit baseline overlapping memory came from the "
            "current direct-user event; requires --baseline-ref."
        ),
    )
    propose.add_argument(
        "--baseline-ref",
        help="Unique direct-user event reference paired with --baseline-source.",
    )

    get_parser = commands.add_parser("get", aliases=["get-proposal"])
    get_parser.add_argument("--proposal-id", required=True)

    confirm = commands.add_parser(
        "confirm",
        description=(
            "Mint one expiring grant from an exact phrase and a unique, trusted "
            "direct-user event reference."
        ),
    )
    confirm.add_argument("--proposal-id", required=True)
    confirm.add_argument("--phrase", required=True)
    confirm.add_argument("--source", required=True, choices=("direct_user",))
    confirm.add_argument("--confirmation-ref", required=True)

    consume = commands.add_parser("consume")
    consume.add_argument("--proposal-id", required=True)
    consume.add_argument("--grant-token")

    deny = commands.add_parser(
        "deny",
        description=(
            "Kill an unconsumed memory recommendation without changing its patterns."
        ),
    )
    deny.add_argument("--proposal-id", required=True)
    deny.add_argument("--source", required=True, choices=("direct_user",))
    deny.add_argument("--denial-ref", required=True)

    get_denial = commands.add_parser("get-denial")
    get_denial.add_argument("--denial-id", required=True)

    resolve_denial = commands.add_parser(
        "resolve-denial",
        description=(
            "Close a denial as agent_mistake or human_forgot without mutating memory."
        ),
    )
    resolve_denial.add_argument("--denial-id", required=True)
    resolve_denial.add_argument(
        "--resolution", required=True, choices=sorted(DENIAL_RESOLUTIONS)
    )
    resolve_denial.add_argument("--phrase", required=True)
    resolve_denial.add_argument("--source", required=True, choices=("direct_user",))
    resolve_denial.add_argument("--resolution-ref", required=True)

    propose_split = commands.add_parser(
        "propose-split",
        description=(
            "Draft strict-scope exceptions for applied patterns from a denied proposal."
        ),
    )
    propose_split.add_argument("--denial-id", required=True)
    propose_split.add_argument("--input-text", required=True)
    propose_split.add_argument("--context", required=True, metavar="JSON_OBJECT")
    propose_split.add_argument("--splits", required=True, metavar="JSON_ARRAY")

    get_split = commands.add_parser("get-split")
    get_split.add_argument("--split-id", required=True)

    confirm_split = commands.add_parser(
        "confirm-split",
        description=(
            "Apply an exact split as a memory write only; it never revives the denied action."
        ),
    )
    confirm_split.add_argument("--split-id", required=True)
    confirm_split.add_argument("--phrase", required=True)
    confirm_split.add_argument("--source", required=True, choices=("direct_user",))
    confirm_split.add_argument("--confirmation-ref", required=True)

    preview_forget = commands.add_parser("preview-forget")
    preview_forget.add_argument("--pattern-id", required=True)

    forget = commands.add_parser(
        "forget",
        description="Forget the exact current cascade from a trusted direct-user event.",
    )
    forget.add_argument("--pattern-id", required=True)
    forget.add_argument("--phrase", required=True)
    forget.add_argument("--source", required=True, choices=("direct_user",))
    forget.add_argument("--confirmation-ref", required=True)
    return parser


def _run_command(store: MemoryStore, arguments: argparse.Namespace) -> Any:
    command = arguments.command
    if command == "enable":
        return store.enable(arguments.namespace, consent_ref=arguments.consent_ref)
    if command == "disable":
        return store.disable(arguments.namespace, consent_ref=arguments.consent_ref)
    if command == "status":
        return store.consent_status(arguments.namespace)
    if command == "observe":
        return store.observe(
            namespace=arguments.namespace,
            episode_id=arguments.episode_id,
            pattern_type=arguments.pattern_type,
            pattern_key=arguments.pattern_key,
            value=_json_argument("--value", arguments.value),
            scope=_json_argument("--scope", arguments.scope),
            triggers=_json_argument("--triggers", arguments.triggers),
            operation=arguments.operation,
            source=arguments.source,
            evidence_ref=arguments.evidence_ref,
        )
    if command == "consolidate":
        return store.consolidate(arguments.namespace, min_episodes=arguments.min_episodes)
    if command in {"list", "list-patterns"}:
        return store.list_patterns(arguments.namespace)
    if command == "preview-promote":
        return store.preview_promote(arguments.pattern_id)
    if command == "promote":
        return store.promote(
            arguments.pattern_id,
            arguments.phrase,
            source=arguments.source,
            confirmation_ref=arguments.confirmation_ref,
        )
    if command == "propose":
        return store.propose(
            namespace=arguments.namespace,
            episode_id=arguments.episode_id,
            input_text=arguments.input_text,
            context=_json_argument("--context", arguments.context),
            baseline=_json_argument("--baseline", arguments.baseline),
            baseline_source=arguments.baseline_source,
            baseline_ref=arguments.baseline_ref,
        )
    if command in {"get", "get-proposal"}:
        return store.get_proposal(arguments.proposal_id)
    if command == "confirm":
        return store.confirm(
            arguments.proposal_id,
            arguments.phrase,
            source=arguments.source,
            confirmation_ref=arguments.confirmation_ref,
        )
    if command == "consume":
        return store.consume(arguments.proposal_id, arguments.grant_token)
    if command == "deny":
        return store.deny(
            arguments.proposal_id,
            source=arguments.source,
            denial_ref=arguments.denial_ref,
        )
    if command == "get-denial":
        return store.get_denial(arguments.denial_id)
    if command == "resolve-denial":
        return store.resolve_denial(
            arguments.denial_id,
            resolution=arguments.resolution,
            confirmation=arguments.phrase,
            source=arguments.source,
            resolution_ref=arguments.resolution_ref,
        )
    if command == "propose-split":
        return store.propose_split(
            arguments.denial_id,
            input_text=arguments.input_text,
            context=_json_argument("--context", arguments.context),
            splits=_json_argument("--splits", arguments.splits),
        )
    if command == "get-split":
        return store.get_split(arguments.split_id)
    if command == "confirm-split":
        return store.confirm_split(
            arguments.split_id,
            arguments.phrase,
            source=arguments.source,
            confirmation_ref=arguments.confirmation_ref,
        )
    if command == "preview-forget":
        return store.preview_forget(arguments.pattern_id)
    if command == "forget":
        return store.forget(
            arguments.pattern_id,
            arguments.phrase,
            source=arguments.source,
            confirmation_ref=arguments.confirmation_ref,
        )
    raise MemoryInputError("unknown memory command")


_ERROR_CODES: tuple[tuple[type[BaseException], str, int], ...] = (
    (MemoryNotFoundError, "not_found", 4),
    (MemoryConsentError, "consent_required", 5),
    (MemoryInvariantError, "invariant_violation", 3),
    (MemoryInputError, "invalid_input", 2),
    (sqlite3.Error, "storage_error", 6),
)


def _emit_json(value: Any, *, stream: Any = sys.stdout) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
    stream.flush()


def main(argv: Sequence[str] | None = None) -> int:
    store: MemoryStore | None = None
    try:
        arguments = _build_parser().parse_args(argv)
        store = MemoryStore(arguments.db)
        result = _run_command(store, arguments)
        _emit_json(result)
        return 0
    except KeyboardInterrupt:
        _emit_json(
            {"ok": False, "error": {"code": "interrupted", "type": "KeyboardInterrupt", "message": "interrupted"}},
            stream=sys.stderr,
        )
        return 130
    except Exception as error:
        for error_type, code, exit_code in _ERROR_CODES:
            if isinstance(error, error_type):
                error_payload: dict[str, Any] = {
                    "code": code,
                    "type": type(error).__name__,
                    "message": str(error),
                }
                if isinstance(error, MemoryBaselineCollisionError):
                    error_payload["details"] = {
                        "baseline_collisions": error.collisions,
                        "required_attestation": {
                            "source": "direct_user",
                            "unique_event_ref": True,
                            "effect": BASELINE_ATTESTATION_EFFECT,
                        },
                    }
                _emit_json(
                    {
                        "ok": False,
                        "error": error_payload,
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
