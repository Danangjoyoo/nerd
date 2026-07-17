---
name: nerd-fast
description: Use when explicitly invoked or when a concrete latency constraint requires minimizing wall-clock agent time without reducing accuracy, including reusing current context, batching independent operations, shortening sequential tool paths, and selecting proportionate verification.
---

# Nerd Fast

## Composition

Apply this as a global modifier to the active workflow. It is never a primary specialty and never replaces or restarts the active workflow. When invoked alone, use `nerd-smart` only if endpoint, scope, or authorization remains materially ambiguous.

Compose with `nerd-silent` only when the user explicitly invokes both modifiers. Never activate, infer, or auto-compose Silent from latency, presentation cost, brevity, token cost, or output preferences. When both are invoked, Fast controls operation selection, scheduling, and whether routine work needs a pre-tool model round; Silent controls overall narration and final presentation. Preserve the active workflow's correctness, authorization, safety, user interaction, and proof requirements.

## Core Rule

Minimize sequential critical-path rounds. Keep an operation only when it resolves a material unknown, advances the requested deliverable, or produces required proof.

Prefer: **reuse -> batch -> parallelize -> target narrowly -> escalate on evidence -> stop when proven**.

Use no hard total tool limit. Fixed limits can trade accuracy for speed when valid evidence or proof needs more operations.

## Gates

Apply these gates in order. Keep them internal unless a conflict, blocker, or user decision must be reported.

| Gate | Decision | Default action |
| --- | --- | --- |
| **Inheritance** | Are endpoint, scope, authorization, and active specialty resolved? | Inherit them. Resolve only a material missing field. |
| **Reuse** | Is sufficient current evidence already available? | Reuse it without another tool call. |
| **Freshness** | Could the evidence have changed or become invalid? | Refresh time-sensitive state, changed files, failed commands, and ambiguous or truncated output. |
| **Need** | Which decision, change, or proof will the operation affect? | Skip operations without a material consumer. |
| **Batch** | Can known operations be dispatched together? | Batch independent operations; combine predetermined read-only commands in one invocation. |
| **Dependency** | Can an intermediate result change the next operation? | Keep adaptive dependencies sequential; never parallelize dependent mutations. |
| **Escalation** | What is the cheapest operation that distinguishes the possibilities? | Start narrowly and broaden only on an explicit trigger. |
| **Recovery** | Did the failed attempt produce new evidence? | Make at most two evidence-driven corrections by default, then report the blocker. |
| **Verification cost** | What is the lowest-cost fresh proof supporting the completion claim? | Select the lowest sufficient tier and escalate only on a verification trigger. |
| **Stop** | Are the requested outcome and required proof satisfied? | Stop without optional exploration or review. |

Use one discovery batch before narrowing when the target is unknown. Read exact named targets before repository-wide discovery. Batch known independent reads, searches, lookups, and safe checks. Use one final proof wave unless it exposes a material unresolved failure. User instructions, repository authority, and the active specialty override these soft limits.

## Concrete Command Batching

Batch operations when the commands and their reactions are known before execution. Prefer one command that spans known targets; otherwise group read-only commands in one tool invocation. Parallelize independent operations when the platform supports it, and keep adaptive operations in separate rounds when an output can change the next command.

Examples:

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

Treat these commands as illustrations, not requirements. Use equivalent tools when `sed`, `rg`, shell operators, or the shown runtimes are unavailable. Only chain commands when the execution tool invokes a shell interpreter; otherwise use separate structured invocations or the tool's native batching interface. Use `;` only when later operations remain useful after an earlier failure. Use `&&` when success is a prerequisite. Use `||` only for intentional recovery or fallback.

## Verification-Cost Gate

Select the cheapest fresh check that observes the behavior or property being claimed.

### Proof Ladder

| Tier | Proof | Typical use |
| --- | --- | --- |
| **V0** | Existing current evidence or no verification claim | Read-only answers, unchanged facts, or work without a proportionate executable check. Report `Not verified` when completion would otherwise imply proof. |
| **V1** | Static, parse, content, or syntax check | Documentation, metadata, formatting, configuration, or static artifacts. |
| **V2** | Focused behavioral check | The unit, contract, repository, component, regression, or browser test closest to the change. |
| **V3** | Boundary or package validation | A relevant package suite, type check, build, integration test, migration check, or multi-component validation. |
| **V4** | Full-system or live validation | A full repository suite, end-to-end run, deployment smoke test, or authorized live integration. |

Choose the lowest tier that directly supports the exact claim. V0 may reuse evidence only when no mutation invalidated it. Any file mutation, structural refactor, or code addition requires at least V1 proof before completion. Any behavioral completion claim after mutation requires fresh proof.

### Incremental and Runtime-Aware Verification

| Situation | Default |
| --- | --- |
| **Reusable state** | Reuse fresh, trustworthy dependency, compiler, transpiler, test, runtime, and build caches. Preserve active daemons and watch processes when available. |
| **Static claim** | Use the narrowest syntax, type, lint, compile, or AST check that directly observes the claim. |
| **Behavioral claim** | Run one test method, case, file, package, or affected component before broader suites. |
| **Cold work** | Avoid clearing caches, reinstalling dependencies, rebuilding unaffected targets, recreating environments, or restarting healthy services without evidence that it is necessary. |
| **Escalation** | Run clean builds, broad suites, or environment resets only when repository authority, stale state, contradictory evidence, release parity, or another verification trigger requires them. |

Illustrative narrow checks:

| Ecosystem | Example |
| --- | --- |
| **Python** | `pytest tests/test_api.py::test_login` |
| **JavaScript / TypeScript** | `vitest run path/to/api.test.ts` |
| **Ruby** | `bundle exec rspec spec/api_spec.rb:42` |
| **Java / Kotlin** | `./gradlew test --tests 'pkg.ApiTest.login'` |
| **Go** | `go test ./pkg/api -run '^TestLogin$'` |

Treat commands, languages, and build systems as illustrations. Use the narrowest equivalent check supported by the active project.

### Verification Escalation Triggers

- The user or repository instructions explicitly require broader proof.
- The change crosses packages, services, persistence boundaries, or public contracts that narrower proof cannot cover.
- Security, authorization, migration, data-loss, concurrency, release, or production risk makes broader proof proportionate.
- The targeted check fails ambiguously or reveals a wider affected surface.
- The lower tier cannot observe a material part of the completion claim.

Do not run a full suite merely because one exists. Do not rerun an unchanged passing check. Classify a failure as related, unrelated, or unknown; correct only a related failure within scope. After two evidence-driven correction attempts, stop with the failing command, observed evidence, and smallest decision needed.

When proof remains narrower than the claim, narrow the claim. Use `Not verified` or state the exact verified boundary rather than implying broader confidence.

## Generic Operational Mappings

Classify operational shape only after intent, endpoint, scope, and authorization are resolved. Select the single closest row. A mapping never grants permission and never overrides user instructions, repository authority, the active specialty, or observed evidence.

| # | Signal | Default recipe |
| --- | --- | --- |
| **1** | Current context is sufficient | Reuse evidence -> perform the active endpoint -> apply the verification-cost gate -> stop. |
| **2** | Exact file, symbol, command, or target is named | Read the target and nearest authority or test together -> work -> run targeted proof. |
| **3** | Local target is unknown | Read mandatory instructions -> run one batched search -> inspect the best hits -> narrow scope. |
| **4** | Multiple targets are independent | Batch or parallelize reads and safe checks -> synthesize once -> continue. |
| **5** | Work has genuine dependencies | Create two to five critical-path TODOs -> execute in dependency order -> prove the result. |
| **6** | The user supplied an approved plan | Read it once -> execute remaining steps -> do not rediscover or re-plan. |
| **7** | Current or external information is required | Query authoritative sources together -> confirm freshness -> use only supported facts. |
| **8** | A failure or contradiction is present | Reuse failure output -> reproduce once -> run one hypothesis and experiment -> make a bounded correction. |
| **9** | Verification is expensive | Choose the lowest sufficient proof tier -> escalate only on a verification trigger. |
| **10** | Work continues after an earlier turn or retry | Reuse the Focus Record, plan, outputs, and diff -> refresh only changed or stale evidence. |

If two rows conflict materially, use one cheap discriminator or ask one material question.

## Execution Discipline

For non-atomic work, maintain this internal Fast Path:

| Field | Value |
| --- | --- |
| **Recipe** | Selected mapping. |
| **Known** | Reusable current evidence. |
| **Unknown** | One critical missing fact. |
| **Next batch** | Independent operations to execute together. |
| **Proof** | Lowest sufficient fresh verification tier. |
| **Stop** | Exact completion condition. |

Execute in four waves:

| Wave | Discipline |
| --- | --- |
| **Reuse** | Consume current records, plans, outputs, and unchanged evidence. |
| **Discover** | Run one narrow batch that resolves the critical unknown. |
| **Execute** | Perform the smallest authorized work and parallelize only independent operations. |
| **Prove** | Apply the verification-cost gate, state only supported claims, and stop. |

### Keep TODOs Outcome-Bound

Each TODO must deliver an outcome, remove a blocker, or provide proof.

### Reuse Evidence Until Invalidated

Do not reread unchanged files, repeat successful commands, or restart planning after each result. Reuse evidence until mutation, contradiction, staleness, or dependency failure invalidates it.

### Index Only When It Pays

Prefer an existing fresh file or symbol index when cheaper than direct search. For complex repository analysis, architecture summaries, or cross-file work likely to need three or more exact-symbol lookups, resolve `scripts/symbol_index.py` relative to this `SKILL.md` and run `ensure` once at the start of discovery. Use `find` without implicit refresh. Do not rebuild or refresh an index for a single known target. Universal Ctags is optional: try once, then fall back to an exact-file read or narrow text search when unavailable, stale, or incomplete. Treat matches as navigation candidates and confirm source before mutation.

### Patch Narrowly and Safely

Prefer a structured patch or targeted-edit primitive. Do not reproduce unchanged file content in output or edit payloads. Rewrite a whole file only when generated, mostly changed, or handled by a trusted formatter or codemod. Before dispatching a mutation batch, require each step to be idempotent, transactional, or safely recoverable; otherwise keep mutations sequential and inspect state between them. Concrete tools are examples, not dependencies.

### Dispatch Routine Tools Immediately

For routine authorized operations, invoke the tool immediately. Explain first only for approval, safety, a material decision, or a required progress update. Fast removes optional pre-tool latency; Silent controls overall narration and final presentation.

### Delegate Only for Net Speed

Dispatch reviewers or subagents only when the active workflow allows it and expected wall-clock savings exceed setup and handoff cost.

## Conflict Discipline

Yield to correctness and authority. When Fast conflicts with repository instructions, safety, the active workflow, or a supported completion claim, preserve the higher-authority requirement and take the lowest-cost valid path.

Treat tool errors as evidence, not automatic permission for broader exploration. Correct the invocation or assumption once, then broaden only when the error shows the current scope or source is insufficient.

After changing this skill family, run `python3 scripts/validate_skills.py`.
