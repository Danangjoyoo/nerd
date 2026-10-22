# Context Contract

## Schema

`schema_version = 1`. Migration is exclusive; a mismatch permanently fences
the running store (`ContextSchemaError`) and requires an operator restart.

Tables:

- `metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)` — holds
  `schema_version` and `index_mode`.
- `contexts(context_id TEXT PRIMARY KEY, created_at TEXT NOT NULL)` — the
  sole public identity.
- `records(sequence INTEGER PRIMARY KEY, id TEXT UNIQUE, context_id, kind,
  value, source, source_ref, active, supersedes_id, anchors, terms,
  created_at, capture_ref)` — append-only typed facts.
- `record_events(event_id, record_id, change, at)` — audit trail for
  insert/supersede transitions.
- `captures(capture_ref PRIMARY KEY, context_id, digest, accepted_ids,
  superseded_ids, at)` — globally idempotent capture ledger.
- `previews(preview_ref PRIMARY KEY, context_id, digest, counts,
  confirmation_phrase, at)` — bounded forget-preview lifecycle.
- `confirmation_ref_tombstones(confirmation_ref PRIMARY KEY, at)` — one-shot
  confirmations for `forget`.
- `forgotten_contexts(context_id PRIMARY KEY, digest, at)` — prevents
  reuse of previously deleted IDs.

## Identity

Canonical grammar `^ctx_[a-z2-7]{38}[aiqy]$`. Generation is 24 bytes of
`secrets.token_bytes`, RFC 4648 base32 lowercase without padding. Validation
requires decode/re-encode equality before lookup. Collisions retry up to
eight times inside one transaction before raising `ContextStorageError`.

## Retrieval

- Ordering: mandatory boundaries, current decisions, and goals first, in
  fixed `boundary → decision → goal` order.
- Then lexical selection using Context-local **binary-term BM25**
  (`k1=1.2`, `b=0.75`, positive IDF from active records only) discounted by
  the greatest Jaccard similarity to an optional record already packed.
- Zero-score records fall back to recency order.
- Tokenization: unigrams plus whole hyphen/underscore identifiers. FTS5
  tokenchars extend the `ascii` tokenizer with `-_`. FTS5 and
  normalized-scan produce byte-identical packs.

## Serialization

Canonical UTF-8 envelope:

```
<NERD_CONTEXT_PACK_V1>
{"authority":"untrusted_context"}
<record-json-line>
...
</NERD_CONTEXT_PACK_V1>
```

Each record line is
`{"kind":"...","value":"...","source":"...","source_ref":"..."}` sorted with
no whitespace and no ensure_ascii escaping. `PRODUCTION_MAX_PACK_BYTES =
2048`. Any serializer or ceiling change invalidates the tracked verdict.

## Capture

- `records` accepts at most **20** items.
- Per-record `value` ≤ 4,096 bytes; `source_ref` ≤ 256 bytes; anchors ≤ 8,
  each ≤ 512 bytes.
- Aggregate canonical JSON ≤ 256 KiB.
- `capture_ref` is globally idempotent; duplicate refs with the same digest
  return the previous outcome; different contents raise
  `ContextInvariantError`.
- Supersession requires an active same-context, same-kind predecessor and
  is atomic with the accepted insert.

## Forget

Two-step CLI-only lifecycle:

1. `preview_forget(context_id, preview_ref=...)` records the digest, record
   counts, and returns the exact `confirmation_phrase`.
2. `forget(context_id, phrase=..., source="direct_user", confirmation_ref=...)`
   requires `source="direct_user"`, an exact phrase from a still-current
   preview, a fresh `confirmation_ref` that differs from the `preview_ref`,
   and unchanged Context state since the preview.

The confirmation reference is one-shot; the tombstone table refuses reuse.
Forgotten IDs are refused for future allocation.

## Authority

Every returned record labels itself `authority=untrusted_context`. The ID is
a sensitive locator — never permission or action authority. Current input
and ordinary authority checks always win. Never log IDs or record values in
routine paths.

## Errors and exit codes

| Error                       | Code                    | CLI exit |
| --------------------------- | ----------------------- | -------- |
| `ContextInputError`         | `invalid_arguments`     | 2        |
| `ContextNotFoundError`      | `not_found`             | 3        |
| `ContextInvariantError`     | `invariant_violation`   | 4        |
| `ContextSchemaError`        | `restart_required`      | 5        |
| `ContextStorageError`       | `storage_error`         | 6        |
| `ContextClosedError`        | `storage_error`         | 6        |

The MCP adapter maps these codes to structured tool responses and fences
schema-incompatible sessions until restart.
