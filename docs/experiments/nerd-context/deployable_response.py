"""Prospective full Context response contract; not the existing POC serializer.

All rendering requires an explicit client projection. A transport JSON size is
not evidence of the model-visible projection. This module never changes the
old ledger, fixtures, ranker, capture implementation, or verdict.

Required IDs/source refs are inline on records; no redundant root arrays.
Record status/revision/timestamps remain in inspection/audit storage. Active
recall includes ID, provenance, value, per-record authority and every supplied
anchor. Conflicts identify unresolved same-Context record pairs/groups.
"""

from dataclasses import dataclass
import json
from pathlib import PurePosixPath
import re
from typing import Callable

from structured import RECORD_KINDS, RECORD_SOURCES, _validate_context_id


CONTRACT_VERSION = "full-context-response-proposal-v1"
MAX_RESPONSE_BYTES = 2_048
MAX_CAPTURE_RECORDS = 20
AUTHORITY = "untrusted_context"
MODEL_TOKEN_MEASUREMENT = "not_established"
Projection = Callable[[dict], bytes]


class ContractError(ValueError):
    """Fixed public messages never interpolate IDs or stored values."""


class BudgetTooSmall(ContractError):
    pass


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def text(value, *, limit, label):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ContractError("invalid " + label)
    try:
        size = len(value.encode())
    except UnicodeError:
        raise ContractError("invalid " + label) from None
    if size > limit:
        raise ContractError("invalid " + label)
    return value


def record_id(value):
    return text(value, limit=128, label="record ID")


def anchors(value):
    if not isinstance(value, list) or len(value) > 4:
        raise ContractError("invalid anchors")
    result = []
    for anchor in value:
        if not isinstance(anchor, dict) or set(anchor) - {"path", "symbol", "sha256"} or "path" not in anchor:
            raise ContractError("invalid anchor shape")
        path = text(anchor["path"], limit=512, label="anchor path")
        parts = path.split("/")
        if (PurePosixPath(path).is_absolute() or "\\" in path or ":" in path
                or path.startswith("~") or any(part in {"", ".", ".."} for part in parts)
                or any(ord(char) < 32 or ord(char) == 127 for char in path)):
            raise ContractError("unsafe anchor path")
        item = {"path": path}
        if "symbol" in anchor:
            symbol = text(anchor["symbol"], limit=256, label="anchor symbol")
            if any(ord(char) < 32 or ord(char) == 127 for char in symbol):
                raise ContractError("invalid anchor symbol")
            item["symbol"] = symbol
        if "sha256" in anchor:
            value_hash = anchor["sha256"]
            if not isinstance(value_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", value_hash):
                raise ContractError("invalid anchor hash")
            item["sha256"] = value_hash
        result.append(item)
    return result


def capture_record(record):
    required = {"kind", "value", "source", "source_ref"}
    if not isinstance(record, dict) or not required <= set(record) or set(record) - required - {"anchors", "supersedes_id"}:
        raise ContractError("invalid capture record shape")
    if not isinstance(record["kind"], str) or record["kind"] not in RECORD_KINDS:
        raise ContractError("invalid record kind")
    if not isinstance(record["source"], str) or record["source"] not in RECORD_SOURCES:
        raise ContractError("invalid record source")
    result = {"kind": record["kind"], "value": text(record["value"], limit=8_192, label="record value"),
              "source": record["source"], "source_ref": text(record["source_ref"], limit=256, label="source reference")}
    if "anchors" in record:
        result["anchors"] = anchors(record["anchors"])
    if "supersedes_id" in record:
        result["supersedes_id"] = record_id(record["supersedes_id"])
    return result


def validate_capture_request(request, *, existing_record_contexts, max_capture_bytes):
    """Prevalidate the whole request before writes; preserve anchors verbatim.

The plan never set an aggregate capture-byte limit. It must be explicitly
provided/frozen by a future caller; this helper does not invent that limit.
Existing POC capture cannot persist anchors, so callers must not strip them to
force acceptance. A future persistence adapter must implement this schema.
"""
    if not isinstance(request, dict) or set(request) != {"context_id", "records", "capture_ref"}:
        raise ContractError("invalid capture request shape")
    try:
        context_id = _validate_context_id(request["context_id"])
    except ValueError:
        raise ContractError("invalid context ID") from None
    if type(max_capture_bytes) is not int or max_capture_bytes <= 0:
        raise ContractError("aggregate capture byte limit must be explicit")
    records = request["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_CAPTURE_RECORDS:
        raise ContractError("capture accepts one through twenty records")
    result = {"context_id": context_id, "capture_ref": text(request["capture_ref"], limit=256, label="capture reference"),
              "records": [capture_record(record) for record in records]}
    superseded = []
    for record in result["records"]:
        if "supersedes_id" in record:
            previous = record["supersedes_id"]
            if existing_record_contexts.get(previous) != context_id or previous in superseded:
                raise ContractError("invalid same-context supersession")
            superseded.append(previous)
    if len(json_bytes(result)) > max_capture_bytes:
        raise ContractError("capture exceeds aggregate byte limit")
    return result


def recalled_record(record, context_id):
    if not isinstance(record, dict) or record.get("context_id") != context_id:
        raise ContractError("record belongs to a different context")
    if record.get("active") is not True:
        raise ContractError("recall accepts only active records")
    # Input may contain audit/fixture metadata. It is never a ranking feature
    # or output field; only the explicitly projected contract is serialized.
    base = capture_record({key: record[key] for key in ("kind", "value", "source", "source_ref", "anchors") if key in record})
    return {"id": record_id(record.get("id")), **base, "authority": AUTHORITY}


def conflicts(value, known_record_contexts, context_id):
    if not isinstance(value, list):
        raise ContractError("invalid conflicts")
    result = []
    for conflict in value:
        if not isinstance(conflict, dict) or set(conflict) != {"record_ids"}:
            raise ContractError("invalid conflict shape")
        identifiers = conflict["record_ids"]
        if not isinstance(identifiers, list) or len(identifiers) < 2:
            raise ContractError("conflict requires at least two records")
        identifiers = [record_id(value) for value in identifiers]
        if len(set(identifiers)) != len(identifiers) or any(known_record_contexts.get(value) != context_id for value in identifiers):
            raise ContractError("invalid same-context conflict")
        result.append({"record_ids": identifiers})
    return result


def mcp_result(payload):
    return {"content": [{"type": "text", "text": json_bytes(payload).decode()}],
            "structuredContent": payload, "isError": payload["status"] == "overflow"}


def transport_json_projection(result):
    """Diagnostic transport projection only; not proof of native visibility."""
    return json_bytes(result)


def observed_codex_http_projection(*, call_id, output_id, wall_seconds):
    """Replay the observed Codex 0.153.4 regular Responses HTTP projection.

Two synthetic-provider observations verified success and isError results:
structuredContent is forwarded once, with a timing header and output item
identity. These fields are added by the client AFTER the server responds.
Supplying known fields permits exact replay/diagnosis; it does not establish
a production server-side reservation, other transports, or model token count.
No unmeasured worst-case metadata length is silently assumed here.
"""
    for value in (call_id, output_id):
        text(value, limit=256, label="observed native item identifier")
    if not isinstance(wall_seconds, str) or not re.fullmatch(r"[0-9]+\.[0-9]{4}", wall_seconds):
        raise ContractError("invalid observed native wall time")

    def project(result):
        if not isinstance(result, dict) or set(result) != {"content", "structuredContent", "isError"}:
            raise ContractError("unverified native response shape")
        content, payload = result["content"], result["structuredContent"]
        if (not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict)
                or set(content[0]) != {"type", "text"} or content[0]["type"] != "text"
                or not isinstance(payload, dict) or type(result["isError"]) is not bool):
            raise ContractError("unverified native response shape")
        try:
            identical = content[0]["text"] == json_bytes(payload).decode()
        except (ValueError, TypeError, UnicodeError):
            raise ContractError("invalid structured response") from None
        if not identical:
            raise ContractError("structured and text response differ")
        # Preserve structured object order, as the actual native output does.
        payload_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return json_bytes({"type": "function_call_output", "call_id": call_id, "id": output_id,
                           "output": "Wall time: " + wall_seconds + " seconds\nOutput:\n" + payload_text})

    return project


@dataclass(frozen=True)
class SerializedResponse:
    payload: dict
    mcp_result: dict
    model_visible_bytes: bytes
    attempted_bytes: int
    projection_name: str
    token_measurement: str = MODEL_TOKEN_MEASUREMENT


def finalize(payload, project, projection_name):
    """Count self-reported size/estimate fields in the complete projection."""
    payload = {**payload, "serialized_bytes": 0, "estimated_tokens": 0}
    for _ in range(32):
        result = mcp_result(payload)
        rendered = project(result)
        if not isinstance(rendered, bytes):
            raise ContractError("client projection must return exact bytes")
        size = len(rendered)
        estimate = (size + 3) // 4  # Diagnostic heuristic; never a measured token gate.
        if (payload["serialized_bytes"], payload["estimated_tokens"]) == (size, estimate):
            return SerializedResponse(payload, result, rendered, size, projection_name)
        payload = {**payload, "serialized_bytes": size, "estimated_tokens": estimate}
    raise ContractError("serialized size did not converge")


def serialize_recall(*, context_id, records, created=False, status="ok", retrieval_path="normalized_scan",
                     unresolved_conflicts=(), known_record_contexts=None, project, projection_name, max_bytes=MAX_RESPONSE_BYTES):
    """Serialize all selected facts or an explicit empty overflow response.

No record, anchor, conflict, or mandatory fact is silently clipped. Candidate
selection must budget against this helper before calling it; this function
does not substitute a different ranker or weaken fixture requirements.
"""
    try:
        _validate_context_id(context_id)
    except ValueError:
        raise ContractError("invalid context ID") from None
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_RESPONSE_BYTES:
        raise ContractError("invalid lower-only response budget")
    if type(created) is not bool or not isinstance(status, str) or status not in {"ok", "not_found", "overflow", "unresolved"}:
        raise ContractError("invalid recall state")
    if not isinstance(retrieval_path, str) or retrieval_path not in {"normalized_scan", "fts5", "none"}:
        raise ContractError("invalid retrieval path")
    if not isinstance(records, list):
        raise ContractError("invalid recall records")
    if created and records:
        raise ContractError("fresh context must be empty")
    if status != "ok" and (records or created or unresolved_conflicts):
        raise ContractError("non-success response cannot hydrate or create")
    selected = [recalled_record(record, context_id) for record in records]
    if len({record["id"] for record in selected}) != len(selected):
        raise ContractError("duplicate recalled record ID")
    known = known_record_contexts if known_record_contexts is not None else {record["id"]: context_id for record in selected}
    projected_conflicts = conflicts(list(unresolved_conflicts), known, context_id)
    payload = {"status": status, "created": created, "context_id": context_id, "records": selected,
               "conflicts": projected_conflicts, "overflow": status == "overflow",
               "authority": AUTHORITY, "retrieval_path": retrieval_path}
    rendered = finalize(payload, project, projection_name)
    if len(rendered.model_visible_bytes) <= max_bytes:
        return rendered
    # Explicit abstention: no partial successful hydration or missing-boundary
    # concealment. Detailed conflict/record data is unavailable in this state.
    overflow = {**payload, "status": "overflow", "records": [], "conflicts": [], "overflow": True}
    bounded = finalize(overflow, project, projection_name)
    if len(bounded.model_visible_bytes) > max_bytes:
        raise BudgetTooSmall("budget cannot fit the complete control envelope")
    return SerializedResponse(bounded.payload, bounded.mcp_result, bounded.model_visible_bytes,
                              len(rendered.model_visible_bytes), projection_name)
