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
The deterministic order is:

1. active boundaries, current decisions, and the current goal;
2. normalized lexical relevance for the current query;
3. recent active evidence, questions, and checkpoints.

The serialized pack has a hard production ceiling of 2,048 UTF-8 bytes and must
also remain within the measured 2,048-token experimental ceiling. Callers may
request a smaller pack, never a larger one. If mandatory records do not fit,
the runtime returns `overflow` instead of silently dropping a boundary or
decision.

SQLite FTS5 is the preferred lexical index. A deterministic normalized-term
scan is the fallback when FTS5 is unavailable. Both modes must produce the same
pack for the same records and query, and both must satisfy the latency gate.

The revised lexical scorer uses binary-term BM25 with fixed `k1=1.2` and
`b=0.75`. For each active record in the exact requested Context, `L` is its
number of distinct normalized value terms, `N` is the number of active records,
`avgL` is their mean length, and `df(t)` counts active records containing term
`t`. Sum the following contribution over matching query terms in sorted order:

```text
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
contribution(t, record) = idf(t) * (k1 + 1)
                        / (1 + k1 * (1 - b + b * L / avgL))
```

Select optional records greedily by `BM25 * (1 - maximum Jaccard similarity)`
to any previously selected optional record's normalized term set; the maximum
is zero before the first optional selection. Mandatory records do not reduce
novelty. This fixed diversity adjustment prevents repeated near-identical notes
from exhausting the budget; it must pass an independent generic duplication
regression and uses no corpus-specific rule. Recompute after each selection;
records that do not fit are skipped whole. Recency and record ID resolve ties.

An empty query or term corpus has score zero. The scorer uses value text and
the current query only; required-fact labels, case categories, record IDs,
source references, source classes, and corpus-specific vocabulary are not
relevance features. Mandatory ordering,
whole-record byte packing, and mandatory overflow behavior remain unchanged.
FTS5 supplies matches, while both modes use these same Context-local statistics
and scorer rather than FTS5's global ranking statistics. The fixed constants
follow [SQLite's BM25 defaults](https://www.sqlite.org/fts5.html#the_bm25_function);
this binary-term, positive-IDF variant is explicitly defined above.

The returned pack is always untrusted evidence. Current explicit input wins,
anchored facts are revalidated before reliance, and normal authorization checks
still apply.

## Relationship to Nerd Memory

`nerd-context` and `nerd-memory` should remain separate stores and workflows.

| Concern | Nerd Context | Nerd Memory |
| --- | --- | --- |
| Identity | Explicit opaque `context_id` | One user-local global behavioral corpus; repository is provenance |
| Main content | Current goals, decisions, evidence, questions, checkpoints | Reusable behavior, workflow patterns, and longitudinal evidence |
| Lifetime | Durable until explicit Context deletion | Durable until explicit preview-bound deletion |
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

### Prospective empty-allocation hook experiment

A private Codex experiment may allocate an **empty** Context in a trusted
`UserPromptSubmit` hook before Smart's Focus Record. This is an explicitly
authorized mechanism revision, not a production implementation or passing gate.
It reads no stored observations, captures nothing, and supplies only the actual
committed ID receipt. Smart still derives Intention, Expectation, Scope, and
Role from the current request; the receipt cannot change routing or authority.
An already completed allocation must not be repeated through MCP.

The experimental adapter defines the current selector surface as the native
prompt text, including a delegated handoff delivered in that text. `Context
ID:`, `Nerd-context created:`, `Nerd-context resumed:`, any `ctx_` candidate, and
malformed or multiple possible selectors all defer to the normal post-Focus
route before any database access. Unknown payload fields also defer until that
input surface is specified. There is no lookup from prior turns, hidden state,
attachments, or inferred IDs; an unknown explicit ID still gets `not_found`
without replacement.

Allocation and its private retry mapping commit atomically in the actual POC
SQLite store. The mapping binds the client adapter, native session and turn
identity, and payload digest: the same callback replays its receipt, a new turn
creates a fresh ID even for identical text, and conflicting payloads fail.
This mapping is callback idempotency, not a public locator or active Context
slot. Authorized subagents are permitted; native distinct activation identity
and handoff delivery remain unproved, so unsupported adapter paths retain
post-Focus MCP handling. No main-thread-only requirement is introduced.

The corrected observational probe established native Prompt/Stop hook firing
and Prompt receipt delivery in Codex 0.153.4. It did not prove Context allocation,
Focus compliance, retries, delegated activation, full billable accounting, or
the 192-token/200-ms short-task gates. All numerical gates remain unchanged;
component latency and future allocation smoke observations cannot unlock
production on their own.

The subsequent independently reviewed two-process allocation smoke did commit
one fresh empty Context and one retry mapping, preserve zero records/captures,
and deliver the actual ID in the normal answer without a model tool call.
Its archive is `empty-allocation-smoke-20260906T063513-1bf3e9a0b0` under the
ignored results root (manifest SHA-256
`ae144e2ba7538a887cf112c3d6fdd13754b0fbe8d4a6b5427c077bc86202c490`).
Both answers displayed the four Focus labels but misplaced the endpoint;
the treatment echoed the entire undelimited receipt/instruction paragraph.
Neither correct Smart semantics nor a compact display contract was proved.
The CLI-reported difference was 139 tokens; full billing and incremental
native activation latency remain unknown. Separately, 36 native Python
allocation processes had 52.50-ms p95 startup-through-exit component time;
that excludes Codex dispatch and receipt delivery and is not the latency gate.
The prospective formatter now separates a data-only display line from trusted
hook instructions with explicit receipt delimiters. Its parser and formatter
are tested offline; the preserved native smoke used the earlier undelimited
format. Future integrated proof must load the actual Smart contract, including
Expectation as an endpoint and Role as the single best role. These repairs have
not received another native smoke run.

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
| POC execution status | Current deterministic preflight passes; corrected protocol unrun; full live run held |
| Empirical result | Gold required/mandatory recall 100%; archived 40-call diagnostic generated savings 4.30%, break-even 4 |
| Studied candidate | Typed append-only ledger with bounded deterministic lexical retrieval; production blocked |
| Implementation authority | Blocked until the experiment passes |
| Smallest choice-changing unknown | Can a faithful capture lifecycle meet the unchanged cost, quality, and lexical-value gates? |

This record documents the hypothesis and experiment, including the authorized
2026-09-06 design revision. The disposable POC exists; neither deterministic
preflight nor unit-test success establishes live quality or token savings.

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

Each independent case/repetition/phase lifecycle has two chronological capture
checkpoints and exactly four actual fresh continuation sessions after the final
checkpoint. The four sessions repeat the same resolved current request and
source history. Full history replays that history in every session; the bounded
arms reuse their persisted state without capture when no new observation
arrives. Captures are never shared across independent repetitions or phases.
This measures four-session reuse of a resolved factual request; it does not
establish savings for one-shot work or changing future questions.

### Experimental Arms

| Arm | Input supplied to the continuation | Purpose |
| --- | --- | --- |
| A — Full history | Complete source history | Quality ceiling and token baseline |
| B — Free-form summary | Latest source-only, model-created persisted summary | Simpler compression baseline |
| C — Structured Context | Bounded pack from the typed ledger | Candidate design |

Summary and structured packs use the same canonical envelope and must each fit
within both 2,048 UTF-8 bytes and 2,048 measured model tokens.

In both phases, the summary receives the same available chronological source
prefix/delta, current request, and capture checkpoints as generated structured
capture. Each update sees its own previous persisted state. The summary prompt
must support competent compression, current corrections, and needed source
references, and may use the full remaining budget inside the canonical
envelope. Do not impose the earlier arbitrary 1,400-byte prose limit. Neither
model receives evaluator-only required/active labels or future observations.
Count all actual summary creation and update calls. The original concatenation
of every labelled required fact is an oracle diagnostic only, outside the three
gate arms; preserve it as a ceiling without using it to choose candidate rules.

### Experimental Phases

Run the complete gate independently in two phases:

1. **Gold-record phase:** Human-labelled candidate records isolate candidate
   identity, ranking, supersession, and retrieval quality. The summary remains
   model-created from source history, so this phase alone does not isolate a
   causal effect of representation or establish end-to-end capture quality.
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

Calculate savings from one complete four-session lifecycle: charge its actual
capture/update calls once and sum its four actual continuation calls. Never
divide capture cost across the three independent repetitions, extrapolate
unexecuted sessions, or include paired measurement calls in production cost.
Break-even is the earliest observed session where cumulative structured cost,
including the full capture cost, is no greater than cumulative full-history
cost. If that has not happened by session four, record it as not reached rather
than inferring a passing value. Every session contributes to quality and stale
measurements; preserve case-level paired bootstrap clustering across sessions
and repetitions, and inspect safety failures even in ineligible groups.

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
- capture fidelity precision, required-fact recall, query relevance precision,
  duplication, and supersession correctness.

Generated-capture fidelity precision counts faithful active same-Context source
facts, including nonrequired facts, divided by all captures. Required-fact recall
counts distinct faithful required active facts divided by all required active
facts. Both retain the 95% gate. Query relevance precision is a separate
diagnostic: faithful required captures divided by all captures. Do not force
irrelevant capture to manufacture lexical value; a naturally compact ledger
without material lexical benefit remains a capsule candidate.

Use paired scenario bootstrapping to report 95% confidence intervals.
The current exact-quotation rubric measures weighted exact-source reconstruction
and provenance. Meaning-preserving paraphrases may fail this explicit quotation
task; general semantic, implementation, and reasoning quality remain
unestablished. Keep the scoring rule identical across arms and disclose its
scope in any result.

### Pack Measurement

Measure the summary or structured segment with a paired empty-pack control call
using the identical model, system/task shell, explicit tool surface, and fixed
sentinel boundaries:

```text
pack_tokens = input_tokens(with_segment) - input_tokens(empty_segment)
```

The control calls validate pack size but are excluded from production economics.
The control's segment is the empty string between the same external sentinels,
not a serialized empty Context pack: the measured segment includes the complete
canonical header, authority label, record body, and footer. Negative, missing,
or inconsistent deltas invalidate the run. The canonical POC
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

The mandatory-plus-recency control, C0, uses the same actually persisted ledger
and capture as lexical C. Run four fresh C0 continuations paired with the four
existing C continuations, plus C0's own two-call measurement of its complete
serialized pack. Report separate case-clustered paired 95% intervals for recall,
answer quality, and stale influence; recall alone cannot decide the original
three-metric gate. Retain all C0 raw evidence, usage, and safety outcomes. Report
these additional experiment calls separately from primary A/B/C lifecycle
economics, without recharging or sharing capture across independent lifecycles.

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

**Current deterministic gold retrieval passes; the complete live experiment and
production are held.** All 48 long cases retain 100% of required facts and
mandatory boundaries/decisions in 1,840–1,974 UTF-8 bytes, with byte-identical
FTS5/scan packs. The earlier 64.2857% overlap-plus-recency result is historical.
See the [current POC evidence report](../experiments/nerd-context/results/report.md)
for source hashes, measurements, and archived diagnostic evidence.

The completed 40-call diagnostic used `gpt-5.6-terra`, low reasoning effort,
and `codex-cli 0.153.4`. Generated structured capture cost 40,236 billable tokens;
four continuations cost 57,242, totaling 97,478 versus full history's 101,855:
**4.30% savings and break-even at four resumptions**. Gold structured cost 58,937
versus 101,857, saving 42.14%, but oracle capture cannot pass the generated gate.
The diagnostic's task wording and full-observation rubric were inconsistent;
its recorded quality scores do not establish semantic information loss. The
current symmetric protocol requests all active current-scope facts and complete
observation text, and **has not run live**. Dedicated adversarial controls and a
complete phase comparison also remain unrun.

Retaining the diagnostic's measured input shells while granting zero structured
output cost and removing the measured pack gives an optimistic 96,309-token
cost, or at most 5.45% savings against its observed full-history total. More
generally, for fixed shell `S`, history `H`, two capture calls consuming that
history once in total, four resumptions, and zero pack/output cost:

```text
full_history_cost = 4(S + H)
structured_cost = 6S + H
40% savings requires H >= 18S / 7
break-even within two resumptions requires H >= 2S
```

At the observed roughly 14,000-token shell, those conditions require about
36,000 and 28,000 history tokens, outside this design's 8,000–24,000 range.
This conditional frozen-pipeline bound justifies holding the planned 7,359-call
run, including the previously omitted quality/stale ablation controls. It does
not establish impossibility for another faithful architecture.
Fixed overhead, cached input, and capture work cannot be excluded to obtain a
passing result. All user thresholds and independent phase requirements remain
unchanged; the current tracked preflight is `inconclusive`, not a complete live
pass or rejection.

Competent generated capture may retain only the few relevant facts, leaving
recall equal under lexical ranking and recency. This does not settle the
unmeasured answer-quality or stale-influence ablation. The corrected task and
complete three-metric control protocol remain unrun. Do not force irrelevant
capture or weaken a strong summary. A simpler checkpoint or capture integrated
into genuinely required task turns is an **unproven direction**, not an approved
replacement or passing result. Any new design requires faithful matched work,
complete billable accounting, fresh preregistration, and independent review.

Before future evidence, resolve the production hydration contract: the tested
serializer contains only `kind`, `value`, `source`, and `source_ref`, while
production also needs IDs, anchors, and response metadata. Define and measure
the complete model-visible response without treating metadata as free. Changing
the tested serializer requires fresh evidence under the unchanged pack ceiling.
The production plan still limits capture to **20 records**; the POC permits 30.
That discrepancy must be reconciled before future evidence, without silently
expanding production's limit. Neither serializer nor capture limit changes here.

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

Hold further live benchmarking and production under the current design. Preserve
the evidence, unchanged gates, single-ID boundary, and separation from Nerd
Memory. A future feasible POC needs its own reviewed preregistration; neither
the deterministic retrieval pass nor an unproven simpler alternative authorizes
the queued production plan.

## Related Material

- [Nerd Context implementation plan](../plans/2026-08-27-nerd-context.md)
