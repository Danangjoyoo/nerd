from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA_VERSION = "shared-behavior-memory/v1"
TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(sorted(set(TOKEN_RE.findall(value.lower()))))


def _string_tuple(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(str(value).strip() for value in values if str(value).strip())


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _overlap_score(command: Sequence[str], phrase: Sequence[str]) -> float:
    command_set = set(command)
    phrase_set = set(phrase)
    if not command_set or not phrase_set:
        return 0.0
    return len(command_set & phrase_set) / len(phrase_set)


class SharedBehaviorMemory:
    """Small SQLite-backed experimental behavioral evidence store."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path, timeout=10.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA busy_timeout=10000")
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SharedBehaviorMemory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _create_schema(self) -> None:
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS behaviors (
                    behavior_id TEXT PRIMARY KEY,
                    cue_phrases_json TEXT NOT NULL,
                    action TEXT NOT NULL,
                    tools_json TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    skills_json TEXT NOT NULL,
                    invalid_signals_json TEXT NOT NULL,
                    source_agent TEXT NOT NULL,
                    source_repository TEXT NOT NULL,
                    verification_id TEXT NOT NULL,
                    verified INTEGER NOT NULL CHECK (verified = 1),
                    recorded_order INTEGER NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS recall_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trial_id TEXT NOT NULL,
                    consumer_agent TEXT NOT NULL,
                    consumer_repository TEXT NOT NULL,
                    command_cues_json TEXT NOT NULL,
                    output_signal TEXT,
                    status TEXT NOT NULL CHECK (status IN ('recalled', 'abstained')),
                    behavior_id TEXT,
                    score REAL NOT NULL,
                    reject_output INTEGER NOT NULL,
                    FOREIGN KEY (behavior_id) REFERENCES behaviors(behavior_id)
                );
                """
            )
            current = self.connection.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
            if current is None:
                self.connection.execute(
                    "INSERT INTO metadata(key, value) VALUES('schema_version', ?)",
                    (SCHEMA_VERSION,),
                )
            elif current["value"] != SCHEMA_VERSION:
                raise RuntimeError(
                    f"unsupported schema {current['value']!r}; expected {SCHEMA_VERSION!r}"
                )

    def record(
        self,
        *,
        behavior_id: str,
        cue_phrases: Iterable[str],
        action: str,
        tools: Iterable[str],
        steps: Iterable[str],
        skills: Iterable[str],
        invalid_signals: Iterable[str],
        source_agent: str,
        source_repository: str,
        verification_id: str,
        verified: bool,
    ) -> dict[str, Any]:
        behavior_id = behavior_id.strip()
        cues = _string_tuple(cue_phrases)
        tools_tuple = _string_tuple(tools)
        steps_tuple = _string_tuple(steps)
        skills_tuple = _string_tuple(skills)
        invalid_tuple = _string_tuple(invalid_signals)
        if not verified:
            raise ValueError("only independently verified behavior may be recorded")
        if not behavior_id or not cues or not action.strip() or not steps_tuple:
            raise ValueError("behavior_id, cue_phrases, action, and steps are required")
        if any(not _tokens(cue) for cue in cues):
            raise ValueError("every cue phrase must contain a searchable token")
        if not source_agent.strip() or not source_repository.strip() or not verification_id.strip():
            raise ValueError("source provenance and verification_id are required")

        payload = {
            "behavior_id": behavior_id,
            "cue_phrases_json": _canonical_json(list(cues)),
            "action": action.strip(),
            "tools_json": _canonical_json(list(tools_tuple)),
            "steps_json": _canonical_json(list(steps_tuple)),
            "skills_json": _canonical_json(list(skills_tuple)),
            "invalid_signals_json": _canonical_json(list(invalid_tuple)),
            "source_agent": source_agent.strip(),
            "source_repository": source_repository.strip(),
            "verification_id": verification_id.strip(),
            "verified": 1,
        }
        existing = self.connection.execute(
            "SELECT * FROM behaviors WHERE behavior_id = ?", (behavior_id,)
        ).fetchone()
        if existing is not None:
            comparable = {key: existing[key] for key in payload}
            if comparable != payload:
                raise ValueError(f"behavior {behavior_id!r} already exists with different data")
            return self._decode_behavior(existing)

        next_order = self.connection.execute(
            "SELECT COALESCE(MAX(recorded_order), 0) + 1 FROM behaviors"
        ).fetchone()[0]
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO behaviors(
                    behavior_id, cue_phrases_json, action, tools_json, steps_json,
                    skills_json, invalid_signals_json, source_agent,
                    source_repository, verification_id, verified, recorded_order
                ) VALUES(
                    :behavior_id, :cue_phrases_json, :action, :tools_json,
                    :steps_json, :skills_json, :invalid_signals_json,
                    :source_agent, :source_repository, :verification_id,
                    :verified, :recorded_order
                )
                """,
                {**payload, "recorded_order": next_order},
            )
        row = self.connection.execute(
            "SELECT * FROM behaviors WHERE behavior_id = ?", (behavior_id,)
        ).fetchone()
        assert row is not None
        return self._decode_behavior(row)

    def _decode_behavior(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "behavior_id": row["behavior_id"],
            "cue_phrases": json.loads(row["cue_phrases_json"]),
            "action": row["action"],
            "tools": json.loads(row["tools_json"]),
            "steps": json.loads(row["steps_json"]),
            "skills": json.loads(row["skills_json"]),
            "invalid_signals": json.loads(row["invalid_signals_json"]),
            "source_agent": row["source_agent"],
            "source_repository": row["source_repository"],
            "verification_id": row["verification_id"],
            "verified": bool(row["verified"]),
            "recorded_order": row["recorded_order"],
        }

    def behaviors(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM behaviors ORDER BY recorded_order, behavior_id"
        ).fetchall()
        return [self._decode_behavior(row) for row in rows]

    def behavior_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM behaviors").fetchone()[0])

    def recall(
        self,
        *,
        command: str,
        consumer_agent: str,
        consumer_repository: str,
        trial_id: str = "adhoc",
        output_signal: str | None = None,
        minimum_score: float = 0.75,
    ) -> dict[str, Any]:
        command_tokens = _tokens(command)
        candidates: list[tuple[float, dict[str, Any]]] = []
        for behavior in self.behaviors():
            score = max(
                _overlap_score(command_tokens, _tokens(phrase))
                for phrase in behavior["cue_phrases"]
            )
            candidates.append((score, behavior))
        candidates.sort(key=lambda item: (-item[0], item[1]["behavior_id"]))

        top_score = candidates[0][0] if candidates else 0.0
        ambiguous = (
            len(candidates) > 1
            and top_score >= minimum_score
            and candidates[1][0] == top_score
        )
        selected = (
            candidates[0][1]
            if candidates and top_score >= minimum_score and not ambiguous
            else None
        )
        normalized_signal = output_signal.strip() if output_signal else None
        reject_output = bool(
            selected
            and normalized_signal
            and normalized_signal in selected["invalid_signals"]
        )
        result: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": "recalled" if selected else "abstained",
            "behavior_id": selected["behavior_id"] if selected else None,
            "score": round(top_score, 6),
            "action": selected["action"] if selected else None,
            "tools": selected["tools"] if selected else [],
            "steps": selected["steps"] if selected else [],
            "skills": selected["skills"] if selected else [],
            "reject_output": reject_output,
            "matched_invalid_signal": normalized_signal if reject_output else None,
            "source_agent": selected["source_agent"] if selected else None,
            "source_repository": selected["source_repository"] if selected else None,
            "consumer_agent": consumer_agent,
            "consumer_repository": consumer_repository,
        }
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO recall_events(
                    trial_id, consumer_agent, consumer_repository, command_cues_json,
                    output_signal, status, behavior_id, score, reject_output
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trial_id,
                    consumer_agent,
                    consumer_repository,
                    _canonical_json(list(command_tokens)),
                    normalized_signal,
                    result["status"],
                    result["behavior_id"],
                    top_score,
                    int(reject_output),
                ),
            )
        return result

    def recall_events(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM recall_events ORDER BY event_id"
        ).fetchall()
        return [dict(row) for row in rows]

    def schema_manifest(self) -> dict[str, list[str]]:
        tables = [
            row["name"]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        return {
            table: [
                row["name"]
                for row in self.connection.execute(f"PRAGMA table_info({table})")
            ]
            for table in tables
        }


def _write_json(value: Any, output: Path | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(text, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Experimental shared behavioral memory")
    parser.add_argument("--db", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init")
    subparsers.add_parser("schema")

    export = subparsers.add_parser("export")
    export.add_argument("--output", type=Path)

    record = subparsers.add_parser("record")
    record.add_argument("--behavior-id", required=True)
    record.add_argument("--cue", action="append", required=True)
    record.add_argument("--action", required=True)
    record.add_argument("--tool", action="append", default=[])
    record.add_argument("--step", action="append", required=True)
    record.add_argument("--skill", action="append", default=[])
    record.add_argument("--invalid-signal", action="append", default=[])
    record.add_argument("--source-agent", required=True)
    record.add_argument("--source-repository", required=True)
    record.add_argument("--verification-id", required=True)

    recall = subparsers.add_parser("recall")
    recall.add_argument("--command-text", required=True)
    recall.add_argument("--trial-id", default="adhoc")
    recall.add_argument("--consumer-agent", required=True)
    recall.add_argument("--consumer-repository", required=True)
    recall.add_argument("--output-signal")
    recall.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    with SharedBehaviorMemory(args.db) as memory:
        if args.command == "init":
            _write_json({"schema_version": SCHEMA_VERSION, "behavior_count": memory.behavior_count()}, None)
        elif args.command == "schema":
            _write_json(memory.schema_manifest(), None)
        elif args.command == "export":
            _write_json({"schema_version": SCHEMA_VERSION, "behaviors": memory.behaviors()}, args.output)
        elif args.command == "record":
            result = memory.record(
                behavior_id=args.behavior_id,
                cue_phrases=args.cue,
                action=args.action,
                tools=args.tool,
                steps=args.step,
                skills=args.skill,
                invalid_signals=args.invalid_signal,
                source_agent=args.source_agent,
                source_repository=args.source_repository,
                verification_id=args.verification_id,
                verified=True,
            )
            _write_json(result, None)
        elif args.command == "recall":
            result = memory.recall(
                command=args.command_text,
                trial_id=args.trial_id,
                consumer_agent=args.consumer_agent,
                consumer_repository=args.consumer_repository,
                output_signal=args.output_signal,
            )
            _write_json(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
