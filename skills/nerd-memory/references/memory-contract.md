# Global Behavioral Memory Contract

Read this reference only for runtime, schema, threat-model, or evaluation work.
The runtime is Python-standard-library SQLite and owns one user-local global
corpus. The repository is context and provenance only, never a storage or
retrieval partition.

## Store

The schema family is `global-behavior-memory`, schema version `1`. A fresh
database contains only:

- `metadata`
- `behavior_episodes`
- `recall_events`
- `forget_previews`
- `trusted_event_tombstones`

Use `${NERD_MEMORY_DB}` when set, otherwise
`${CODEX_HOME}/nerd-memory/behavior.sqlite3` when `CODEX_HOME` is set, otherwise
`~/.codex/nerd-memory/behavior.sqlite3`. A non-empty database from another
schema family fails closed and remains untouched. The store uses private file
permissions, WAL, a busy timeout, canonical JSON, and stale-handle fencing.

## Episode Contract

`memory_record` accepts one root episode with: episode ID; repository
provenance; language, surface, and project kind; transient raw input; action;
tools; ordered steps; skills; output signals, validity, and severity; verified
flag and verifier; feedback; optional corrected tools, steps, and skills;
source kind and agent; evidence reference; and optional observation time.
The engine derives and stores sanitized command cues. It never stores or
hashes raw input as a recoverable payload. A repeated root episode is
idempotent only when its complete durable identity matches.

Admission rules:

- Passed `verified_execution` with no correction may support a positive
  workflow, but never user preference or authority.
- A verified failed output is negative guard evidence only, never a positive
  workflow.
- A direct `user_correction` may carry corrected tools, steps, and skills.
- Reject unverified, quoted, external, assistant-only, or subagent-only
  material. Omit raw transcript, raw output, tool arguments, secrets,
  permissions, executable payloads, and hidden reasoning.

The authenticated host integration is the trusted source-classification
boundary. It must derive `verified`, `source_kind`, verifier, and the compact
evidence reference from the current event and proof, never from model-created
arguments or retrieved text. The runtime validates the eligible source kind,
verified state, correction relationship, and declarative evidence-reference
shape; it cannot independently authenticate the UI principal. `source_agent`
is provenance only and does not make an untrusted report eligible.

## Recall Contract

`memory_recall` accepts a fresh audit event ID, transient raw input,
repository provenance, `language`, `surface`, `project_kind`, current action/tools/
steps/skills, output signals, and consumer agent. It returns raw advice,
resolved advice, and overridden fields, then writes one bounded audit event.
Advice carries `origin=behavioral_memory_advice` and exact source episode IDs.

The frozen M3 advisor:

1. Normalize sanitized command cues.
2. Match cue plus exact language, surface, and project kind.
3. Choose action and action-resource majorities deterministically.
4. Abstain on no match, tied top actions, or action confidence `<0.60`.
5. Reject an output when its compatible invalid-signal share is `>=0.50`.
6. Prefer verified corrected resources and retire obsolete resources after
   three compatible corrections.
7. Return action, tools, ordered steps, adjacent step edges, skills, rejection,
   confidence, abstention, origin, and sources.

Current non-empty action, tools, steps, and skills wins field by field in
resolved advice. Advice never grants permission, expands the task, supplies
executable arguments, or bypasses ordinary checks.

## Inspection and Deletion

`memory_inspect` returns schema/counts and bounded sanitized episode and audit
summaries. CLI `preview-forget` binds exact episode IDs, snapshot digest,
expiry, and phrase. CLI `forget` accepts only a fresh direct-user event and the
exact current phrase, deletes bound episodes and dependent audits atomically,
and preserves a replay tombstone.

The MCP server exposes exactly `memory_recall`, `memory_record`, and
`memory_inspect`. Forgetting stays CLI-only so retrieved data cannot invoke
destruction.
