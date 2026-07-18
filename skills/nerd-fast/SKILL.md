---
name: nerd-fast
description: Use when explicitly invoked or when a concrete latency constraint requires minimizing wall-clock agent time without reducing accuracy.
---

# Nerd Fast

## Composition

Apply this as a global modifier. It is never a primary specialty and never replaces or restarts the active workflow. Use `nerd-smart` only for material endpoint, scope, or authorization ambiguity.

Compose with `nerd-silent` only when the user explicitly invokes both modifiers. Never activate, infer, or auto-compose Silent from latency or presentation preferences. Fast controls operation selection and scheduling; Silent owns presentation. Preserve correctness, authorization, safety, user interaction, and proof requirements.

## Core Rule

Minimize sequential critical-path rounds. Keep an operation only when it resolves a material unknown, advances the requested deliverable, or produces required proof.

Prefer: **reuse -> batch -> parallelize -> target narrowly -> escalate on evidence -> stop when proven**.

Use no hard total tool limit. A fixed limit can trade accuracy for speed when valid evidence or proof requires more operations.

## Read-Volume Gate

At task start, before the first source read, estimate `x`: the total estimated lines direct navigation would require. Estimate from the named scope, known ranges or sizes, and likely supporting files; do not read targets merely to calculate an exact count.

- `x <= 200`: skip `symbol_index.py`; read or search the targets directly.
- `x > 200`: resolve `scripts/symbol_index.py` relative to this `SKILL.md`, run `ensure` once before source reads, then navigate with `find` without implicit refresh.

Do not wait until 200 lines have already been read. Universal Ctags is optional: if it or a usable index is unavailable, stale, or incomplete, fall back to an exact-file read or narrow text search. Treat index matches as navigation candidates and confirm source before mutation.

## Gates

Apply these gates in order. Keep them internal unless a conflict, blocker, or user decision must be reported.

| Gate | Decision | Default action |
| --- | --- | --- |
| **Inheritance** | Are endpoint, scope, authorization, and active specialty resolved? | Inherit them. Resolve only a material missing field. |
| **Reuse** | Is sufficient current evidence available? | Reuse it without another operation. |
| **Freshness** | Could evidence have changed or become invalid? | Refresh time-sensitive state, changed files, failures, and ambiguous or truncated output. |
| **Need** | Which decision, change, or proof will this affect? | Skip operations without a material consumer. |
| **Batch** | Are the operations known and independent? | Batch them with the platform's native interface. |
| **Dependency** | Can one result change the next operation? | Keep adaptive dependencies sequential. |
| **Escalation** | What is the cheapest operation that distinguishes the possibilities? | Start narrowly and broaden only on evidence. |
| **Recovery** | Did the failed attempt produce new evidence? | Make at most two evidence-driven corrections by default, then report the blocker. |
| **Verification cost** | What is the lowest-cost fresh proof supporting the claim? | Select the lowest sufficient tier and escalate only on a verification trigger. |
| **Stop** | Are the outcome and required proof satisfied? | Stop without optional exploration or review. |

User instructions, repository authority, safety, and the active workflow override these defaults.

## Batching and Dependencies

Batch independent operations when their commands and reactions are known. Prefer one operation spanning known targets or the tool's native batching or parallel interface. Keep adaptive work sequential when an output can change the next operation.

Before dispatching a mutation batch, require every step to be idempotent, transactional, or safely recoverable; otherwise keep mutations sequential and inspect state between them.

## Verification-Cost Gate

Select the cheapest fresh check that observes the property being claimed.

### Proof Ladder

| Tier | Proof | Typical use |
| --- | --- | --- |
| **V0** | Existing current evidence or no verification claim | Read-only answers, unchanged facts, or work without a proportionate executable check. Report `Not verified` when completion would otherwise imply proof. |
| **V1** | Static, parse, content, or syntax check | Documentation, metadata, formatting, configuration, or static artifacts. |
| **V2** | Focused behavioral check | The unit, contract, repository, component, regression, or browser test closest to the change. |
| **V3** | Boundary or package validation | A relevant package suite, type check, build, integration test, migration check, or multi-component validation. |
| **V4** | Full-system or live validation | A full repository suite, end-to-end run, deployment smoke test, or authorized live integration. |

Choose the lowest tier that directly supports the exact claim. V0 may reuse evidence only when no mutation invalidated it. Any file mutation, structural refactor, or code addition requires at least V1 proof before completion. Any behavioral completion claim after mutation requires fresh proof.

Reuse fresh, trustworthy dependency, compiler, transpiler, test, runtime, and build caches. Preserve active daemons and watch processes when available. For static claims, use the narrowest syntax, type, lint, compile, or AST check. For behavioral claims, run one test method, case, file, package, or affected component before broader suites. Avoid clearing caches, reinstalling dependencies, rebuilding unaffected targets, recreating environments, or restarting healthy services without evidence. Run clean builds, broad suites, or environment resets only when required by repository authority, stale state, contradictory evidence, release parity, or a trigger below.

### Verification Escalation Triggers

- The user or repository instructions require broader proof.
- The change crosses packages, services, persistence boundaries, or public contracts that narrower proof cannot cover.
- Security, authorization, migration, data-loss, concurrency, release, or production risk makes broader proof proportionate.
- The targeted check fails ambiguously or reveals a wider affected surface.
- The lower tier cannot observe a material part of the completion claim.

Do not run a full suite merely because one exists. Do not rerun an unchanged passing check. Classify a failure as related, unrelated, or unknown; correct only a related failure within scope. After two evidence-driven correction attempts, stop with the failing command, observed evidence, and smallest decision needed. When proof remains narrower than the claim, narrow the claim and state the verified boundary or `Not verified`.

## Adaptive Path

- If current evidence is sufficient, perform the active endpoint, apply proportionate proof, and stop.
- If an exact target is named, apply the Read-Volume Gate and navigate the target plus its nearest authority or test.
- If the target is unknown, run one narrow discovery batch, inspect the best evidence, and narrow scope.
- If operations are independent, batch or parallelize them and synthesize once.
- If an output can change the next operation, sequence them.
- If a current plan exists, execute its remaining work without rediscovery.
- If current or external information is required, query authoritative sources together and confirm freshness.
- If a failure or contradiction appears, reuse it as evidence, reproduce once when needed, and test one bounded hypothesis.
- If work continues from an earlier turn, reuse the current record, plan, outputs, and diff; refresh only changed or stale evidence.

Use the smallest applicable path. These conditions do not grant permission or replace the active workflow.

## Execution Discipline

For non-atomic work, keep only the current evidence, one critical unknown, the next independent batch, the lowest sufficient proof, and the stop condition. Skip any field without a material consumer.

Each TODO must deliver an outcome, remove a blocker, or provide proof. Do not reread unchanged files, repeat successful commands, or restart planning after each result. Reuse evidence until mutation, contradiction, staleness, or dependency failure invalidates it.

Prefer a structured patch or targeted-edit primitive. Do not reproduce unchanged file content. Rewrite a whole file only when generated, mostly changed, or handled by a trusted formatter or codemod.

For routine authorized operations, invoke the tool immediately. Explain first only for approval, safety, a material decision, or a required progress update. Silent controls overall narration and final presentation.

Dispatch reviewers or subagents only when the active workflow permits them and expected wall-clock savings exceed setup and handoff cost.

## Conflict Discipline

Yield to correctness and authority. When Fast conflicts with repository instructions, safety, the active workflow, or a supported completion claim, preserve the higher-authority requirement and take the lowest-cost valid path.

Treat tool errors as evidence. Correct the invocation or assumption once, then broaden only when the error shows that the current scope or source is insufficient.

After changing this skill family, run `python3 scripts/validate_skills.py`.
