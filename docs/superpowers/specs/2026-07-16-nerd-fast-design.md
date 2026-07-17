# Nerd Fast Design

## Goal

Publish `nerd-fast` as a global Nerd modifier that reduces end-to-end agent latency without lowering correctness, authorization, safety, or verification quality.

Optimize the number of sequential operations on the critical path. Do not optimize merely for fewer tokens, fewer total tools, or less reasoning when those reductions weaken the result.

## Position in the Skill Family

`nerd-fast` is a modifier, not a primary specialty.

- `nerd-smart` owns intention, endpoint, scope, and role.
- `nerd-execute`, `nerd-surgery`, and `nerd-patrol` own their domain workflows.
- `nerd-fast` changes operation selection, ordering, batching, reuse, escalation, stopping behavior, and whether routine work needs a pre-tool model round.
- `nerd-silent` changes overall narration and final presentation cost.

Fast and Silent may compose. Fast never replaces or restarts the active workflow. When invoked without a resolved workflow, it uses Nerd Smart only when a material endpoint, scope, or authorization ambiguity remains.

Activate Fast on explicit invocation or a concrete request to minimize wall-clock latency without reducing accuracy. Do not infer activation from vague terms such as `simple` or `quick` when speed is not an actual outcome constraint.

## Core Rule

Minimize sequential critical-path rounds while preserving the active workflow's accuracy, authorization, safety, and proof requirements.

Keep an operation only when it does at least one of the following:

1. Resolves a material unknown.
2. Advances the requested deliverable.
3. Produces required proof.

Prefer this order:

> Reuse -> batch -> parallelize -> target narrowly -> escalate on evidence -> stop when proven.

Fast has no hard total tool limit. A fixed cap would trade accuracy for speed on tasks whose evidence or proof genuinely requires more operations.

## Gates

Apply the gates in order. Do not narrate them unless a user decision, conflict, or blocker is required.

| Gate | Decision | Default action |
| --- | --- | --- |
| Inheritance | Are endpoint, scope, authorization, and active specialty resolved? | Inherit them without reopening work. Resolve only a material missing field. |
| Reuse | Is sufficient current evidence already present? | Reuse it without another tool call. |
| Freshness | Could the evidence have changed or become invalid? | Refresh time-sensitive external state, changed files, failed commands, and ambiguous or truncated output. |
| Need | Which decision, change, or proof will the operation affect? | Skip operations without a material consumer. |
| Batch | Can known operations be dispatched together? | Batch independent operations; combine predetermined read-only commands in one invocation. |
| Dependency | Can an intermediate result change the next operation? | Keep adaptive dependencies sequential. Do not parallelize dependent mutations. |
| Escalation | What is the cheapest operation that can distinguish the possibilities? | Start narrowly and broaden only after an escalation trigger. |
| Recovery | Did the failed attempt produce new evidence? | Make at most two evidence-driven corrections by default, then report the blocker. |
| Verification cost | What is the lowest-cost fresh proof that directly supports the completion claim? | Select the lowest sufficient proof tier and escalate only on a verification trigger. |
| Stop | Are the requested outcome and required proof satisfied? | Stop immediately without optional exploration or review. |

### Soft Operating Limits

- Use one discovery batch before narrowing when the target is unknown.
- Read exact named targets before repository-wide discovery.
- Batch all known independent reads, searches, lookups, and safe checks.
- Use at most two evidence-driven recovery attempts unless the active workflow requires otherwise.
- Use one fresh final proof wave unless its result exposes a material unresolved failure.
- Broaden exploration only for a contradiction, missing authority, incomplete proof, or relevant high-risk evidence.

User instructions, repository authority, and the active specialty override these defaults.

### Concrete Command Batching

Batch operations when the commands and their reactions are known before execution. Prefer one command that spans known targets; otherwise group read-only commands in one tool invocation. Parallelize independent operations when the platform supports it, and keep adaptive operations in separate rounds when an output can change the next command.

Use concrete examples without making their tools part of the contract:

```sh
# Read several known regions in one round.
sed -n '1,160p' src/a.py; sed -n '40,120p' tests/test_a.py

# Search several known targets with one command.
rg -n 'timeout|retry' src tests docs

# Collect independent, read-only repository evidence.
git status --short; git diff --stat; git diff --check

# Run dependent checks as a fail-fast sequence.
python3 -m compileall src && pytest tests/unit -q && python3 scripts/validate.py

# Select an intentional fallback after failure.
primary-command || compatible-fallback-command
```

Require equivalent tools when these examples are unavailable. Only chain commands when the execution tool invokes a shell interpreter; otherwise use separate structured invocations or the tool's native batching interface. Use `;` only when later operations remain useful after an earlier failure, `&&` when success is a prerequisite, and `||` only for intentional recovery or fallback.

## Verification-Cost Gate

Verification is required to support claims, not to perform ceremony. Select the cheapest fresh check that observes the behavior or property being claimed.

### Proof Ladder

| Tier | Proof | Typical use |
| --- | --- | --- |
| V0 | Existing current evidence or no verification claim | Read-only answers, unchanged facts, or outcomes for which no proportionate executable check exists. Report `Not verified` when completion would otherwise imply proof. |
| V1 | Static, parse, content, or syntax check | Documentation, metadata, formatting, configuration, or static artifacts. |
| V2 | Focused behavioral check | One unit, contract, repository, component, regression, or targeted browser test closest to the change. |
| V3 | Boundary or package validation | Relevant package suite, type check, build, integration test, migration check, or multi-component validation. |
| V4 | Full-system or live validation | Full repository suite, end-to-end run, deployment smoke test, or authorized live integration. |

Choose the lowest tier that directly supports the exact claim. V0 may reuse evidence only when no mutation has invalidated it. Any file mutation, structural refactor, or code addition requires at least V1 proof before completion. Any behavioral completion claim after mutation requires fresh proof.

### Incremental and Runtime-Aware Verification

| Situation | Default |
| --- | --- |
| **Reusable state** | Reuse fresh, trustworthy dependency, compiler, transpiler, test, runtime, and build caches. Preserve active daemons and watch processes when available. |
| **Static claim** | Use the narrowest syntax, type, lint, compile, or AST check that directly observes the claim. |
| **Behavioral claim** | Run one test method, case, file, package, or affected component before broader suites. |
| **Cold work** | Avoid clearing caches, reinstalling dependencies, rebuilding unaffected targets, recreating environments, or restarting healthy services without evidence that it is necessary. |
| **Escalation** | Run clean builds, broad suites, or environment resets only when repository authority, stale state, contradictory evidence, release parity, or another verification trigger requires them. |

Use concrete narrow-check examples without making their ecosystems part of the contract:

| Ecosystem | Example |
| --- | --- |
| **Python** | `pytest tests/test_api.py::test_login` |
| **JavaScript / TypeScript** | `vitest run path/to/api.test.ts` |
| **Ruby** | `bundle exec rspec spec/api_spec.rb:42` |
| **Java / Kotlin** | `./gradlew test --tests 'pkg.ApiTest.login'` |
| **Go** | `go test ./pkg/api -run '^TestLogin$'` |

Treat commands, languages, and build systems as illustrations. Require the narrowest equivalent check supported by the active project.

### Verification Escalation Triggers

Escalate to a broader or more expensive tier only when at least one trigger applies:

- The user or repository instructions explicitly require it.
- The change crosses packages, services, persistence boundaries, or public contracts that a narrower check cannot cover.
- Security, authorization, migration, data-loss, concurrency, release, or production risk makes broader proof proportionate.
- The targeted check fails ambiguously or reveals a wider affected surface.
- The lower tier cannot observe a material part of the completion claim.

Do not run a full suite merely because one exists. Do not rerun an unchanged passing check. After a failure, classify it as related, unrelated, or unknown; correct only a related failure within scope. After two evidence-driven correction attempts, stop with the failing command, observed evidence, and smallest decision needed.

When proof remains narrower than the claim, narrow the claim. Use `Not verified` or state the exact verified boundary rather than implying broader confidence.

## Generic Operational Mappings

Mappings classify operational shape only after intent, endpoint, scope, and authorization are resolved. They never guess permission or replace repository evidence.

| # | Signal | Default recipe |
| --- | --- | --- |
| 1 | Current context is sufficient | Reuse evidence -> perform the active endpoint -> apply the verification-cost gate -> stop. |
| 2 | Exact file, symbol, command, or target is named | Read the target and nearest authority or test together -> work -> run targeted proof. |
| 3 | Local target is unknown | Read mandatory instructions -> run one batched search -> inspect the best hits -> narrow scope. |
| 4 | Multiple targets are independent | Batch or parallelize reads and safe checks -> synthesize once -> continue. |
| 5 | Work has genuine dependencies | Create two to five critical-path TODOs -> execute in dependency order -> prove the result. |
| 6 | The user supplied an approved plan | Read it once -> execute remaining steps -> do not rediscover or re-plan. |
| 7 | Current or external information is required | Query authoritative sources together -> confirm freshness -> use only supported facts. |
| 8 | A failure or contradiction is present | Reuse the failure output -> reproduce once -> run one hypothesis and experiment -> make a bounded correction. |
| 9 | Verification is expensive | Choose the lowest sufficient proof tier -> escalate only on a verification trigger. |
| 10 | Work continues after an earlier turn or retry | Reuse the Focus Record, plan, outputs, and diff -> refresh only changed or stale evidence. |

Select the single closest mapping. If two mappings conflict materially, use one cheap discriminator or ask one material question. The active specialty, user instructions, repository authority, and observed evidence always override a mapping.

## Execution Discipline

For non-atomic work, maintain this internal Fast Path record:

| Field | Value |
| --- | --- |
| **Recipe** | Selected mapping. |
| **Known** | Reusable current evidence. |
| **Unknown** | One critical missing fact. |
| **Next batch** | Independent operations to execute together. |
| **Proof** | Lowest sufficient fresh verification tier. |
| **Stop** | Exact completion condition. |

Do not display the record unless it exposes a conflict that requires user input.

Execute in four waves:

| Wave | Discipline |
| --- | --- |
| **Reuse** | Consume current records, plans, outputs, and unchanged evidence. |
| **Discover** | Run one narrow batch that resolves the critical unknown. |
| **Execute** | Perform the smallest authorized work and parallelize only independent operations. |
| **Prove** | Apply the verification-cost gate, state only supported claims, and stop. |

Additional discipline:

| Rule | Discipline |
| --- | --- |
| **TODOs** | Make every TODO produce an outcome, remove a blocker, or provide proof. Do not create TODOs named only `analyze`, `think`, or `inspect more`. |
| **Evidence reuse** | Do not reread unchanged files, repeat successful commands, or restart planning after every tool result. Reuse a successful result until a mutation, contradiction, freshness requirement, or failed dependent operation invalidates it. |
| **Indexed navigation** | Prefer an existing fresh file or symbol index when its query cost is lower than direct search and expected reuse amortizes refresh cost. Do not rebuild or refresh an index for a single lookup. Resolve the bundled `scripts/symbol_index.py` relative to `SKILL.md`, run `ensure` once before repeated exact-symbol lookups, and use `find` without implicit refresh. Universal Ctags is optional; fall back to an exact-file read or narrow text search when the index is unavailable, stale, or incomplete. Treat matches as navigation candidates and confirm source before mutation. |
| **Delegation** | Do not dispatch reviewers or subagents unless the active workflow permits them and their expected wall-clock savings exceed startup and handoff cost. |
| **Authority** | Preserve required user interaction, safety checks, authorization, and proof. |
| **Mutation** | Prefer a structured patch or targeted-edit primitive for localized mutations. Do not reproduce unchanged file content in the model output or edit payload. Rewrite whole files only when they are generated, mostly replaced, or transformed by an appropriate trusted tool. Before dispatching a mutation batch, confirm that each intermediate step is idempotent, transactional, or safely recoverable if a later command fails; otherwise keep mutations sequential and inspect state between them. |
| **Tool dispatch** | Invoke tools immediately for routine authorized operations. Add a pre-tool model round only for approval, safety, a material decision, or a required progress update. |
| **Presentation** | Leave overall narration and final-output reduction to Nerd Silent. |

## Conflicts and Failure Handling

Fast yields to correctness and authority. When a speed rule conflicts with the active workflow, repository instructions, safety, or a supported completion claim, preserve the higher-authority requirement and take the lowest-cost valid path.

Ask the user only when the conflict changes scope, authorization, output, safety, meaningful cost, or risk of rework. Otherwise select the safe default and continue.

Tool errors do not automatically authorize broader exploration. Reuse the error as evidence, correct the invocation or assumption once, and broaden only when the error shows that the current scope or source is insufficient.

## Package Shape

Create only the files needed for publication and validation:

```text
skills/nerd-fast/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── symbol_index.py
```

The optional indexer script uses only Python standard-library modules and keeps its workspace-keyed SQLite cache outside the workspace. Universal Ctags with JSON support is optional and is used only during explicit incremental refreshes. When the dependency or a usable index is unavailable, an exact-file read or narrow text search remains the required fallback. The implementation and measurement boundary is specified in [the symbol indexer implementation plan](../plans/2026-07-17-nerd-fast-symbol-indexer.md).

No assets or reference files are justified. Keep `nerd-fast` in the public skill contract, README skill table, modifier composition language, installation validation, and contract tests.

The metadata description must identify Fast as a latency modifier and include its explicit and concrete latency triggers. The default prompt must name `$nerd-fast`.

Fast is original Nerd guidance, not shortened Superpowers material, so it does not receive `LICENSE.superpowers`. Replace the validator's positional `PUBLIC_SKILLS[:-1]` attribution rule with an explicit derived-skill tuple so adding or reordering modifiers cannot silently assign the wrong license requirement.

## Contract and Benchmark Proof

Structural and contract tests must establish that Fast:

- Is a public skill with only `name` and `description` frontmatter.
- Is a modifier, never a primary specialty.
- Preserves active workflow correctness, authorization, safety, and proof.
- Has no hard total tool cap.
- Contains the ten ordered gates, proof ladder, five verification escalation triggers, ten generic mappings, four execution waves, and bounded recovery rule.
- Includes concrete, non-binding command-batching examples and equivalent-tool guidance.
- Prefers targeted edits and immediate tool dispatch for routine authorized operations.
- Reuses trustworthy incremental runtime state and gives non-binding narrow-check examples across language ecosystems.
- Selects an existing fresh index only when reuse amortizes its cost, invokes the bundled script relative to `SKILL.md`, confirms source before mutation, and preserves direct-search fallback.
- Composes with Nerd Silent without duplicating narration rules.
- Does not contain a runtime `superpowers:` dependency.

Benchmark Fast against the same active workflow without Fast on paired tasks that exercise known-target work, unknown-target discovery, independent operations, continuation, failure recovery, and expensive verification. Extend benchmark condition prompts to compose Fast with the selected active workflow instead of replacing that workflow.

Use identical agent, model, reasoning effort, fixture, task, and repetition for each pair, with at least three paired repetitions per case. Success requires:

1. No new hard-gate correctness failure under Fast.
2. Accuracy score no lower than the paired baseline within the benchmark rubric.
3. Lower median end-to-end elapsed time across the Fast cases.
4. No broader verification tier than the case requires unless an escalation trigger is present.

Record total elapsed time for compatibility with the existing benchmark. Where agent events permit it, also record sequential tool/model rounds, tool-call count, verification commands, and verification elapsed time so latency changes can be attributed rather than inferred from totals alone.

## Out of Scope

- Selecting a faster or less accurate model.
- Reducing reasoning effort globally.
- Skipping required evidence, authorization, safety, or verification.
- Replacing Nerd Smart or any primary specialty.
- Changing final response verbosity; Nerd Silent owns presentation cost.
- Adding a hard time, token, or tool-call budget without an explicit user constraint.
