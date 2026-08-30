# Nerd Context Implementation Plan

**Goal:** Add a public `nerd-context` skill that persists one ID-addressed context in a private local SQLite store and hydrates a bounded, source-linked context pack through MCP, reducing total model tokens without weakening task quality, freshness, context-ID isolation, or action authority.

**Approach:** First run a falsifiable three-arm experiment against full history and an equal-budget free-form summary. Only if the structured arm passes every gate, build a separate append-only context runtime and `nerd-context-tools` MCP server, then compose it after Smart and Memory but before the selected endpoint route. Address Context only by one runtime-generated opaque `context_id`: supplying it resumes that exact Context across sessions, while omitting it atomically creates a fresh Context and returns the new ID. Keep deterministic retrieval, explicit supersession, and abstention; defer embeddings, fuzzy ID lookup, context enumeration, remote sync, and autonomous prompt injection.

**Scope:** Create the POC harness, `nerd-context` skill package, SQLite/CLI runtime, MCP adapter, Smart/Memory/hook composition, installer wiring, tests, CI coverage, and README documentation. Preserve `nerd-memory` as a separate behavioral/evidence store. Do not merge databases, store raw transcripts or hidden reasoning, infer permission from context, add third-party runtime dependencies, commit credentials, publish benchmarks, or implement semantic retrieval.

**Proof:** The experiment must meet the preregistered token, quality, recall, stale-context, isolation, break-even, and latency gates; deterministic engine/security/MCP tests must pass; installation must register both Nerd servers for all supported clients; the skill validator, full unit suite, compile check, and benchmark-plan validation must remain green.

**Sub-Agent Driven:** YES — explicitly requested. Independently completable tasks use `nerd-smart`; sub-agents inherit the current model because no model override was requested. Implementation remains unauthorized until a new Execute Focus Record.

## Confirmed Direction and Blocking Unknown

The selected direction is an append-only typed ledger with record kinds `goal`, `boundary`, `decision`, `evidence`, `open_question`, and `checkpoint`; one exact `context_id`; provenance; explicit supersession; deterministic lexical retrieval; and a bounded pack. `context_recall` accepts an optional ID: an ID explicitly present in the current activation or delegated sub-agent handoff resumes only that Context, while omission creates a fresh `ctx_<192-bit-random>` Context. A returned ID is displayed for the caller to supply again, but it never becomes hidden active-session state. IDs are never inferred from earlier turns, prompt similarity, workspace, task, thread, or title, and the runtime never enumerates alternatives.

Tasks 2–7 are blocked until Task 1 proves that active records from one exact Context ID retain at least 95% of required facts inside the actual deployable 2,048-byte ceiling, structured context materially beats an equal-budget summary, and lexical retrieval contributes material value over mandatory-plus-recency retrieval. A passing result with no material lexical contribution stops for a new Brainstorm/Plan of the simpler checkpoint capsule; lexical misses that prevent the recall gate stop for Brainstorm before any semantic experiment. This plan proceeds only with `verdict=pass` and `retrieval_design=typed_lexical`; it never silently substitutes another design.

## File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `docs/experiments/nerd-context/README.md` | Create | Preregister arms, corpus, metrics, gates, run commands, and interpretation rules. |
| `docs/experiments/nerd-context/cases.json` | Create | Define 48 long-context cases, 12 negative controls, required facts, stale facts, boundaries, and exact Context IDs. |
| `docs/experiments/nerd-context/fixtures.py` | Create | Validate and materialize deterministic synthetic histories and gold records. |
| `docs/experiments/nerd-context/baselines.py` | Create | Build full-history and equal-budget summary arms. |
| `docs/experiments/nerd-context/structured.py` | Create | Implement the disposable typed-ledger POC and deterministic bounded retrieval. |
| `docs/experiments/nerd-context/bench.py` | Create | Run randomized paired arms, capture usage, score results, bootstrap intervals, and enforce gates. |
| `docs/experiments/nerd-context/test_experiment.py` | Create | Prove fixture, metric, leakage, ordering, abstention, and gate behavior without live model calls. |
| `docs/experiments/nerd-context/results/report.md` | Create | Record the human-readable POC verdict, limitations, immutable source-run ID, and aggregate evidence. |
| `docs/experiments/nerd-context/results/verdict.json` | Create | Store the machine-checkable aggregate gates, run ID, raw-manifest digest, and selected retrieval design without raw prompts or responses. |
| `benchmarks/results/nerd-context/` | Generate (ignored) | Hold immutable raw run manifests/output plus the explicit selected-run reference under the repository's existing ignored results root. |
| `benchmarks/nerdbench/adapters.py` | Modify | Put Context POC conditions on Codex’s existing isolated user-config/rules path. |
| `tests/test_benchmark_adapters.py` | Modify | Prove Context arms receive isolation flags and no unrelated MCP configuration. |
| `skills/nerd-context/SKILL.md` | Create | Define activation, hydration, capture, lifecycle, authority, transport, and stopping rules. |
| `skills/nerd-context/agents/openai.yaml` | Create | Publish display metadata and implicit-invocation policy. |
| `skills/nerd-context/references/context-contract.md` | Create | Specify schema, identity, provenance, lifecycle, retrieval, security, migration, and evaluation contracts. |
| `skills/nerd-context/references/research.md` | Create | Record verified design/evaluation influences without adding runtime dependencies. |
| `skills/nerd-context/references/recall-and-capture.md` | Create | Give the progressive workflow for supplied-ID resume, omitted-ID creation, revalidation, capture, and abstention. |
| `skills/nerd-context/references/transport-preflight.md` | Create | Require live MCP discovery first and gate CLI fallback per activation. |
| `skills/nerd-context/scripts/context.py` | Create | Provide the standard-library SQLite engine and behaviorally equivalent JSON CLI. |
| `skills/nerd-context/scripts/mcp_server.py` | Create | Expose the warm three-tool stdio MCP surface as thin adapters over `ContextStore`. |
| `tests/test_context_engine.py` | Create | Cover fresh-ID creation, exact-ID resume, persistence, supersession, deterministic packing, overflow, and CLI parity. |
| `tests/test_context_security.py` | Create | Cover ID isolation, provenance, secret rejection, stale records, prompt injection, replay, forgetting, and schema fencing. |
| `tests/test_context_mcp.py` | Create | Cover the exact MCP inventory, schemas, CLI equivalence, error mapping, isolation, and restart behavior. |
| `skills/nerd-smart/SKILL.md` | Modify | Establish Smart → Memory → Context → route middleware order without changing endpoints. |
| `skills/nerd-smart/scripts/prompt_hook.py` | Modify | Auto-activate Context with exact-ID, non-authoritative local access. |
| `skills/nerd-memory/SKILL.md` | Modify | State the non-overlap and forbid current-Context storage or automatic Context-to-Memory promotion. |
| `scripts/validate_skills.py` | Modify | Register the public skill, references, and scripts. |
| `scripts/install_mcp.py` | Modify | Register `nerd-context-tools` and its exact tool inventory. |
| `scripts/install.sh` | Modify | Install both MCP servers independently and keep registration failures non-fatal. |
| `tests/test_skill_structure.py` | Modify | Pin the expanded public-skill/reference/script registries. |
| `tests/test_skill_contracts.py` | Modify | Pin Context activation, authority, retrieval, transport, composition, and separation contracts. |
| `tests/test_install_mcp.py` | Modify | Prove the Context server definition, copied runtime, health check, and coexistence with Memory. |
| `tests/test_install.py` | Modify | Prove all clients receive both MCP servers and the updated hook contract. |
| `tests/test_workflows.py` | Modify | Require CI and release compile checks to include `skills/`. |
| `.github/workflows/ci.yml` | Modify | Compile skill runtime scripts before unit and contract tests. |
| `.github/workflows/release.yml` | Modify | Apply the compile gate and add Context to exact release skill counts, install loops, and metadata checks. |
| `README.md` | Modify | List `nerd-context`, explain its boundary from Memory, install behavior, local storage, and proof status. |
| `tests/test_readme.py` | Modify | Pin one public row and the essential Context claims without allowing README bloat. |

## Tasks

### Task 1: Run the falsifiable Context POC

**Outcome:** A reproducible three-arm report either unlocks the structured-ledger implementation or stops the project with a falsified hypothesis.

**Focus Record**

- **Intention:** Measure whether bounded structured context saves net tokens while preserving quality and freshness better than a same-budget summary.
- **Expectation:** Execute
- **Scope:** Synthetic experiment artifacts, Codex adapter isolation, adapter tests, and local result report only; no public skill, installer, hook, or production runtime changes.
- **Role:** Evaluation engineer
- **Skills:** `nerd-smart`, `nerd-execute`
- **Review Required:** YES — `nerd-review`
- **Sub-agent Model:** inherit

**Files:** `docs/experiments/nerd-context/{README.md,cases.json,fixtures.py,baselines.py,structured.py,bench.py,test_experiment.py,results/report.md,results/verdict.json}`, ignored `benchmarks/results/nerd-context/`, `benchmarks/nerdbench/adapters.py`, `tests/test_benchmark_adapters.py`

1. Add failing tests that require exactly 12 resumption, 12 cross-session, 12 supersession/stale, 12 distractor/isolation/authority, and 12 short negative-control cases; three primary arms; a structured lexical-versus-mandatory-plus-recency ablation; deterministic seeded ordering; no future-fact leakage; exact Context-ID isolation; fresh creation whenever the current activation omits the ID; one canonical pack serializer; a hard 2,048 UTF-8-byte and 2,048 measured-token ceiling for both summary and structured packs; stable bootstrap output; and distinct pass/inconclusive/reject verdicts.
2. Run `python3 docs/experiments/nerd-context/test_experiment.py -v`; expect import/file failures because the experiment does not exist.
3. Implement the synthetic corpus and disposable arms. Every cross-session resume prompt must independently state the current intention, endpoint-relevant request, scope, and any required action authority plus the Context ID. Add negative cases where an ID-only “continue” request stops for clarification before `context_recall`; stored records may inform work only after Smart resolves the current request.
4. Restrict the live POC to Codex until another adapter has an equivalent isolation contract. Add `context-full-history`, `context-summary`, and `context-structured` to `CodexAdapter`’s existing `--ephemeral --ignore-user-config --ignore-rules` path. Materialize every run in a fresh temporary workspace without repository rules, installed skills, hooks, MCP definitions, or persisted Context/Memory state; retain only the client’s existing authentication path and pass the identical explicit tool surface to every arm. Tests inspect the built command/environment and fail if unrelated configuration can load.
5. Count every capture/update and continuation call with `billable_tokens = input_tokens + output_tokens` from existing `benchmarks.nerdbench.adapters.usage_tokens`; cached input and reasoning output are diagnostic subsets and are never added again. Mark a run ineligible when input or output usage is missing. Keep gold-record retrieval and model-generated capture results separate.
6. Implement these preregistered measures: paired total-token savings; weighted required-fact quality; active-fact recall; boundary/current-decision recall; retrieval precision; stale influence; cross-scope/authority violations; pack size; p50/p95 retrieval latency; and resumption break-even. Use a fixed seed and paired 95% bootstrap intervals.
7. Serialize each summary and structured pack with the exact canonical UTF-8 envelope intended for production and reject any payload over `DEPLOYABLE_MAX_PACK_BYTES = 2_048` before a model call. Measure that same serialized segment with a paired empty-pack control call using the identical model, system/task shell, explicit tool surface, and fixed newline-delimited sentinel boundaries. Define `pack_tokens = input_tokens(with_segment) - input_tokens(empty_segment)`; exclude both control calls from production economics, reject negative/inconsistent/missing deltas, and unit-test boundary stability with fixed adapter event fixtures. Every eligible summary and structured segment must satisfy both ceilings; any later serializer change invalidates the report.
8. Run `python3 docs/experiments/nerd-context/test_experiment.py -v` and `python3 -m unittest tests.test_benchmark_adapters -v`; expect all deterministic experiment/isolation contracts to pass.
9. Run `python3 docs/experiments/nerd-context/bench.py run --config benchmarks/config.json --agent codex --repetitions 3 --selection-file benchmarks/results/nerd-context/selected-run.json`. The command writes immutable raw evidence under `benchmarks/results/nerd-context/<run_id>/` and atomically writes the selected run ID plus manifest digest to the named ignored selection file. Then run `python3 docs/experiments/nerd-context/bench.py report --selection-file benchmarks/results/nerd-context/selected-run.json`; it refuses mutable/mismatched evidence and atomically writes tracked `report.md` and `verdict.json` containing the same run ID/digest. Finally run `python3 docs/experiments/nerd-context/bench.py check --result docs/experiments/nerd-context/results/verdict.json --require typed-ledger-pass`.
10. Classify `pass` only when all strict long-context gates hold: median token savings ≥40% and lower 95% bound ≥30%; quality-delta lower bound ≥−3 percentage points; active-fact recall ≥95%; boundary/current-decision recall 100%; stale influence ≤2% with zero boundary/permission stale incidents; zero wrong-ID, missing-ID reuse, context-enumeration, or stored-authority failures; median break-even ≤2 resumptions and p90 ≤4; p95 retrieval ≤200 ms at 10,000 records; every pack within both deployable ceilings; and structured context beats summary by ≥5 quality points or ≥50% stale-error reduction. Gate the short controls separately: on every eligible paired repetition, Context must preserve every full-history rubric item, add at most 192 billable tokens, create exactly one new empty Context with a never-before-seen ID, make no capture call and persist zero records; across all 36 repetitions, added create/recall latency p95 must be ≤200 ms and prior IDs must never be reused.
11. Apply the complete gate independently to the gold-record phase and the generated-capture phase. Generated capture must also pass capture precision/recall, supersession, isolation, stored-authority, quality, and total capture-plus-continuation token gates; oracle retrieval cannot unlock production on its behalf.
12. Run the structured lexical/no-lexical ablation through both phases, exercising both the SQLite FTS5 implementation and the deterministic normalized-term fallback with byte-identical pack fixtures. Set `retrieval_design=typed_lexical` only when lexical ranking improves at least one preregistered primary metric—active-fact recall, answer quality, or stale-incident rate—with a paired 95% interval excluding zero, no isolation/authority regression, and p95 retrieval ≤200 ms at 10,000 records in both index modes. If mandatory-plus-recency meets all gates without material lexical contribution, set `retrieval_design=capsule_candidate` and stop for a new Brainstorm/Plan. If lexical misses still prevent ≥95% recall, return `inconclusive` and Brainstorm before testing semantic retrieval.
13. Classify `reject` when median savings are <20%, quality delta is <−5 percentage points, any short-control safety/quality invariant fails, or any permission, boundary, wrong-ID, missing-ID reuse, enumeration, or stored-authority failure occurs. A short-control overhead/latency miss without a safety or quality miss is `inconclusive`. Classify all other results `inconclusive`. `reject`, `inconclusive`, and `pass` with a non-`typed_lexical` retrieval design all block Task 2; the report preserves the reason and records the exact model/version/date so hosted-model drift is visible.

**Proof:** `python3 docs/experiments/nerd-context/bench.py check --result docs/experiments/nerd-context/results/verdict.json --require typed-ledger-pass` → exit 0 only when both gold-record and generated-capture phases, deployable byte/token ceilings, short-control gates, both lexical index modes, and the `retrieval_design=typed_lexical` ablation pass; all other verdict/design combinations are distinct nonzero outcomes.

### Task 2: Create the CLI-first public Context skill and deterministic engine

**Outcome:** `nerd-context` is a valid public skill with a private, schema-versioned SQLite engine whose exact-ID create/resume lifecycle and CLI are fully tested before transport integration.

**Focus Record**

- **Intention:** Establish the smallest safe persisted Context contract and engine proven by the POC.
- **Expectation:** Execute
- **Scope:** New skill package, core/contract/security tests, and skill registries; no MCP, hook, installer, or README behavior yet.
- **Role:** Persistence and skill-contract engineer
- **Skills:** `nerd-smart`, `nerd-execute`, `skill-creator`
- **Review Required:** YES — `nerd-review`
- **Sub-agent Model:** inherit

**Files:** `skills/nerd-context/{SKILL.md,agents/openai.yaml,references/context-contract.md,references/research.md,scripts/context.py}`, `scripts/validate_skills.py`, `tests/{test_context_engine.py,test_context_security.py,test_skill_structure.py,test_skill_contracts.py}`

1. Add failing structure/contract tests for the new public skill and failing engine/security tests for the interfaces and invariants below. Run `python3 -m unittest tests.test_context_engine tests.test_context_security tests.test_skill_structure tests.test_skill_contracts -v`; expect missing skill/module/registry failures.
2. Create `ContextStore` with default path `${NERD_CONTEXT_DB}`, else `${CODEX_HOME}/nerd-context/context.sqlite3`, else `~/.codex/nerd-context/context.sqlite3`; user-only directory/file permissions; symlink refusal; foreign keys; full sync; secure delete; exclusive schema migrations; and persistent stale-writer triggers modeled on `MemoryStore` without sharing its database.
3. Create schema-versioned `metadata`, `contexts`, `records`, `record_events`, `confirmation_ref_tombstones`, and `forgotten_contexts`. `contexts.context_id` is the sole public identity with canonical grammar `^ctx_[a-z2-7]{38}[aiqy]$`: generate 24 bytes with `secrets.token_bytes(24)`, encode lowercase RFC 4648 base32 without padding, validate case-sensitively, and require decode/re-encode equality before lookup. Insert under the unique primary key and retry a collision up to eight times in the same transaction before a structured storage failure. Callers cannot choose IDs. `recall(context_id=None, ...)` atomically creates a fresh empty Context and returns its ID. A supplied unknown or forgotten ID returns `not_found` and never creates, searches, lists, or suggests another Context.
4. Make records append-only with kind, minimal structured value, source class, `source_ref`, status, revision, timestamps, optional repository-relative anchors/content hashes, and optional `supersedes_id`. An atomic supersession makes the predecessor inactive but auditable. Contexts persist until explicit preview-bound forget; checkpoints are ordinary records, so no task/open/close lifecycle or secondary locator is required.
5. Implement these canonical engine signatures and mirror them unchanged in CLI JSON arguments/results:

   ```python
   recall(*, context_id=None, query, activation_ref, max_bytes=None) -> {status, created, context_id, records, conflicts, overflow, serialized_bytes, estimated_tokens, authority}
   capture(context_id, *, records, capture_ref) -> {context_id, accepted_ids, superseded_ids, duplicate}
   inspect(context_id, *, activation_ref, cursor=None, limit=50) -> {context, record_metadata, next_cursor}
   preview_forget(context_id, *, preview_ref) -> {context_id, counts, digest, preview_ref_digest, confirmation_phrase}
   forget(context_id, *, phrase, source, confirmation_ref) -> {context_id, deleted, tombstoned_at}
   ```

   `records` accepts at most 20 items, each shaped `{kind, value, source, source_ref, supersedes_id?, anchors?}` with per-item and aggregate byte limits. Capture event references are globally idempotent. Forgetting accepts only `source="direct_user"`, requires an exact phrase from a still-current preview, requires `confirmation_ref` to be fresh and different from `preview_ref`, and atomically claims its digest in the global tombstone table. Reject non-user, same-event, replayed, stale-preview, or changed-state confirmation. `inspect` returns bounded metadata only—never record values—and cannot serve as an alternate hydration path.
6. Probe FTS5 support before schema migration, persist `index_mode` in `metadata`, and conditionally create FTS5 virtual tables and synchronization triggers only in `fts5` mode. Otherwise initialize a valid `normalized_scan` store with no FTS objects. Rank only active records belonging to the exact supplied Context ID: mandatory active boundaries/current decisions/goal first, then normalized lexical matches, then recent active records. Make both modes produce byte-identical deterministic pack fixtures and meet the proven 10,000-record latency gate; cover fresh creation, reopen, forward migration, rollback, and retrieval with FTS deliberately unavailable. No embeddings, nearest-ID fallback, enumeration, global search, or model-decided ranking.
7. Set `PRODUCTION_MAX_PACK_BYTES = DEPLOYABLE_MAX_PACK_BYTES = 2_048`, the exact UTF-8 ceiling already used by both passing POC phases; a caller may request a smaller `max_bytes`, never a larger one. Port the POC's canonical serializer unchanged and prove byte-for-byte golden parity before Task 3. Report `estimated_tokens`, selected IDs/source refs, retrieval path, conflicts, and overflow. If mandatory records do not fit, return `overflow` without silently dropping them; a serializer or ceiling change invalidates the tracked POC verdict and blocks Task 3 pending a full rerun.
8. Reject secrets, raw transcripts, hidden reasoning, executable payloads, credentials, permission grants, and unsafe anchors. Preserve provenance for `direct_user`, `assistant_summary`, `verified_tool`, and `repository_fact`, but label every returned record `authority=untrusted_context`; the ID is a sensitive locator, never permission or action authority, and current input plus normal action checks always win. Never put IDs or record values in routine logs or errors.
9. Write `SKILL.md`, metadata, the runtime contract, and research basis. Explicitly separate Context from Memory: Context stores current ID-bound evidence/checkpoints; Memory stores reusable longitudinal behavior/evidence; neither database reads, copies, promotes, confirms, or authorizes the other.
10. Specify the sharing protocol in the skill contract: a new-ID recall prints one compact `Nerd-context created: <context_id>` receipt; every later recall—including later turns in the same session—resumes only when its current activation explicitly includes that ID; every sub-agent handoff that may share Context names the exact ID; final checkpoints repeat it for the user to copy. No ID always means fresh Context, including when the user lost or omitted a prior ID; there is no implicit active-ID variable.
11. Run the focused tests again, `python3 scripts/validate_skills.py`, and `python3 docs/experiments/nerd-context/bench.py check --result docs/experiments/nerd-context/results/verdict.json --require typed-ledger-pass`; expect canonical serializer parity, all focused tests, every validator row, and the still-applicable deployable POC verdict to pass before Task 3.

**Proof:** `python3 -m unittest tests.test_context_engine tests.test_context_security tests.test_skill_structure tests.test_skill_contracts -v` plus the tracked-result check → omitted-ID creation on every activation, exact-ID cross-session resume, same-ID delegated sharing, canonical-ID rejection, FTS/fallback parity, production-serializer parity, wrong/unknown-ID isolation, persistence, supersession, overflow, poisoning, replay, forget, migration rollback, and stale-writer tests pass.

### Task 3: Add the warm MCP surface and guarded transport fallback

**Outcome:** Three `nerd-context-tools` calls expose the engine through one warm process, with exact CLI equivalence and fail-closed schema handling.

**Focus Record**

- **Intention:** Reduce context lifecycle round trips without moving policy out of the deterministic engine.
- **Expectation:** Execute
- **Scope:** Context MCP adapter, transport/capture references, MCP tests, and required-file registries only.
- **Role:** MCP integration engineer
- **Skills:** `nerd-smart`, `nerd-execute`
- **Review Required:** YES — `nerd-review`
- **Sub-agent Model:** inherit

**Files:** `skills/nerd-context/scripts/mcp_server.py`, `skills/nerd-context/references/{transport-preflight.md,recall-and-capture.md}`, `skills/nerd-context/SKILL.md`, `scripts/validate_skills.py`, `tests/{test_context_mcp.py,test_skill_structure.py,test_skill_contracts.py}`

1. Add failing MCP tests asserting the exact inventory `context_recall`, `context_capture`, and `context_inspect`; strict JSON schemas matching Task 2; annotations; structured/text payload equality; omitted-ID fresh creation; exact-ID resume and isolation; lower-only pack budgets; bounded metadata-only inspection; CLI equivalence; domain-error parity; malformed-request survival; notification behavior; and permanent `restart_required` after schema mismatch.
2. Run `python3 -m unittest tests.test_context_mcp tests.test_skill_contracts tests.test_skill_structure -v`; expect missing server/tool/reference failures.
3. Adapt the canonical engine methods without changing their shapes. `context_recall` creates a fresh Context when `context_id` is omitted or returns the exact supplied Context pack; capture remains atomic; inspect is bounded metadata-only. No tool discovers fuzzy IDs, lists Contexts, changes Smart’s endpoint, confirms Memory, grants action, or includes destructive forget.
4. Implement a dependency-free stdio server following `skills/nerd-memory/scripts/mcp_server.py`: one lazy `ContextStore`, adapter-side strict argument validation, engine-owned policy, safe structured error mapping, no grant/secret echo, and fail-closed restart state.
5. Add transport preflight: search the callable registry for all three tools on every activation; prefer MCP; distinguish missing/disabled/registered-not-live/unknown states; use the same exact short fallback gate as Memory; allow the CLI only after the user rejects MCP recovery; never launch a server manually or persist transport choice.
6. Add recall/capture guidance: recall only after Smart/Memory resolve the current intention, endpoint, scope, and ordinary authority from the current prompt; an ID-only or otherwise ambiguous “continue” request stops for clarification before hydration. Resume only the exact ID explicitly present in the current activation or delegated handoff; otherwise create and display a fresh one, even if an earlier turn used another ID. Revalidate anchored facts before reliance; capture only minimal durable Context state after a decision, verified discovery, checkpoint, or stop; never store entire prompts/responses; use CLI-only preview/forget for deletion.
7. Register the new references/scripts and run the focused tests plus `python3 scripts/validate_skills.py`; expect pass.

**Proof:** `python3 -m unittest tests.test_context_mcp tests.test_context_engine tests.test_context_security -v` → exact tool inventory, fresh-ID creation, exact-ID sharing/isolation, CLI/MCP equivalence, transport-independent policy, and restart fencing pass.

### Task 4: Compose Context with Smart, Memory, and the installed hook

**Outcome:** Every hook-activated request follows one explicit middleware order and Context can shorten rediscovery without changing intent, endpoint, permission, or Memory state.

**Focus Record**

- **Intention:** Integrate Context into the Nerd lifecycle without creating a second router or authority channel.
- **Expectation:** Execute
- **Scope:** Smart composition, hook activation, Memory separation language, and contract/install-hook tests; no engine or installer registration changes.
- **Role:** Workflow-contract engineer
- **Skills:** `nerd-smart`, `nerd-execute`
- **Review Required:** YES — `nerd-review`
- **Sub-agent Model:** inherit

**Files:** `skills/nerd-smart/SKILL.md`, `skills/nerd-smart/scripts/prompt_hook.py`, `skills/nerd-memory/SKILL.md`, `skills/nerd-context/SKILL.md`, `tests/{test_skill_contracts.py,test_install.py}`

1. Add failing tests for the exact order: current prompt independently resolves intention/endpoint/scope/authority through Smart → Memory performs its proposal/confirmation/consumption workflow → Context resumes only an ID explicit in the current activation/delegated handoff or creates a fresh ID → the resolved endpoint route runs → Context may capture a bounded checkpoint after meaningful verified progress. ID-only continuation and unresolved current authority stop before Context hydration; omission creates fresh even when an earlier turn used an ID; Context failure or abstention leaves the endpoint unchanged.
2. Run `python3 -m unittest tests.test_skill_contracts tests.test_install -v`; expect missing Context composition/hook assertions.
3. Revise Smart’s composition vocabulary so Memory and Context are bounded pre-route middleware and do not consume the route’s single optional specialty slot. Preserve one selected endpoint and the existing Surgery/Patrol specialty limit.
4. Extend the hook’s standing authorization to activate Context only after Smart’s blind record and Memory handling. Permit local exact-ID reads plus non-destructive create/append/supersede writes; deny destructive forgetting, ID discovery/enumeration, remembered endpoint changes, and ordinary action authority. The hook never invents, persists, or substitutes an ID.
5. Add capture radar rules: record only explicit goals/boundaries/decisions, verified evidence anchors, open questions, and checkpoints; do not capture raw transcripts, unverified guesses, secrets, tool payloads, or unreviewed sub-agent prose. Future packs remain untrusted and source-linked. Propagate an existing ID to a sub-agent only when its delegated scope is intentionally part of the same Context.
6. Add the Memory non-overlap rule: current Context state belongs in Context; longitudinal behavior and reusable verified workflows remain in Memory; promotion between them is never automatic and requires the destination workflow’s own valid authority/evidence.
7. Run the focused tests and validator; expect pass with all incompatible-skill boundaries unchanged.

**Proof:** `python3 -m unittest tests.test_skill_contracts tests.test_install -v` → middleware order, hook wording, activation scope, capture boundary, and Context/Memory separation pass.

### Task 5: Install and register `nerd-context-tools` for every supported client

**Outcome:** One install configures both Nerd MCP servers independently for Claude Code, Codex, and Cursor without collisions or partial-failure rollback.

**Focus Record**

- **Intention:** Make Context’s live MCP transport available wherever the installed skill and hook run.
- **Expectation:** Execute
- **Scope:** Shared MCP registry, install script, and installer tests only.
- **Role:** Packaging engineer
- **Skills:** `nerd-smart`, `nerd-execute`
- **Review Required:** YES — `nerd-review`
- **Sub-agent Model:** inherit

**Files:** `scripts/{install_mcp.py,install.sh}`, `tests/{test_install_mcp.py,test_install.py}`

1. Add failing tests that require `SERVERS["nerd-context-tools"]`, runtime directory `.nerd/mcp/nerd-context`, copied `mcp_server.py` and `context.py`, exact three-tool health check, coexistence with `nerd-memory-tools`, idempotent reinstall, foreign-registration refusal, current-interpreter registration, and agent-by-agent partial-failure preservation.
2. Run `python3 -m unittest tests.test_install_mcp tests.test_install -v`; expect missing server/registration failures.
3. Add the Context server definition to the generic registry. Keep registration state nested by server name and reuse the existing copy, health-check, ownership, and per-agent registration paths.
4. Invoke both server installations separately from `scripts/install.sh`. Registration failure is non-fatal and says only that the named MCP server is unavailable and its activation will run transport preflight; it must not promise automatic CLI fallback. Correct the existing Memory warning at the same integration point. Failure of one server does not roll back skills, hooks, the other server, or successful agents.
5. Run the focused tests twice to exercise idempotency; expect pass and state containing both server keys for all three clients.

**Proof:** `python3 -m unittest tests.test_install_mcp tests.test_install -v` → both servers install, coexist, recover idempotently, and preserve successful registrations under partial failure.

### Task 6: Document the released boundary and extend CI proof

**Outcome:** Users can understand what Context stores, when it activates, how it differs from Memory, and what evidence supports it; CI compiles and tests every shipped runtime.

**Focus Record**

- **Intention:** Finish user-facing and continuous-verification surfaces without overstating experimental evidence.
- **Expectation:** Execute
- **Scope:** README, README/workflow tests, and CI/release compile commands only.
- **Role:** Release documentation engineer
- **Skills:** `nerd-smart`, `nerd-execute`
- **Review Required:** YES — `nerd-review`
- **Sub-agent Model:** inherit

**Files:** `README.md`, `tests/{test_readme.py,test_workflows.py}`, `.github/workflows/{ci.yml,release.yml}`

1. Add failing README tests requiring exactly one `nerd-context` table row and concise claims for local SQLite, explicit-current-activation ID resume, omitted-ID fresh creation even within one session, bounded source-linked packs, sensitive IDs/untrusted evidence, Memory separation, MCP-first guarded fallback, and the measured POC status. Add workflow tests requiring `python3 -m compileall -q scripts skills benchmarks tests`, the deterministic experiment test, and `bench.py check --result docs/experiments/nerd-context/results/verdict.json --require typed-ledger-pass` in both CI and release without live model calls.
2. Run `python3 -m unittest tests.test_readme tests.test_workflows -v`; expect missing text/compile-scope failures.
3. Update README without publishing raw prompts, local paths, unsupported benchmark generalizations, or an “infinite prompt” claim. Link the experiment report and describe persisted storage as durable until explicit forget, while active hydration remains bounded. State that lost IDs are intentionally undiscoverable and can leave orphan Contexts until the whole local store is removed, exact IDs are sensitive task metadata, possession grants lookup but no action authority, and the measured quality/token claim is Codex-only and may drift with hosted model versions rather than generalizing to Claude Code or Cursor.
4. Expand compile commands to include `skills`. Add the deterministic `test_experiment.py` command and tracked `verdict.json` gate to CI and release; these validate fixtures, scoring, and the previously selected passing report but never execute live benchmarks. Update `.github/workflows/release.yml` everywhere it hard-codes the public skill count or name set: isolated package discovery, per-skill install loops, exact installed-directory assertions, and `agents/openai.yaml` implicit-invocation checks. Update `tests/test_workflows.py` to pin all new commands, the new count, and isolated `nerd-context` installation/metadata verification.
5. Preserve the existing unit, validator, and benchmark-plan gates alongside the new deterministic experiment/report gates; run focused tests, then the final verification below.

**Proof:** `python3 -m unittest tests.test_readme tests.test_workflows -v` → public listing and CI/release contract pass.

### Task 7: Run the complete release gate and inspect generated state

**Outcome:** The final branch proves the experiment decision, skill/runtime behavior, installation, repository contracts, and regression safety with no unexpected tracked artifacts.

**Focus Record**

- **Intention:** Demonstrate that the complete Context boundary works and existing Nerd behavior remains intact.
- **Expectation:** Execute
- **Scope:** Read-only verification plus disposable test/build output; no commit, push, tag, deployment, or publication.
- **Role:** Release verifier
- **Skills:** `nerd-smart`, `nerd-execute`
- **Review Required:** YES — `nerd-review`
- **Sub-agent Model:** inherit

**Files:** All files above; no additional product files.

1. Run `python3 -m compileall -q scripts skills benchmarks tests`; expect exit 0.
2. Run `python3 scripts/validate_skills.py`; expect a `PASS nerd-context` row plus all existing skill, routing, reference, and attribution rows.
3. Run `python3 -m unittest discover -s tests -v`; expect the complete suite to pass with no skipped Context safety/transport tests.
4. Run `python3 benchmarks/run.py plan --config benchmarks/config.json`; expect benchmark configuration validation to succeed without executing live release benchmarks.
5. Run `python3 docs/experiments/nerd-context/test_experiment.py -v`, `python3 -m unittest tests.test_benchmark_adapters -v`, and `python3 docs/experiments/nerd-context/bench.py check --result docs/experiments/nerd-context/results/verdict.json --require typed-ledger-pass`; expect the isolation harness to pass, both experiment phases and short controls to report `pass`, both index modes to meet the latency/parity gate, and the ablation to report `retrieval_design=typed_lexical`.
6. Run `git status --short`, `git check-ignore benchmarks/results/nerd-context/`, and inspect the diff; expect only the tracked paths named in this plan plus the plan itself, with raw POC runs confined to the declared ignored root and no SQLite databases, credentials, caches, raw model output elsewhere, or unrelated changes tracked.

**Proof:** Every command exits 0 and the final diff contains only the declared Context, integration, test, documentation, workflow, experiment-report, and plan paths.

## Final Verification

- `python3 docs/experiments/nerd-context/test_experiment.py -v` → deterministic experiment contract passes.
- `python3 -m unittest tests.test_benchmark_adapters -v` → Codex context conditions run in the same isolated configuration as the other benchmark arms.
- `python3 docs/experiments/nerd-context/bench.py check --result docs/experiments/nerd-context/results/verdict.json --require typed-ledger-pass` → both preregistered phases, short controls, deployable ceilings, and both index modes pass; the selected retrieval design is `typed_lexical`.
- `python3 -m unittest tests.test_context_engine tests.test_context_security tests.test_context_mcp -v` → engine, security, and MCP contracts pass.
- `python3 -m unittest tests.test_skill_structure tests.test_skill_contracts tests.test_install_mcp tests.test_install tests.test_readme tests.test_workflows -v` → family integration, packaging, docs, and CI contracts pass.
- `python3 -m compileall -q scripts skills benchmarks tests` → all shipped Python compiles.
- `python3 scripts/validate_skills.py` → all public skills, references, scripts, routing, and attribution validate.
- `python3 -m unittest discover -s tests -v` → full repository suite passes.
- `python3 benchmarks/run.py plan --config benchmarks/config.json` → benchmark plan remains valid.
