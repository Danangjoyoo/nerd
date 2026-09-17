"""Disposable typed-ledger retrieval used by the preregistered POC."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import secrets
import sqlite3


DEPLOYABLE_MAX_PACK_BYTES = 2_048
PACK_START = "<NERD_CONTEXT_PACK_V1>"
PACK_END = "</NERD_CONTEXT_PACK_V1>"
PACK_AUTHORITY = '{"authority":"untrusted_context"}'
RECORD_KINDS = frozenset({"goal", "boundary", "decision", "evidence", "open_question", "checkpoint"})
RECORD_SOURCES = frozenset({"direct_user", "assistant_summary", "verified_tool", "repository_fact"})
CONTEXT_ID_RE = re.compile(r"ctx_[a-z2-7]{38}[aiqy]\Z")
MAX_CAPTURE_RECORDS = 30
MANDATORY_ORDER = {"boundary": 0, "decision": 1, "goal": 2}
TERM_RE = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "case",
    "current",
    "for",
    "from",
    "in",
    "is",
    "next",
    "of",
    "only",
    "or",
    "request",
    "retrieval",
    "return",
    "task",
    "the",
    "to",
    "topic",
}


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
    if len(segment.encode("utf-8")) > DEPLOYABLE_MAX_PACK_BYTES:
        raise ValueError("context pack exceeds the 2048-byte deployable ceiling")
    return segment


def _terms(value: str) -> frozenset[str]:
    return frozenset(
        term
        for term in TERM_RE.findall(value.casefold())
        if term not in STOP_WORDS and not (term.isdigit() and len(term) == 1)
    )


@dataclass(frozen=True)
class RecallResult:
    segment: str
    record_ids: tuple[str, ...]
    overflow: bool
    index_mode: str
    context_id: str | None = None
    created: bool = False
    status: str = "ok"


def _validate_context_id(context_id: str) -> str:
    if not isinstance(context_id, str) or not CONTEXT_ID_RE.fullmatch(context_id):
        raise ValueError("invalid canonical context ID")
    encoded = context_id[4:]
    decoded = base64.b32decode(encoded.upper() + "=")
    if len(decoded) != 24 or base64.b32encode(decoded).decode().rstrip("=").lower() != encoded:
        raise ValueError("invalid canonical context ID")
    return context_id


def _new_context_id() -> str:
    return "ctx_" + base64.b32encode(secrets.token_bytes(24)).decode("ascii").rstrip("=").lower()


def _validate_record(record: dict, *, fixture: bool = False) -> dict:
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    allowed = {"kind", "value", "source", "source_ref", "supersedes_id", "context_id"}
    if not fixture and set(record) - allowed:
        raise ValueError("unsupported capture record fields")
    if not isinstance(record.get("kind"), str) or record["kind"] not in RECORD_KINDS:
        raise ValueError("unsupported record kind")
    source = record.get("source", "assistant_summary" if fixture else None)
    if not isinstance(source, str) or source not in RECORD_SOURCES:
        raise ValueError("unsupported record source")
    for field, ceiling in (("value", 8_192), ("source_ref", 256)):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > ceiling:
            raise ValueError(f"invalid record {field}")
    supersedes_id = record.get("supersedes_id")
    if supersedes_id is not None and (not isinstance(supersedes_id, str) or not supersedes_id):
        raise ValueError("invalid supersedes ID")
    return {
        "kind": record["kind"],
        "value": record["value"],
        "source": source,
        "source_ref": record["source_ref"],
        "supersedes_id": supersedes_id,
    }


class StructuredLedger:
    def __init__(
        self,
        records: list[dict] | tuple = (),
        *,
        index_mode: str = "normalized_scan",
        database: Path | None = None,
    ) -> None:
        if index_mode not in {"fts5", "normalized_scan"}:
            raise ValueError("unsupported index mode")
        self.index_mode = index_mode
        self.database = database
        self._connection = sqlite3.connect(database or ":memory:")
        self._connection.row_factory = sqlite3.Row
        try:
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS contexts (context_id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS records (
                    sequence INTEGER PRIMARY KEY,
                    id TEXT NOT NULL UNIQUE,
                    context_id TEXT NOT NULL REFERENCES contexts(context_id),
                    kind TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    active INTEGER NOT NULL CHECK (active IN (0, 1)),
                    supersedes_id TEXT REFERENCES records(id),
                    terms TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS records_context_active
                    ON records(context_id, active, sequence);
                CREATE TABLE IF NOT EXISTS captures (
                    capture_ref TEXT PRIMARY KEY,
                    context_id TEXT NOT NULL REFERENCES contexts(context_id),
                    digest TEXT NOT NULL,
                    accepted_ids TEXT NOT NULL,
                    superseded_ids TEXT NOT NULL
                );
            """)
            if index_mode == "fts5":
                self._initialize_fts5()
            self._load_gold_fixture(records)
        except BaseException:
            self._connection.close()
            raise

    def _initialize_fts5(self) -> None:
        exists = self._connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'poc_record_terms'"
        ).fetchone()
        self._connection.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS poc_record_terms USING fts5(
                terms, content='records', content_rowid='sequence', tokenize='ascii'
            );
            CREATE TRIGGER IF NOT EXISTS poc_records_insert AFTER INSERT ON records BEGIN
                INSERT INTO poc_record_terms(rowid, terms) VALUES (new.sequence, new.terms);
            END;
        """)
        if not exists:
            self._connection.execute("INSERT INTO poc_record_terms(poc_record_terms) VALUES ('rebuild')")
            self._connection.commit()

    def _load_gold_fixture(self, records: list[dict] | tuple) -> None:
        """Explicit evaluator-only seed path; runtime capture never accepts chosen IDs."""
        with self._connection:
            for record in records:
                context_id = _validate_context_id(record.get("context_id"))
                normalized = _validate_record(record, fixture=True)
                record_id = record.get("id")
                if not isinstance(record_id, str) or not record_id:
                    raise ValueError("gold fixture requires a record ID")
                if type(record.get("active", True)) is not bool:
                    raise ValueError("invalid gold fixture active flag")
                self._connection.execute(
                    "INSERT OR IGNORE INTO contexts(context_id) VALUES (?)", (context_id,)
                )
                self._insert_record(
                    record_id, context_id, normalized, active=record.get("active", True)
                )

    def _insert_record(self, record_id: str, context_id: str, record: dict, *, active: bool = True) -> None:
        self._connection.execute(
            """INSERT INTO records
                (id, context_id, kind, value, source, source_ref, active, supersedes_id, terms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record_id, context_id, record["kind"], record["value"], record["source"],
                record["source_ref"], int(active), record.get("supersedes_id"),
                " ".join(sorted(_terms(record["value"]))),
            ),
        )

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> StructuredLedger:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def counts(self) -> dict:
        """Aggregate POC observations only: no alternate context-ID lookup surface."""
        return {
            "context_count": self._connection.execute("SELECT COUNT(*) FROM contexts").fetchone()[0],
            "record_count": self._connection.execute("SELECT COUNT(*) FROM records").fetchone()[0],
            "capture_count": self._connection.execute("SELECT COUNT(*) FROM captures").fetchone()[0],
        }

    def inspect(self, context_id: str, *, limit: int = 50) -> dict:
        _validate_context_id(context_id)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid inspection limit")
        if not self._connection.execute(
            "SELECT 1 FROM contexts WHERE context_id = ?", (context_id,)
        ).fetchone():
            return {"status": "not_found", "context_id": context_id}
        counts = self._connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(active), 0) FROM records WHERE context_id = ?", (context_id,)
        ).fetchone()
        metadata = self._connection.execute(
            """SELECT id, kind, source, source_ref, active, supersedes_id
                FROM records WHERE context_id = ? ORDER BY sequence LIMIT ?""",
            (context_id, limit),
        ).fetchall()
        return {
            "status": "ok", "context_id": context_id,
            "record_count": counts[0], "active_record_count": counts[1],
            "capture_count": self._connection.execute(
                "SELECT COUNT(*) FROM captures WHERE context_id = ?", (context_id,)
            ).fetchone()[0],
            "record_metadata": [dict(row) for row in metadata],
        }

    def capture(self, context_id: str, records: list[dict], capture_ref: str) -> dict:
        _validate_context_id(context_id)
        if not isinstance(records, list) or len(records) > MAX_CAPTURE_RECORDS:
            raise ValueError("capture accepts at most 30 records")
        if not isinstance(capture_ref, str) or not capture_ref.strip() or len(capture_ref.encode()) > 256:
            raise ValueError("invalid capture reference")
        normalized = []
        for record in records:
            item = _validate_record(record)
            if record.get("context_id", context_id) != context_id:
                raise ValueError("capture crosses context boundary")
            normalized.append(item)
        payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(payload.encode("utf-8")) > 65_536:
            raise ValueError("capture exceeds byte budget")
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        # Acquire the write lock before checking references or active predecessors.
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            if not self._connection.execute(
                "SELECT 1 FROM contexts WHERE context_id = ?", (context_id,)
            ).fetchone():
                return {"status": "not_found", "context_id": context_id}
            previous = self._connection.execute(
                "SELECT * FROM captures WHERE capture_ref = ?", (capture_ref,)
            ).fetchone()
            if previous:
                if previous["context_id"] != context_id or previous["digest"] != digest:
                    raise ValueError("capture reference reused with different contents")
                return {
                    "status": "ok", "context_id": context_id, "duplicate": True,
                    "accepted_ids": json.loads(previous["accepted_ids"]),
                    "superseded_ids": json.loads(previous["superseded_ids"]),
                }
            accepted, superseded = [], []
            for record in normalized:
                predecessor = record["supersedes_id"]
                if predecessor is not None:
                    changed = self._connection.execute(
                        """UPDATE records SET active = 0
                            WHERE id = ? AND context_id = ? AND active = 1 AND kind = ?""",
                        (predecessor, context_id, record["kind"]),
                    ).rowcount
                    if changed != 1:
                        raise ValueError("supersession requires an active same-context, same-kind predecessor")
                    superseded.append(predecessor)
                record_id = "rec_" + secrets.token_hex(16)
                self._insert_record(record_id, context_id, record)
                accepted.append(record_id)
            self._connection.execute(
                "INSERT INTO captures VALUES (?, ?, ?, ?, ?)",
                (capture_ref, context_id, digest, json.dumps(accepted), json.dumps(superseded)),
            )
        return {
            "status": "ok", "context_id": context_id, "duplicate": False,
            "accepted_ids": accepted, "superseded_ids": superseded,
        }

    def recall(
        self,
        context_id: str | None = None,
        query: str = "",
        *,
        max_bytes: int = DEPLOYABLE_MAX_PACK_BYTES,
        use_lexical: bool = True,
        resolved: bool = True,
    ) -> RecallResult:
        empty = serialize_pack([])
        if type(max_bytes) is not int or not len(empty.encode("utf-8")) <= max_bytes <= DEPLOYABLE_MAX_PACK_BYTES:
            raise ValueError("invalid pack byte budget")
        if not isinstance(query, str) or type(resolved) is not bool or type(use_lexical) is not bool:
            raise ValueError("invalid recall arguments")
        if not resolved:
            return RecallResult(empty, (), False, self.index_mode, status="unresolved")
        created = context_id is None
        if created:
            with self._connection:
                for _ in range(8):
                    candidate = _new_context_id()
                    try:
                        self._connection.execute("INSERT INTO contexts(context_id) VALUES (?)", (candidate,))
                    except sqlite3.IntegrityError:
                        continue
                    context_id = candidate
                    break
                else:
                    raise RuntimeError("context ID allocation failed")
        else:
            _validate_context_id(context_id)
            if not self._connection.execute(
                "SELECT 1 FROM contexts WHERE context_id = ?", (context_id,)
            ).fetchone():
                return RecallResult(empty, (), False, self.index_mode, context_id, False, "not_found")
        active = [dict(row) for row in self._connection.execute(
            "SELECT * FROM records WHERE context_id = ? AND active = 1 ORDER BY sequence", (context_id,)
        )]
        positions = {record["id"]: record["sequence"] for record in active}
        mandatory = sorted(
            (record for record in active if record["kind"] in MANDATORY_ORDER),
            key=lambda record: (MANDATORY_ORDER[record["kind"]], positions[str(record["id"])]),
        )
        query_terms = _terms(query)
        optional = [record for record in active if record["kind"] not in MANDATORY_ORDER]
        if use_lexical:
            # Binary-term BM25: duplicate words cannot inflate a record's score.
            # Statistics belong exclusively to active records in this exact Context.
            record_terms = {record["id"]: frozenset(record["terms"].split()) for record in active}
            average_length = sum(map(len, record_terms.values())) / max(1, len(active)) or 1.0
            document_frequency = {term: sum(term in terms for terms in record_terms.values())
                                  for term in query_terms}
            inverse_frequency = {
                term: math.log1p((len(active) - frequency + 0.5) / (frequency + 0.5))
                for term, frequency in document_frequency.items()
            }
            if self.index_mode == "fts5" and query_terms:
                expression = " OR ".join(f'"{term}"' for term in sorted(query_terms))
                # Keep FTS first: reversing this join repeats MATCH for every record.
                matched = {row[0] for row in self._connection.execute(
                    """SELECT r.id FROM poc_record_terms CROSS JOIN records AS r
                        ON r.sequence = poc_record_terms.rowid
                        WHERE poc_record_terms MATCH ? AND r.context_id = ? AND r.active = 1""",
                    (expression, context_id),
                )}
            else:
                matched = {record["id"] for record in optional}

            def relevance(record: dict) -> float:
                if record["id"] not in matched:
                    return 0.0
                terms = record_terms[record["id"]]
                normalization = 2.2 / (1.0 + 1.2 * (0.25 + 0.75 * len(terms) / average_length))
                return sum(inverse_frequency[term] for term in sorted(query_terms & terms)) * normalization

            if not query_terms:
                optional.sort(key=lambda record: (-positions[record["id"]], record["id"]))
        else:
            optional.sort(
                key=lambda record: (-positions[str(record["id"])], str(record["id"]))
            )
        selected: list[dict] = []
        selected_bytes = len(empty.encode("utf-8"))
        record_bytes = {record["id"]: len(_record_line(record).encode("utf-8")) for record in active}

        def fits(record: dict) -> bool:
            separator_bytes = 1 if selected else 0
            return selected_bytes + separator_bytes + record_bytes[record["id"]] <= max_bytes

        for record in mandatory:
            if not fits(record):
                return RecallResult(empty, (), True, self.index_mode, context_id, created, "overflow")
            selected_bytes += (1 if selected else 0) + record_bytes[record["id"]]
            selected.append(record)
        if use_lexical and query_terms:
            # Choose useful marginal information: BM25 relevance is discounted by
            # the greatest Jaccard similarity to an optional record already packed.
            # Mandatory authority boundaries never compete for this diversity budget.
            relevance_scores = {record["id"]: relevance(record) for record in optional}
            redundancy = {record["id"]: 0.0 for record in optional}
            while optional:
                optional = [record for record in optional if fits(record)]
                if not optional:
                    break
                record = min(optional, key=lambda item: (
                    -relevance_scores[item["id"]] * (1.0 - redundancy[item["id"]]),
                    -positions[item["id"]], item["id"],
                ))
                selected_bytes += (1 if selected else 0) + record_bytes[record["id"]]
                selected.append(record)
                optional.remove(record)
                chosen_terms = record_terms[record["id"]]
                for item in optional:
                    if relevance_scores[item["id"]] == 0.0:
                        continue
                    terms = record_terms[item["id"]]
                    similarity = len(terms & chosen_terms) / max(1, len(terms | chosen_terms))
                    redundancy[item["id"]] = max(redundancy[item["id"]], similarity)
        else:
            for record in optional:
                if fits(record):
                    selected_bytes += (1 if selected else 0) + record_bytes[record["id"]]
                    selected.append(record)
        return RecallResult(
            serialize_pack(selected),
            tuple(str(record["id"]) for record in selected),
            False,
            self.index_mode,
            context_id,
            created,
        )
