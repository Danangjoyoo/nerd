# Prospective full response contract

This private prerequisite is not the production implementation or a benchmark
pass. The existing serializer, ranker, fixtures, capture path, evaluator, and
numeric gates are unchanged. `budgeted_response.py` is the current prospective
full-response serializer and selection adapter. `deployable_response.py`
retains the earlier diagnostic contract and shared validators. Neither makes
the current POC deployable.

## Adopted private byte boundary and selection

The manager and independent reviewer accepted this prospective interpretation:
the 2,048-byte ceiling covers the **decoded native output text**, including all
visible client prefixes and every required Context payload field. Transport
JSON escaping, call/routing IDs, and other protocol metadata remain separately
reported, and all actual token costs remain charged. This does not change the
measured 2,048-token gate or confer the old serializer's verdict.

For pinned Codex 0.153.4 regular MCP structured responses, the client renders
structured JSON once and prepends a duration header. The source uses
`std::time::Duration::as_secs_f64()` and fixed four-decimal formatting.
The entire Duration domain rounds no higher than 2^64 seconds, yielding at most
25 formatted duration characters plus 28 literal bytes: **53 reserved bytes**.
This is a domain bound, not the 34 bytes observed for a short call. The
[pinned formatter](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/core/src/tools/context.rs#L150)
and [structured renderer](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/protocol/src/models.rs#L2246)
are archived with hashes; a local Rust Duration::MAX formatter proof yields 53.

The current payload's `serialized_bytes` equals its exact canonical JSON UTF-8
length, including its own fields. The audit reports `wrapper_reserved_bytes=53`
and `budgeted_output_bytes=serialized_bytes+53` separately. `estimated_tokens`
is only `ceil(budgeted_output_bytes/4)`, never measured tokens. Actual native text
length is measured after delivery and must be no larger than this bound or
2,048 bytes. Exact payload equality rejects missing fields, altered data, and
client truncation. Before future sampling, the protocol must independently pin
an effective native truncation byte budget of at least 2,048. The formatter
truncates after adding its header; post-delivery checking alone is insufficient
to authorize a configuration that can silently cut the pack. Code mode, media,
other clients, and HookAdditionalContext require their own contracts.

The hydrated `retrieval_path` identifies strategy: `typed_lexical` or
`typed_recency`, with equal-length labels. Actual `index_mode` remains in
engine/audit/inspect metadata. Canonical Context payload bytes must match across
FTS/scan; native timing prefixes may vary and still count toward the text cap.

The new selector copies the existing Context-local BM25, novelty, mandatory
ordering, and tie rules. Only the fit calculation changes: it counts the full
payload and reserved prefix before selecting each optional record. It never
reads evaluator-required labels or clips IDs, values, anchors, or metadata.
Mandatory or conflict-metadata overflow produces an explicit empty overflow
response. The SQLite bridge is read-only and unknown IDs never create anything.

On all 48 unchanged long cases, canonical FTS/scan payload parity holds and
reserved native output is 1,824–1,966 bytes. Mandatory recall is 100%, but
required recall is **86.6071%** (minimum 71.4286%; 12/48 complete), below the
unchanged 95% gate. Some archive observations outrank required optional facts
under the smaller full-response capacity. The negative result is preserved;
no ranker, fixture, identifier, fact, or gate is tuned to repair it here.

Evidence after the canonical object-order delivery fix:
`benchmarks/results/nerd-context/budgeted-response-20260905T221355`,
manifest SHA-256 `d634edc7b28ca45695c6858b2ff9a1aa1f2d85589898b6eb2d150bde927dfc33`.
It binds three upstream source files, installed launcher/binary hashes, the Rust
domain proof, local source snapshots, and all 96 backend rows. Row text is a
domain-bound model-free rendering, not a native delivery run of the new full
responses. Native delivery, measured tokens, latency, fair lifecycle economics,
and generated capture remain unproved for this candidate.

The 86.6071% is a macro average across cases. There are 324 required facts in
total and 45 missing selections; the supersession cases have six required facts.
The new selections equal the first seven old selected IDs in every case, so
this is not a port-ordering or byte-accounting defect. No omitted active record
fits the remaining budget. Archives are intentional gold stress data and are
not removed. The complete reconstruction contract also requires current-scope
facts beyond the narrower immediate query passed to ranking; that semantic
distinction must remain explicit in any proposed retrieval study.

## Reconciliation with the plan

Task 2 step 5 requires the recall fields `status`, `created`, `context_id`,
`records`, `conflicts`, `overflow`, `serialized_bytes`, `estimated_tokens`, and
`authority`. Step 7 additionally reports retrieval path and selected IDs/source
references. The helper includes all root fields plus `retrieval_path`; IDs and
source references occur on each returned record, without redundant root arrays.
Each record includes `id`, `kind`, `value`, `source`, `source_ref`,
`authority="untrusted_context"`, and every supplied anchor. The root has the
same authority label. Status/revision/timestamps/supersession audit metadata
remain available through inspection rather than ordinary hydration.

These are prospective schema choices requiring explicit reconciliation with
Task 2's instruction to port the four-field serializer unchanged. The old
serializer cannot simultaneously remain unchanged and contain these fields.
No production schema is silently substituted by this helper.

The adopted private anchor shape is a list of at most four objects with a required relative
POSIX `path`, optional `symbol`, and optional lowercase 64-character `sha256`.
Paths forbid traversal, absolute paths, backslashes, drive/scheme syntax, and
control characters. This validates lexical shape only; repository containment,
symlinks, and current content must be revalidated by a future runtime. The
original prose did not settle a shape or numeric anchor limit. Standalone
symbols/hashes remain valid record values with provenance; they are not silently
coerced into path anchors or accepted as anchors by this adapter.

The adopted private conflict shape is a list of `{record_ids: [id, ...]}` with at least two unique
same-Context IDs per group. The helper preserves conflicts, but does not infer
them from prose. The persistence layer supplies authoritative ownership.

Capture prevalidation accepts at most **20** records with exactly the plan's
fields, preserves anchors, and verifies same-Context supersession targets
before returning any accepted batch. Existing POC capture accepts 30 and does
not persist anchors; neither behavior is changed. The current private
`validate_bounded_capture` fixes a **256 KiB** aggregate ceiling on the complete
canonical capture-argument JSON, including Context ID and capture reference;
callers may lower it, never raise it. The manager explicitly adopted this new
contract limit because the original plan left it unspecified. It need not admit
every worst-case combination of individually valid escaped values and anchors.
Per-value and source-reference limits use existing POC limits (8,192 and 256
UTF-8 bytes). This helper is not a complete secret/transcript admission filter
or a persistence transaction. Future integration must implement the schema,
atomic writes, global idempotency, and all remaining security requirements;
it must not strip anchors or split batches without counting actual calls.

## Earlier diagnostic serializer and native projection

In the earlier `deployable_response.py` diagnostic, the caller supplies an explicit projection. Size is
computed to a fixed point including the size and estimate fields themselves.
`estimated_tokens=ceil(bytes/4)` is diagnostic only; measured tokens remain
unestablished. Callers may lower the 2,048-byte cap but never raise it.

All selected records, anchors, and conflict metadata are included or the result
is explicit `overflow` with no records/conflicts and an identity/status/authority
receipt. No successful partial mandatory hydration or value clipping occurs.
If even the complete receipt cannot fit a smaller requested budget, the helper
raises `BudgetTooSmall`; a future transport must define a bounded domain-error
path before any state mutation. Creation cannot hydrate existing records, and
`not_found` cannot create or replace an ID.

The MCP result includes semantically identical compact JSON text and
`structuredContent`, plus `isError`. Counting this wire JSON is not sufficient
to establish the actual client projection. Two model-free native observations
used Codex 0.153.4, a private empty home, synthetic authentication, and a local
scripted Responses provider. Native tool discovery and real stdio MCP calls
returned both successful and overflow fixture results. The client forwarded
structured content **once**, adding a `Wall time` / `Output` prefix and a
`function_call_output` item containing `call_id`, output `id`, and `type`.
Complete canonical items were 383 and 361 UTF-8 bytes. No model inference,
token measurement, billing, quality, or production latency was involved.

`observed_codex_http_projection` exactly replays both observed item shapes;
the capacity audit conservatively counts the entire canonical item, including
escaped output and identity metadata. It is specific to this observed native
HTTP path. Runtime timing and output IDs are added **after** the server returns.
That original observation did not establish a future client metadata bound.
The subsequent adopted decoded-text boundary and 53-byte source-domain bound
above resolve the pinned regular-client reservation. Other clients/transports
may differ, and final delivery must still be verified.

## Historical whole-item capacity diagnostic

The immutable capacity diagnostic preserves the old ranker and all 48 long
fixtures. Their original packs still achieve 100% required recall at
1,840–1,974 bytes. Under one observed complete native frame:

| Unchanged facts measured | Complete bytes | Fits / 48 |
| --- | ---: | ---: |
| Original ranker's selected records | 3,017–3,171 | 0 |
| All evaluator-required records only | 1,942–2,204 | 12 |
| Mandatory active goal/boundary/decision records only | 1,122–1,208 | 48 |

The table uses the conservative **whole-item JSON** counting policy. Required
payload JSON itself is 1,599–1,837 bytes; the native output string including
timing is 1,633–1,871 bytes. Both fit all 48 cases. HTTP inspection establishes
these representations, but not which protocol identity fields or JSON escaping
the upstream model sees. The 36 whole-item overflows therefore do **not** prove
that the full schema intrinsically cannot fit the model-visible 2,048-byte gate.
The subsequent decoded-text policy resolves this choice without reclassifying
the old diagnostic as a pass.

Required labels are used only for a diagnostic capacity lower bound, never
candidate selection. Records and source sentences are not shortened; no
anchors occur in these fixtures. The required-only result is not an executable
gold-selected retrieval design. This full response proposal therefore cannot
inherit the old byte/recall result. The 36 required-only overflows remain
visible negative evidence; no threshold or mandatory fact is removed.

Native evidence: `benchmarks/results/nerd-context/response-wire-20260905T215512`,
manifest SHA-256 `3e15828dc2dd8b5c96819264a4b6562f609e45ec9fa425d157441156f7cd2f14`.
Capacity evidence with all three counting surfaces:
`benchmarks/results/nerd-context/response-capacity-20260905T215933`,
manifest SHA-256 `b2f15bf729ea4fb8d12c1054f5667b35049f7ef3d42e9454ad1def0b0fc01f39`.
Both include immutable source snapshots and hashed observations. The earlier
success-only native observation and whole-item-only capacity diagnostic remain
intact as separate source-bound archives.

Run focused proof with:

```sh
python3 -m unittest discover -s docs/experiments/nerd-context -p 'test_*response*.py' -v
python3 docs/experiments/nerd-context/response_contract_audit.py --probe-root benchmarks/results/nerd-context/response-wire-20260905T215512
python3 docs/experiments/nerd-context/budgeted_response_audit.py
```

No new cohort is implemented. Any later representative active-state/coding
study must retain compact and short controls, capture independently of future
questions/rubric labels, preserve all numeric gates and meaningful ordinary
work, and provide the summary **equal durable storage as well as equal
hydration** with competent query-time selection and every call fully charged.
The full response and actual native wrapper must be settled before fresh
empirical evidence; a larger corpus does not repair this contract gap itself.
