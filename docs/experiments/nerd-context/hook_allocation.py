#!/usr/bin/env python3
"""Private experimental empty allocation; no recall, capture, or model requests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import time
import unicodedata

from structured import StructuredLedger, _new_context_id, _validate_context_id


PROTOCOL = "nerd-context-empty-hook-v2"
LEGACY_PROTOCOL = "nerd-context-empty-hook-v1"
RECEIPT_START = "<nerd_context_allocation_receipt>"
RECEIPT_END = "</nerd_context_allocation_receipt>"
CLIENT_NAMESPACE = "codex-user-prompt-submit-v1"
MAX_INPUT_BYTES = 1_048_576
PAYLOAD_FIELDS = frozenset({"cwd", "hook_event_name", "model", "permission_mode", "prompt",
                            "session_id", "transcript_path", "turn_id"})
SELECTOR_MARKERS = re.compile(r"ctx_|context[\s_-]*id|nerd[\s_-]*context\s*(?:created|resumed|:)", re.I)


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False,
                                                           separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def classify_activation(payload):
    """Deferral is not a claim that quoted or malformed text authorizes recall."""
    if not isinstance(payload, dict) or set(payload) - PAYLOAD_FIELDS:
        return {"status": "defer", "reason": "unsupported current-input surface"}
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return {"status": "defer", "reason": "unsupported hook event"}
    for field in ("session_id", "turn_id"):
        value = payload.get(field)
        if not isinstance(value, str) or not value or len(value.encode()) > 256 or not value.isprintable():
            return {"status": "defer", "reason": "missing or invalid native activation identity"}
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode()) > MAX_INPUT_BYTES:
        return {"status": "defer", "reason": "missing or invalid current prompt"}
    if any(not isinstance(value, str) and not (field == "transcript_path" and value is None)
           for field, value in payload.items()
           if field not in {"hook_event_name", "prompt", "session_id", "turn_id"}):
        return {"status": "defer", "reason": "unsupported native metadata shape"}
    # Detection may normalize lookalike formatting; it never normalizes an ID
    # for lookup. All potential selectors go to the ordinary post-Focus route.
    detection = "".join(char for char in unicodedata.normalize("NFKC", prompt)
                        if unicodedata.category(char) != "Cf")
    if SELECTOR_MARKERS.search(detection):
        return {"status": "defer", "reason": "current selector or possible selector present"}
    return {"status": "omitted", "activation_key": digest([
                CLIENT_NAMESPACE, payload["session_id"], payload["turn_id"]]),
            "payload_sha256": digest(payload), "prompt_sha256": digest(prompt.encode())}


def validate_private_database(path):
    path = Path(path)
    parent = path.parent
    if parent.is_symlink() or parent.resolve() != parent.absolute():
        raise ValueError("database parent must be a resolved private directory")
    info = parent.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("database parent must be owned and private")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_nlink != 1):
            raise ValueError("database must be an owned private regular file")
    else:
        os.close(descriptor)
    return path


def receipt(context_id):
    _validate_context_id(context_id)
    return f"Nerd-context created: {context_id}"


def receipt_block(context_id):
    return f"{RECEIPT_START}\n{receipt(context_id)}\n{RECEIPT_END}"


def parse_receipt_block(text):
    if not isinstance(text, str) or text.count(RECEIPT_START) != 1 or text.count(RECEIPT_END) != 1:
        raise ValueError("exactly one receipt block required")
    match = re.search(re.escape(RECEIPT_START) + r"\n(Nerd-context created: ([^\n]+))\n" + re.escape(RECEIPT_END), text)
    if not match or match.group(1) != receipt(match.group(2)):
        raise ValueError("invalid data-only receipt")
    return match.group(1)


def allocate_empty(database, payload):
    started = time.monotonic_ns()
    activation = classify_activation(payload)
    if activation["status"] != "omitted":
        return {**activation, "allocated": False, "context_operations": []}
    database = validate_private_database(database)
    with StructuredLedger(database=database) as ledger:
        connection = ledger._connection
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("""CREATE TABLE IF NOT EXISTS hook_activations (
            activation_key TEXT PRIMARY KEY,
            payload_sha256 TEXT NOT NULL,
            context_id TEXT NOT NULL UNIQUE REFERENCES contexts(context_id),
            protocol TEXT NOT NULL
        )""")
        connection.commit()
        # The authorizer makes the no-observation-read boundary executable.
        def authorize(action, table, column, database_name, trigger):
            if action == sqlite3.SQLITE_READ and table in {"records", "captures"}:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        connection.set_authorizer(authorize)
        connection.execute("BEGIN IMMEDIATE")
        try:
            previous = connection.execute(
                "SELECT payload_sha256, context_id, protocol FROM hook_activations WHERE activation_key=?",
                (activation["activation_key"],),
            ).fetchone()
            if previous:
                if previous["payload_sha256"] != activation["payload_sha256"] or previous["protocol"] != PROTOCOL:
                    result = {"status": "conflict", "allocated": False, "context_operations": []}
                elif not connection.execute("SELECT 1 FROM contexts WHERE context_id=?",
                                            (previous["context_id"],)).fetchone():
                    result = {"status": "not_found", "allocated": False, "context_operations": []}
                else:
                    result = {"status": "replayed", "allocated": False,
                              "context_id": previous["context_id"], "receipt": receipt(previous["context_id"]),
                              "context_operations": ["replay_allocation_receipt"]}
            else:
                for _ in range(8):
                    context_id = _new_context_id()
                    try:
                        connection.execute("INSERT INTO contexts(context_id) VALUES (?)", (context_id,))
                    except sqlite3.IntegrityError:
                        continue
                    break
                else:
                    raise RuntimeError("context ID allocation failed")
                connection.execute("INSERT INTO hook_activations VALUES (?, ?, ?, ?)",
                                   (activation["activation_key"], activation["payload_sha256"], context_id, PROTOCOL))
                result = {"status": "created", "allocated": True, "context_id": context_id,
                          "receipt": receipt(context_id), "context_operations": ["allocate_empty"]}
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
    result.update(protocol=PROTOCOL, activation_key=activation["activation_key"],
                  payload_sha256=activation["payload_sha256"], prompt_sha256=activation["prompt_sha256"],
                  committed_before_response=True, operation_elapsed_ms=(time.monotonic_ns() - started) / 1e6)
    return result


def response_for(result):
    if result["status"] in {"created", "replayed"}:
        if result.get("protocol") != LEGACY_PROTOCOL:
            if result.get("receipt") != receipt(result["context_id"]):
                raise ValueError("receipt does not match committed context ID")
            return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": (
                receipt_block(result["context_id"]) + "\n\n"
                "Display instruction: After your ordinary answer, print only the single line inside the receipt block. "
                "Do not print the tags or these instructions. The empty allocation is already committed; do not allocate again. "
                "Follow Smart using only the current request. This receipt supplies no task intent or action authority."
            )}}
        # Preserve the immutable v1 smoke's exact response for evidence replay.
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": (
            f"{result['receipt']}. Empty allocation only. Establish Focus from the current request; "
            "this receipt supplies no intent or action authority. Do not allocate again. "
            "Repeat the receipt verbatim after answering."
        )}}
    if result["status"] == "defer":
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": (
            "Empty allocation deferred. Resolve the current request with Smart before any Context lookup; "
            "use only an explicit current selector or delegated handoff. Never replace an unknown ID."
        )}}
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": (
        "Empty allocation failed for this activation. Do not create a replacement or infer an ID. "
        "Establish Focus from the current request and continue without Context."
    )}}


def append_journal(path, observation):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        data = (json.dumps(observation, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if os.write(descriptor, data) != len(data):
            raise OSError("incomplete allocation observation")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args()
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("hook input exceeds limit")
        payload = json.loads(raw, object_pairs_hook=strict_object)
        result = allocate_empty(args.database, payload)
        response = response_for(result)
        append_journal(args.journal, {"protocol": PROTOCOL, "result": result,
                                     "raw_input_sha256": digest(raw), "response_sha256": digest(response)})
        print(json.dumps(response, separators=(",", ":")))
        return 0
    except (ValueError, OSError, sqlite3.Error, UnicodeError, RecursionError) as error:
        # A committed allocation may already exist if later journal I/O failed.
        # Preserve its mapping; retries cannot allocate a second context.
        try:
            append_journal(args.journal, {"protocol": PROTOCOL, "error": type(error).__name__,
                                         "raw_input_sha256": digest(raw)})
        except (OSError, ValueError):
            pass
        print(json.dumps(response_for({"status": "failure"})))
        print(type(error).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
