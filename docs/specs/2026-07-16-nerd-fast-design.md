# Nerd Fast Design

## Goal

Publish `nerd-fast` as a global modifier that reduces end-to-end agent latency without lowering correctness, authorization, safety, or proof quality.

Optimize sequential operations on the critical path. Do not optimize merely for fewer tokens, fewer total tools, or less reasoning when those reductions weaken the result.

## Position in the Skill Family

`nerd-fast` changes operation selection, ordering, batching, reuse, escalation, and stopping behavior. It does not own the endpoint or domain workflow.

- `nerd-smart` owns intention, endpoint, scope, and role.
- `nerd-execute`, `nerd-surgery`, and `nerd-patrol` own their specialty workflows.
- `nerd-silent` owns narration and final-presentation cost.

Fast is never a primary specialty and never replaces or restarts an active workflow. It composes with Silent only when both modifiers are explicitly invoked. It preserves all required user interaction, safety, authorization, and proof.

Activate Fast on explicit invocation or a concrete request to minimize wall-clock latency without reducing accuracy. Do not infer it from vague words such as `simple` or `quick`.

## Core Rule

Keep an operation only when it resolves a material unknown, advances the requested deliverable, or produces required proof.

> Reuse -> batch -> parallelize -> target narrowly -> escalate on evidence -> stop when proven.

Fast has no hard total tool limit. A fixed cap can trade correctness for speed when valid evidence or proof requires more operations.

## Read-Volume Gate

Before the first source read, estimate `x`, the total lines direct navigation is likely to require. Estimate from the named scope, known sizes or ranges, and likely supporting files without reading targets merely to calculate an exact count.

- `x <= 200`: skip the symbol index and navigate directly.
- `x > 200`: resolve `scripts/symbol_index.py` relative to `SKILL.md`, run `ensure` once, then use `find` without implicit refresh.

Apply this decision before discovery. Universal Ctags remains optional. If `ensure` reports it unavailable, ask once whether to install it, explaining that measured large-repository workloads showed up to 70% faster indexed navigation. Installation requires explicit approval. On decline, unsupported installation, or failure, fall back immediately without asking again during the task. For any other unusable, stale, or incomplete index, use an exact-file read or narrow text search. Index matches remain navigation candidates and must be confirmed in source before mutation.

## Ordered Decisions

Apply these decisions once in order and keep them internal unless a user decision, conflict, or blocker must be reported.

| Gate | Question | Default |
| --- | --- | --- |
| Inheritance | Are endpoint, scope, authorization, and specialty resolved? | Inherit them; resolve only a material omission. |
| Reuse | Is sufficient current evidence available? | Reuse it. |
| Freshness | Could evidence be stale or invalid? | Refresh only time-sensitive, changed, failed, ambiguous, or truncated evidence. |
| Need | What material consumer does the operation have? | Skip operations without one. |
| Batch | Are known operations independent? | Batch them with the platform's native interface. |
| Dependency | Can one result change the next operation? | Keep the dependency sequential. |
| Escalation | What is the cheapest discriminator? | Start narrowly and broaden on evidence. |
| Recovery | Did failure produce new evidence? | Make at most two evidence-driven corrections by default. |
| Verification cost | What is the lowest-cost sufficient proof? | Choose the lowest sufficient tier. |
| Stop | Are outcome and proof satisfied? | Stop. |

User instructions, repository authority, safety, and the active workflow override these defaults.

## Adaptive Execution

Use only the conditions that apply:

- Sufficient context: perform the active endpoint, apply proportionate proof, and stop.
- Exact target: apply the Read-Volume Gate and navigate the target plus its nearest authority or test.
- Unknown target: run one narrow discovery batch, inspect the best evidence, and narrow scope.
- Independent work: batch or parallelize it and synthesize once.
- Adaptive dependency: sequence it because the result can change the next operation.
- Existing plan: execute remaining work without rediscovery.
- Current or external information: query authoritative sources together and confirm freshness.
- Failure or contradiction: reuse it as evidence and test one bounded hypothesis.
- Continuation: reuse the current record, plan, outputs, and diff; refresh only changed or stale evidence.

This replaces the former ten-recipe mapping and mandatory-looking four-wave presentation. Reuse, discovery, endpoint work, and proof remain available but are not forced to be non-empty phases.

## Batching and Mutation Safety

Batch operations only when their commands and reactions are known. Prefer a single operation spanning known targets or a native batching or parallel interface. Keep adaptive work sequential.

Batch mutations only when every step is idempotent, transactional, or safely recoverable. Otherwise mutate sequentially and inspect state between steps. Prefer targeted edits and avoid reproducing unchanged content.

Invoke routine authorized tools immediately. Add narration first only for approval, safety, a material decision, or a required progress update. Delegate only when the active workflow permits it and expected wall-clock savings exceed startup and handoff cost.

## Verification-Cost Gate

Select the cheapest fresh check that directly observes the completion claim.

| Tier | Proof | Typical use |
| --- | --- | --- |
| V0 | Current evidence or no verification claim | Read-only answers, unchanged facts, or no proportionate executable check. |
| V1 | Static, parse, content, or syntax check | Documentation, metadata, formatting, configuration, or static artifacts. |
| V2 | Focused behavioral check | The closest unit, contract, component, regression, repository, or browser test. |
| V3 | Boundary or package validation | A relevant package suite, type check, build, integration test, migration check, or multi-component validation. |
| V4 | Full-system or live validation | A full suite, end-to-end run, deployment smoke test, or authorized live integration. |

Any mutation requires at least V1 before completion. Any behavioral completion claim after mutation requires fresh proof. Reuse trustworthy dependency, compiler, transpiler, test, runtime, and build caches; preserve healthy daemons and watch processes. Start with the narrowest static or behavioral check and avoid cache clearing, dependency reinstall, clean builds, broad suites, environment recreation, or service restarts without evidence.

Escalate only when:

- User or repository instructions require broader proof.
- A change crosses boundaries that narrower proof cannot cover.
- Security, authorization, migration, data-loss, concurrency, release, or production risk makes broader proof proportionate.
- A targeted check fails ambiguously or exposes a wider affected surface.
- The lower tier cannot observe a material part of the claim.

Do not run a full suite merely because one exists or rerun an unchanged passing check. Classify failures as related, unrelated, or unknown. After two evidence-driven corrections, report the blocker and smallest required decision. When proof is narrower than the claim, narrow the claim and state the verified boundary or `Not verified`.

## Package and Indexer Boundary

The publication package remains:

```text
skills/nerd-fast/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── symbol_index.py
```

The indexer remains a standard-library, workspace-keyed, incremental SQLite exact-symbol index with optional Universal Ctags refresh. This consolidation does not change its schema, fingerprinting, exact lookup, result ordering, CLI, or fallback behavior. Fuzzy lookup, language filters, ranking, reference graphs, and content hashes remain out of scope.

Universal Ctags capability detection must accept both single-column `--list-features` output and the tabular `#NAME DESCRIPTION` format emitted by Homebrew Universal Ctags 6.2.x. For every nonempty row, the first whitespace-delimited field is the feature name; `json` remains mandatory. The installed Ctags binary must work directly through `--ctags` without a user-created wrapper.

The metadata description must identify the concrete latency trigger, and the default prompt must name `$nerd-fast`. Fast remains original Nerd guidance and does not receive `LICENSE.superpowers`.

## Contract and Benchmark Proof

Deterministic contracts must establish that Fast:

- Is a public modifier with valid frontmatter and metadata.
- Preserves active-workflow correctness, authorization, safety, and proof.
- Has no hard total tool cap.
- Contains the ordered gates, early Read-Volume Gate, V0-V4 proof ladder, five verification triggers, bounded recovery, and one conditional adaptive path.
- Keeps batching platform-neutral and mutations recoverable.
- Reuses incremental runtime state without ecosystem-specific command tables.
- Preserves targeted editing, immediate routine tool dispatch, direct-search fallback, and source confirmation before mutation.
- Offers a missing Universal Ctags install once, states the scoped benchmark, requires explicit approval, and preserves immediate fallback.
- Accepts single-column and tabular Universal Ctags feature output without a wrapper while retaining the JSON requirement.
- Composes with Silent only when both are explicitly invoked.
- Does not contain a runtime `superpowers:` dependency.
- Remains at or below 1,400 words.

Benchmark Fast against the same active workflow without Fast on paired tasks covering known targets, unknown discovery, independent operations, continuation, failure recovery, and expensive verification. Use the same agent, model, effort, fixture, task, and repetition for each pair, with at least three paired repetitions per case.

Success requires no new hard-gate failure, no lower paired accuracy, lower median elapsed time, and no broader verification tier without a trigger. Record elapsed time and, where available, sequential model/tool rounds, tool calls, verification commands, and verification time.

## Out of Scope

- Selecting a faster or less accurate model.
- Reducing reasoning effort globally.
- Skipping required evidence, authorization, safety, or verification.
- Replacing Nerd Smart or a primary specialty.
- Changing final response verbosity; Nerd Silent owns presentation.
- Adding a hard time, token, or tool-call budget without an explicit user constraint.
- Adding numeric confidence thresholds or a fixed global operation-cost ranking.
- Changing index schema, CLI, lookup semantics, or adding index features beyond Universal Ctags capability-output compatibility.
