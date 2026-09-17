"""Prospective full-payload selection under a pinned native decoded-text bound.

Private prerequisite only: no production/core integration or empirical pass.
Codex rust-v0.153.4 McpToolOutput::response_payload uses Duration.as_secs_f64
and fixed .4 formatting. Duration's entire domain rounds no higher than 2**64
seconds: 20 integer digits + decimal/four digits + 28 literal bytes = 53.
Regular structured JSON text only; code mode, media and truncation are excluded.
"""
from dataclasses import dataclass
import json
import math
import re

from deployable_response import (AUTHORITY, MAX_RESPONSE_BYTES, BudgetTooSmall, ContractError,
                                conflicts, json_bytes, mcp_result, recalled_record, text,
                                validate_capture_request)
from structured import MANDATORY_ORDER, _terms, _validate_context_id


CLIENT_VERSION = "codex-cli 0.153.4"
WRAPPER_RESERVED_BYTES = 53
MAX_CAPTURE_ARGUMENT_BYTES = 256 * 1024
MAX_DURATION_TEXT = "18446744073709551616.0000"
STRATEGIES = {"typed_lexical", "typed_recency", "none"}


def validate_bounded_capture(request, *, existing_record_contexts, max_bytes=MAX_CAPTURE_ARGUMENT_BYTES):
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_CAPTURE_ARGUMENT_BYTES:
        raise ContractError("invalid lower-only capture argument budget")
    return validate_capture_request(request, existing_record_contexts=existing_record_contexts, max_capture_bytes=max_bytes)


@dataclass(frozen=True)
class NativeResponse:
    payload: dict
    mcp_result: dict
    payload_json: bytes
    budgeted_output_bytes: int
    attempted_budgeted_bytes: int
    max_bytes: int
    wrapper_reserved_bytes: int = WRAPPER_RESERVED_BYTES

    @property
    def transport_json_bytes(self):
        return len(json_bytes(self.mcp_result))


def _metadata(context_id, *, status, created, strategy, conflict_groups):
    try:
        _validate_context_id(context_id)
    except ValueError:
        raise ContractError("invalid context ID") from None
    if not isinstance(status, str) or status not in {"ok", "not_found", "overflow", "unresolved"} or type(created) is not bool:
        raise ContractError("invalid recall state")
    if not isinstance(strategy, str) or strategy not in STRATEGIES:
        raise ContractError("invalid retrieval strategy")
    return {"status": status, "created": created, "context_id": context_id, "records": [],
            "conflicts": conflict_groups, "overflow": status == "overflow", "authority": AUTHORITY,
            "retrieval_path": strategy, "serialized_bytes": 0, "estimated_tokens": 0}


def _finalize(payload, max_bytes):
    for _ in range(32):
        encoded = json_bytes(payload)
        size = len(encoded)
        estimate = (size + WRAPPER_RESERVED_BYTES + 3) // 4  # Not measured model tokens.
        if (payload["serialized_bytes"], payload["estimated_tokens"]) == (size, estimate):
            bound = size + WRAPPER_RESERVED_BYTES
            # Freeze the object order too: both canonical JSON-RPC serialization
            # and a serializer preserving dict order now deliver identical text.
            canonical = json.loads(encoded)
            return NativeResponse(canonical, mcp_result(canonical), encoded, bound, bound, max_bytes)
        payload = {**payload, "serialized_bytes": size, "estimated_tokens": estimate}
    raise ContractError("payload byte accounting did not converge")


def serialize_native_recall(*, context_id, records, created=False, status="ok", strategy="typed_lexical",
                            conflict_groups=(), known_record_contexts=None, max_bytes=MAX_RESPONSE_BYTES):
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_RESPONSE_BYTES:
        raise ContractError("invalid lower-only native text budget")
    if not isinstance(records, list):
        raise ContractError("invalid recall records")
    if created and records:
        raise ContractError("fresh context must be empty")
    if status != "ok" and (records or created or conflict_groups):
        raise ContractError("non-success response cannot hydrate or create")
    selected = [recalled_record(record, context_id) for record in records]
    if len({record["id"] for record in selected}) != len(selected):
        raise ContractError("duplicate recalled record ID")
    known = known_record_contexts if known_record_contexts is not None else {record["id"]: context_id for record in selected}
    groups = conflicts(list(conflict_groups), known, context_id)
    payload = _metadata(context_id, status=status, created=created, strategy=strategy, conflict_groups=groups)
    payload["records"] = selected
    response = _finalize(payload, max_bytes)
    if response.budgeted_output_bytes <= max_bytes:
        return response
    overflow = _finalize({**payload, "status": "overflow", "overflow": True, "records": [], "conflicts": []}, max_bytes)
    if overflow.budgeted_output_bytes > max_bytes:
        raise BudgetTooSmall("budget cannot fit the complete native control response")
    return NativeResponse(overflow.payload, overflow.mcp_result, overflow.payload_json, overflow.budgeted_output_bytes,
                          response.budgeted_output_bytes, max_bytes)


def verify_native_output(response, output_text, *, client_version=CLIENT_VERSION):
    """Verify actual native text after delivery; missing/truncated/changed data fails.

Return actual text size separately from the reserved upper bound. This is not
all-request billing or upstream tokenizer evidence. Call/routing/wire metadata
remains separately retained by the surrounding experiment.
"""
    if client_version != CLIENT_VERSION or not isinstance(output_text, str):
        raise ContractError("unsupported native output contract")
    match = re.match(r"Wall time: ([0-9]+)\.([0-9]{4}) seconds\nOutput:\n", output_text)
    if match is None or int(match[1]) > 2 ** 64 or (int(match[1]) == 2 ** 64 and match[2] != "0000"):
        raise ContractError("unsupported native output prefix")
    if len(match[0].encode()) > WRAPPER_RESERVED_BYTES:
        raise ContractError("native prefix exceeds reserved bytes")
    expected = json.dumps(response.payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if output_text[match.end():] != expected:
        raise ContractError("native output is missing, truncated, or changed")
    size = len(output_text.encode())
    if response.payload["serialized_bytes"] != len(response.payload_json) or response.payload_json != json_bytes(response.payload):
        raise ContractError("payload size or content differs")
    if response.budgeted_output_bytes != len(response.payload_json) + WRAPPER_RESERVED_BYTES:
        raise ContractError("native byte reservation differs")
    if not size <= response.budgeted_output_bytes <= response.max_bytes <= MAX_RESPONSE_BYTES:
        raise ContractError("native output exceeds its byte budget")
    return {"payload_json_bytes": len(response.payload_json), "actual_native_output_bytes": size,
            "wrapper_reserved_bytes": WRAPPER_RESERVED_BYTES, "budgeted_output_bytes": response.budgeted_output_bytes,
            "transport_json_bytes": response.transport_json_bytes, "token_measurement": "not_established"}


def _size_with_records(base_size, count, record_bytes):
    size = base_size + record_bytes + max(0, count - 1)
    for _ in range(32):
        estimate = (size + WRAPPER_RESERVED_BYTES + 3) // 4
        corrected = base_size + record_bytes + max(0, count - 1) + len(str(size)) - 1 + len(str(estimate)) - 1
        if corrected == size:
            return size + WRAPPER_RESERVED_BYTES
        size = corrected
    raise ContractError("selection size accounting did not converge")


@dataclass(frozen=True)
class Selection:
    response: NativeResponse
    record_ids: tuple
    index_mode: str


def select_native_response(*, context_id, records, query, index_mode="normalized_scan", matched_ids=None,
                           use_lexical=True, conflict_groups=(), max_bytes=MAX_RESPONSE_BYTES):
    """Same Context-local BM25/novelty/mandatory ordering; only fits() changes.

Input is trusted current store rows in chronological sequence order. No rubric
or required-label fields are read. Only same-Context active rows enter scores.
FTS candidate IDs must come from the real exact-Context MATCH query below.
"""
    _validate_context_id(context_id)
    if (not isinstance(query, str) or type(use_lexical) is not bool or not isinstance(index_mode, str)
            or index_mode not in {"normalized_scan", "fts5"}):
        raise ContractError("invalid selection arguments")
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_RESPONSE_BYTES:
        raise ContractError("invalid lower-only native text budget")
    if not isinstance(records, list):
        raise ContractError("invalid store record rows")
    if any(not isinstance(record, dict) for record in records):
        raise ContractError("invalid store record row")
    active = [record for record in records if record.get("context_id") == context_id and record.get("active") is True]
    projected = {record["id"]: recalled_record(record, context_id) for record in active}
    if len(projected) != len(active):
        raise ContractError("duplicate store record ID")
    positions = {record["id"]: record.get("sequence", index) for index, record in enumerate(active)}
    if any(type(position) is not int for position in positions.values()):
        raise ContractError("invalid record sequence")
    known = {record["id"]: record["context_id"] for record in records}
    groups = conflicts(list(conflict_groups), known, context_id)
    strategy = "typed_lexical" if use_lexical else "typed_recency"
    metadata = _metadata(context_id, status="ok", created=False, strategy=strategy, conflict_groups=groups)
    base_size = len(json_bytes(metadata))
    record_sizes = {key: len(json_bytes(value)) for key, value in projected.items()}
    mandatory = sorted((record for record in active if record["kind"] in MANDATORY_ORDER),
                       key=lambda record: (MANDATORY_ORDER[record["kind"]], positions[record["id"]]))
    optional = [record for record in active if record["kind"] not in MANDATORY_ORDER]
    selected, selected_bytes = list(mandatory), sum(record_sizes[record["id"]] for record in mandatory)
    if _size_with_records(base_size, len(selected), selected_bytes) > max_bytes:
        response = serialize_native_recall(context_id=context_id, records=mandatory, strategy=strategy,
                                           conflict_groups=groups, known_record_contexts=known, max_bytes=max_bytes)
        return Selection(response, (), index_mode)

    def fits(record):
        return _size_with_records(base_size, len(selected) + 1, selected_bytes + record_sizes[record["id"]]) <= max_bytes

    query_terms = _terms(query)
    if use_lexical and query_terms:
        terms = {record["id"]: frozenset(_terms(record["value"])) for record in active}
        average_length = sum(map(len, terms.values())) / max(1, len(active)) or 1.0
        frequency = {term: sum(term in value for value in terms.values()) for term in query_terms}
        inverse = {term: math.log1p((len(active) - count + 0.5) / (count + 0.5)) for term, count in frequency.items()}
        if index_mode == "fts5" and matched_ids is None:
            raise ContractError("FTS selection requires observed match IDs")
        matched = set(matched_ids) if index_mode == "fts5" else {record["id"] for record in optional}
        scores = {}
        for record in optional:
            identifier = record["id"]
            normalization = 2.2 / (1.0 + 1.2 * (0.25 + 0.75 * len(terms[identifier]) / average_length))
            scores[identifier] = (sum(inverse[term] for term in sorted(query_terms & terms[identifier])) * normalization
                                  if identifier in matched else 0.0)
        redundancy = {record["id"]: 0.0 for record in optional}
        while optional:
            optional = [record for record in optional if fits(record)]
            if not optional:
                break
            record = min(optional, key=lambda item: (-scores[item["id"]] * (1.0 - redundancy[item["id"]]),
                                                     -positions[item["id"]], item["id"]))
            selected.append(record)
            selected_bytes += record_sizes[record["id"]]
            optional.remove(record)
            chosen = terms[record["id"]]
            for item in optional:
                identifier = item["id"]
                if scores[identifier] == 0:
                    continue
                similarity = len(terms[identifier] & chosen) / max(1, len(terms[identifier] | chosen))
                redundancy[identifier] = max(redundancy[identifier], similarity)
    else:
        for record in sorted(optional, key=lambda item: (-positions[item["id"]], item["id"])):
            if fits(record):
                selected.append(record)
                selected_bytes += record_sizes[record["id"]]
    response = serialize_native_recall(context_id=context_id, records=selected, strategy=strategy, conflict_groups=groups,
                                       known_record_contexts=known, max_bytes=max_bytes)
    if response.payload["overflow"] or response.budgeted_output_bytes != _size_with_records(base_size, len(selected), selected_bytes):
        raise ContractError("selection and final serialization disagree")
    return Selection(response, tuple(record["id"] for record in selected), index_mode)


def recall_from_ledger(ledger, *, context_id, query, use_lexical=True, max_bytes=MAX_RESPONSE_BYTES):
    """Read-only bridge for POC SQLite evidence; never creates or captures.

POC SQLite has no anchor persistence. Anchored synthetic rows are exercised by
the pure selector; future storage must persist them rather than strip them.
"""
    _validate_context_id(context_id)
    connection = ledger._connection
    if not connection.execute("SELECT 1 FROM contexts WHERE context_id = ?", (context_id,)).fetchone():
        response = serialize_native_recall(context_id=context_id, records=[], status="not_found", strategy="none", max_bytes=max_bytes)
        return Selection(response, (), ledger.index_mode)
    rows = [dict(row) for row in connection.execute("SELECT * FROM records WHERE context_id = ? AND active = 1 ORDER BY sequence", (context_id,))]
    for row in rows:
        row["active"] = bool(row["active"])
    matches = None
    query_terms = _terms(query)
    if ledger.index_mode == "fts5" and use_lexical and query_terms:
        expression = " OR ".join(f'"{term}"' for term in sorted(query_terms))
        matches = {row[0] for row in connection.execute(
            "SELECT r.id FROM poc_record_terms CROSS JOIN records AS r ON r.sequence = poc_record_terms.rowid "
            "WHERE poc_record_terms MATCH ? AND r.context_id = ? AND r.active = 1", (expression, context_id))}
    return select_native_response(context_id=context_id, records=rows, query=query, index_mode=ledger.index_mode,
                                  matched_ids=matches, use_lexical=use_lexical, max_bytes=max_bytes)
