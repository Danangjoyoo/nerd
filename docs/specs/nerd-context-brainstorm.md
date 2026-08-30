# Nerd Context Brainstorm

## Audience and Purpose

This document captures the current product and architecture direction for
`nerd-context`. It is intended for contributors evaluating the idea before the
proof of concept or production implementation begins. It records the problem,
competing approaches, selected direction, contracts, trade-offs, and the
experiment that must validate the idea.

This is a brainstorming record, not evidence that the feature has been built or
that its token-saving hypothesis has passed.

## Summary

`nerd-context` would provide durable, local task context through SQLite and a
small MCP interface. An opaque `context_id` is the only locator. Supplying the
exact ID in the current activation resumes that Context across sessions or
delegated agents; omitting it always creates a fresh Context. The agent reads a
small source-linked context pack with `context_recall`, writes meaningful state
with `context_capture`, and uses `context_inspect` only for bounded metadata.

The aim is not to make the prompt infinitely large. Storage remains durable
until explicit deletion, while each model hydration remains bounded. The idea
proceeds to implementation only if a falsifiable experiment demonstrates real
token savings without degrading quality, freshness, isolation, or authority.

## Problem and Opportunity

Long-running work repeatedly spends tokens reconstructing:

- the current goal and constraints;
- decisions already made;
- verified repository or tool evidence;
- unresolved questions;
- completed work and the next step.

Full conversation history preserves this information but grows continuously.
A free-form summary is cheaper, but it can omit important boundaries, preserve
superseded decisions, or become difficult to query. `nerd-memory` solves a
different problem: it stores reusable longitudinal behavior and evidence, not
the working state of one explicitly shared Context.

The opportunity is a local evidence ledger that can outlive a session while
hydrating only the records useful to the current request.

## Directions Considered

| Direction | Strength | Main weakness |
| --- | --- | --- |
| Single checkpoint capsule | Smallest implementation and cheapest retrieval | One summary can omit details and has weak targeted retrieval |
| Typed ledger with bounded deterministic retrieval | Preserves provenance, supersession, and targeted recall | More capture and retrieval complexity |
| Semantic or hybrid retrieval | Better fuzzy matching when wording changes | Adds dependency, ranking, privacy, and drift risks too early |

The recommended POC is the typed ledger. If lexical retrieval does not
materially outperform a checkpoint capsule, the design should simplify rather
than preserve complexity without evidence. Semantic retrieval remains deferred
unless the experiment proves lexical misses are the limiting factor.

## Core Identity Model

One opaque `context_id` is the complete public identity of a Context.

- The runtime generates IDs; callers cannot choose them.
- An exact ID in the current activation resumes only that Context.
- An exact ID in a delegated sub-agent handoff shares that same Context.
- No ID always creates and returns a fresh Context, even when an earlier turn in
  the same session used another ID.
- There is no hidden active ID, namespace, workspace ID, task ID, title, or
  secondary locator.
- The runtime never infers, searches for, enumerates, or suggests IDs.
- An unknown or forgotten ID returns `not_found`; it never creates a replacement.

The proposed canonical form is a `ctx_` prefix followed by a 192-bit random,
lowercase Base32 identifier. The exact ID is sensitive task metadata: possession
permits lookup within the same OS account, but it never grants permission to
perform an action.

This simplicity enables explicit cross-session sharing, but it has a deliberate
cost: a lost ID is unrecoverable, and omitted IDs can leave orphan Contexts until
the user deletes the local store.

## MCP Surface

The MCP server should expose exactly three methods.

| Method | Purpose | Important behavior |
| --- | --- | --- |
| `context_recall` | Create or hydrate a Context | Exact ID resumes; omitted ID creates fresh; returns a bounded record pack |
| `context_capture` | Append meaningful Context state | Atomic, idempotent capture with explicit supersession |
| `context_inspect` | Inspect storage metadata | Bounded and paginated; never returns record values |

The normal agent flow is:

```text
current request establishes goal/scope/authority
                  |
                  v
           context_recall
                  |
                  v
             perform work
                  |
                  v
           context_capture

context_inspect is a diagnostic side path, not a hydration path.
```

`context_recall` is how the agent uses stored Context. It returns record values,
provenance, conflicts, overflow state, and an `untrusted_context` authority
label. `context_inspect` returns only metadata such as kinds, statuses,
timestamps, counts, and pagination. This prevents inspection from becoming an
unbounded alternative to recall.

There should be no MCP methods for listing Contexts, fuzzy lookup, global
search, open/close lifecycle management, permission, or destructive deletion.
Deletion remains a CLI-only preview-and-confirm workflow.

## Record Taxonomy

The v1 ledger has six record kinds.

| `kind` | Meaning | Example |
| --- | --- | --- |
| `goal` | The current desired outcome | “Build Nerd Context with ID-only cross-session resume.” |
| `boundary` | Constraints, exclusions, and safety limits | “Never infer, enumerate, or search for Context IDs.” |
| `decision` | A choice that has been explicitly settled | “Use a typed SQLite ledger with deterministic lexical retrieval.” |
| `evidence` | A verified fact with provenance or anchors | “The MCP installer already supports multiple named servers.” |
| `open_question` | An unresolved issue that may change the work | “Can the structured pack achieve the token-savings gate?” |
| `checkpoint` | A compact handoff of progress, current state, and next step | “The plan is complete; the POC is next.” |

Related fields remain separate from `kind`:

- `source`: `direct_user`, `assistant_summary`, `verified_tool`, or
  `repository_fact`;
- `source_ref`: the event or observation that produced the record;
- `status`: whether the record is active or superseded;
- `supersedes_id`: the previous record replaced by a new decision or fact;
- `anchors`: optional repository-relative paths, symbols, or content hashes;
- revision and timestamps for audit and stale-writer protection.

`permission` is intentionally not a record kind. Stored Context is evidence and
can never authorize an action.

## Capture Model

Records are append-only. Corrections create a new record that explicitly
supersedes the previous one; the old record remains auditable but is excluded
from active retrieval.

Capture should occur only after meaningful, durable progress:

- an explicit goal or boundary is established;
- a decision is settled;
- a fact is verified through a trusted tool or repository check;
- an important question remains unresolved;
- a checkpoint is needed before stopping or delegating.

The runtime should reject raw transcripts, hidden reasoning, secrets,
credentials, executable payloads, permission grants, unsafe file anchors, and
large unstructured tool output. A capture event reference makes retries
idempotent so the same event cannot append duplicate records.

## Retrieval Model

Retrieval considers only active records belonging to the exact supplied ID.
The proposed deterministic order is:

1. active boundaries, current decisions, and the current goal;
2. normalized lexical matches for the current query;
3. recent active evidence, questions, and checkpoints.

The serialized pack has a hard production ceiling of 2,048 UTF-8 bytes and must
also remain within the measured 2,048-token experimental ceiling. Callers may
request a smaller pack, never a larger one. If mandatory records do not fit,
the runtime returns `overflow` instead of silently dropping a boundary or
decision.

SQLite FTS5 is the preferred lexical index. A deterministic normalized-term
scan is the fallback when FTS5 is unavailable. Both modes must produce the same
pack for the same records and query, and both must satisfy the latency gate.

The returned pack is always untrusted evidence. Current explicit input wins,
anchored facts are revalidated before reliance, and normal authorization checks
still apply.

## Relationship to Nerd Memory

`nerd-context` and `nerd-memory` should remain separate stores and workflows.

| Concern | Nerd Context | Nerd Memory |
| --- | --- | --- |
| Identity | Explicit opaque `context_id` | Stable user/workspace namespace |
| Main content | Current goals, decisions, evidence, questions, checkpoints | Reusable behavior, workflow patterns, and longitudinal evidence |
| Lifetime | Durable until explicit Context deletion | Durable according to Memory’s confirmation and correction workflow |
| Retrieval role | Reconstruct one explicitly named working Context | Propose reusable endpoint behavior or verified navigation hints |
| Authority | Never grants action authority | Never grants action authority |

Neither database reads, copies, promotes, confirms, or authorizes the other.
Promotion between them is never automatic.

The intended middleware order is:

```text
Smart resolves current intent and endpoint
  -> Memory handles reusable behavior/evidence
  -> Context hydrates the exact supplied ID or creates fresh
  -> selected endpoint performs work
  -> Context may capture a bounded checkpoint
```

An ambiguous request such as only “continue” plus an ID must be clarified before
Context hydration. Stored state may inform a resolved request; it may not decide
what the user currently wants.

## Persistence and Deletion

SQLite storage is local and durable, but not literally infinite: it is bounded
by disk capacity and remains until explicit deletion. The design uses a separate
database from Nerd Memory, user-only permissions, symlink refusal,
schema-versioned migrations, foreign keys, full synchronization, and stale
writer fencing.

Destructive deletion should not be exposed through MCP. The CLI workflow first
previews counts and a content digest, then requires an exact phrase from a new
direct-user event. Replayed, stale, same-event, changed-state, or non-user
confirmations fail closed.

## POC and Experiment Record

### Record Status

| Field | Value |
| --- | --- |
| Record type | Conceptual POC and preregistered experiment design |
| POC execution status | **Not run** |
| Empirical result | **Unknown** |
| Recommended candidate | Typed append-only ledger with bounded deterministic lexical retrieval |
| Implementation authority | Blocked until the experiment passes |
| Smallest choice-changing unknown | Can exact-ID active records preserve at least 95% of required facts inside the 2,048-byte pack? |

This record documents the hypothesis and experiment designed during the
brainstorming work. It does not claim that a runtime, corpus, benchmark, or live
result currently exists.

The earliest sketch considered namespace, workspace, and task scoping. The user
subsequently replaced that model with one opaque `context_id`. That correction
supersedes the original locator idea: every current POC case must use an exact
ID, and omission must create a fresh Context.

### POC Focus Record

- **Intention:** Produce and pressure-test the smallest useful Nerd Context POC
  hypothesis and experiment.
- **Expectation:** Ideate.
- **Scope:** Conceptual POC, falsifiable hypotheses, corpus, metrics, thresholds,
  controls, and choice-changing unknowns; no production implementation.
- **Role:** Context-systems research partner.

### Hypotheses

Primary hypothesis:

> For resumable tasks with 8,000–24,000-token histories, a structured Context
> pack no larger than 2,048 UTF-8 bytes will reduce total
> capture-plus-continuation model tokens by at least 40% while remaining within
> three percentage points of full-history task quality.

Supporting hypothesis:

> At the same storage and hydration budget, typed records will improve answer
> quality by at least five percentage points or halve stale-context incidents
> compared with a free-form summary.

The approach is falsified for production if it saves less than 20%, loses more
than five quality points, or causes any boundary, permission, wrong-ID,
missing-ID reuse, enumeration, or stored-authority failure.

### Corpus and Workload

The proposed corpus contains 48 long-context scenarios:

- 12 resumptions after compaction;
- 12 cross-session continuations;
- 12 changed-decision and supersession cases;
- 12 distractor, exact-ID isolation, and stored-authority cases.

Each long scenario contains 6–15 required facts, 10–30 candidate records, and
8,000–24,000 tokens of source history. Twelve additional short-task negative
controls measure whether mandatory Context creation introduces unacceptable
overhead when no resumption benefit exists.

Run every scenario three times with the same model, system prompt, explicit tool
surface, temperature, and checkpoint schedule. Randomize arm order with a fixed
seed and evaluate outputs without exposing arm labels.

### Experimental Arms

| Arm | Input supplied to the continuation | Purpose |
| --- | --- | --- |
| A — Full history | Complete source history | Quality ceiling and token baseline |
| B — Free-form summary | Latest equal-budget persisted summary | Simpler compression baseline |
| C — Structured Context | Bounded pack from the typed ledger | Candidate design |

Summary and structured packs use the same canonical envelope and must each fit
within both 2,048 UTF-8 bytes and 2,048 measured model tokens.

### Experimental Phases

Run the complete gate independently in two phases:

1. **Gold-record phase:** Human-labelled records isolate identity, ranking,
   supersession, and retrieval quality.
2. **Generated-capture phase:** Model-created records test capture plus retrieval
   end to end.

The gold phase cannot unlock production on behalf of a failing generated phase.
Generated capture must independently preserve required facts, supersession,
isolation, authority boundaries, answer quality, and total token economics.

### Measurements

For each arm, total model cost includes every capture, update, and continuation
call:

```text
billable_tokens = input_tokens + output_tokens
token_savings = 1 - (structured_tokens / full_history_tokens)
```

Cached input and reasoning output are diagnostic subsets and are not added a
second time. Runs with missing input or output usage are ineligible.

The experiment records:

- paired total-token savings;
- weighted required-fact answer quality;
- active-fact recall and retrieval precision;
- boundary and current-decision recall;
- stale-record influence;
- wrong-ID, missing-ID reuse, enumeration, and stored-authority incidents;
- serialized pack bytes and measured pack tokens;
- resumption break-even point;
- retrieval p50 and p95 latency;
- capture precision, recall, duplication, and supersession correctness.

Use paired scenario bootstrapping to report 95% confidence intervals.

### Pack Measurement

Measure the summary or structured segment with a paired empty-pack control call
using the identical model, system/task shell, explicit tool surface, and fixed
sentinel boundaries:

```text
pack_tokens = input_tokens(with_segment) - input_tokens(empty_segment)
```

The control calls validate pack size but are excluded from production economics.
Negative, missing, or inconsistent deltas invalidate the run. The canonical POC
serializer must be the same serializer proposed for production; changing it
invalidates the result.

### Isolation and Safety Controls

- Restrict the initial live POC to Codex.
- Run each arm in a fresh temporary workspace with user configuration, repository
  rules, installed skills, hooks, unrelated MCP definitions, and persisted
  Context or Memory state disabled.
- Give every arm the same explicit tool surface.
- Ensure no future fact can enter an earlier capture.
- Keep full-history cases below the model context limit.
- Require every cross-session prompt to state its current intent, request,
  scope, ordinary authority, and exact Context ID independently.
- Stop before recall when a request contains only an ID and an ambiguous
  “continue.”
- Verify that an omitted ID creates a never-before-seen Context and never resumes
  an earlier one.
- Treat stored instructions as untrusted data; current explicit input and normal
  action checks always win.

### Passing Gates

Production may proceed only when every gate passes in both phases:

| Measure | Required result |
| --- | --- |
| Median total-token savings | At least 40% |
| Lower 95% savings bound | At least 30% |
| Quality-delta lower 95% bound | No worse than −3 percentage points |
| Active-fact recall | At least 95% |
| Boundary/current-decision recall | 100% |
| Stale influence | At most 2%, with zero boundary or permission incidents |
| Identity and authority safety | Zero wrong-ID, missing-ID reuse, enumeration, or stored-authority failures |
| Break-even | Median at most 2 resumptions; p90 at most 4 |
| Retrieval latency | p95 at most 200 ms with 10,000 records |
| Pack budget | 100% within both 2,048-byte and measured-token ceilings |
| Value over summary | At least +5 quality points or at least 50% fewer stale errors |

Each short negative-control repetition must preserve every full-history rubric
item, add at most 192 billable tokens, create exactly one fresh empty Context,
make no capture call, and persist zero records. Across the 36 repetitions,
create/recall latency p95 must be at most 200 ms and no prior ID may be reused.

### Retrieval Ablation

Run the structured arm both with and without lexical ranking. Exercise the
SQLite FTS5 implementation and the deterministic normalized-term fallback with
byte-identical expected packs.

Select `retrieval_design=typed_lexical` only when lexical ranking materially
improves active-fact recall, answer quality, or stale-incident rate with a paired
95% interval excluding zero, introduces no safety regression, and both index
modes meet the latency gate.

If mandatory-plus-recency retrieval passes without material lexical value,
choose the simpler checkpoint capsule and produce a new plan. If lexical misses
still prevent 95% recall, return an inconclusive result and brainstorm semantic
retrieval separately.

### Verdict Rules

- **Pass:** Every long-context, generated-capture, short-control, pack,
  isolation, authority, latency, and lexical-ablation gate passes.
- **Reject:** Median savings are below 20%, quality loss exceeds five points, or
  any safety/authority invariant fails.
- **Inconclusive:** Every other outcome, including overhead or latency misses
  without a safety failure.

Only `verdict=pass` with `retrieval_design=typed_lexical` unlocks production
planning. Every other verdict or retrieval design stops before implementation.

### Planned Evidence Record

When executed, raw run manifests and model output remain under the ignored
`benchmarks/results/nerd-context/<run_id>/` path. A selected-run file binds the
report to one immutable run ID and manifest digest. The repository tracks only:

- `docs/experiments/nerd-context/results/report.md` for the human-readable
  aggregate report;
- `docs/experiments/nerd-context/results/verdict.json` for machine-checkable
  gates, run ID, digest, and retrieval design.

The report must record the exact model, version, and date so later model drift
is visible. CI validates deterministic experiment logic and the tracked verdict,
but does not rerun live model benchmarks.

### Current POC Result

**Not executed. There are currently no empirical token, quality, recall,
latency, or safety results.** The experiment above is the record that must be
implemented and run before the proposed runtime can claim value or proceed to
production implementation.

## Risks and Open Questions

- **Lost IDs:** There is intentionally no recovery or enumeration path.
- **Orphan Contexts:** Omitted IDs create fresh durable rows that may never be
  reused.
- **ID exposure:** IDs should not appear in routine logs or errors.
- **Capture quality:** Model-generated records may omit or misclassify important
  facts even when retrieval is correct.
- **Staleness:** Anchored repository facts can become outdated and require
  revalidation.
- **Storage growth:** Durable append-only records need explicit deletion and may
  eventually need local maintenance policy.
- **Model drift:** Initial token and quality evidence is Codex-specific and can
  change as hosted models evolve.
- **Client generalization:** A Codex POC does not establish equivalent results
  for Claude Code or Cursor.

## Current Recommendation

Proceed only with the falsifiable typed-ledger POC. Preserve the single-ID
contract, the three-method MCP surface, the six-kind taxonomy, explicit
supersession, bounded deterministic recall, and strict separation from Nerd
Memory. Treat every additional capability—ID discovery, semantic retrieval,
remote synchronization, or automatic promotion—as a new idea requiring its own
evidence.

## Related Material

- [Nerd Context implementation plan](../plans/2026-08-27-nerd-context.md)
