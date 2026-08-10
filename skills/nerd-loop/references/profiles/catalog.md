# Loop Profiles and Routes: Catalog

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Loop Profiles and Routes router](index.md) and load it only for its named trigger.

## Contents

- [Profile Catalog](#profile-catalog)
- [D0 — Direct Completion](#d0-direct-completion)
- [L1 — Minimal Loop](#l1-minimal-loop)
- [L2 — Simple Loop](#l2-simple-loop)
- [L3 — Managed Loop](#l3-managed-loop)
- [L4 — Complex Loop](#l4-complex-loop)

## Profile Catalog

### D0 — Direct Completion

Use when there is no useful back edge: answer, transform, make one tiny
reversible change, run a decisive check, and stop.

```text
micro-DoD -> direct action -> fresh proof -> typed result
```

Minimum mechanics:

- one resolved endpoint and authority boundary;
- one-sentence observable micro-DoD;
- the smallest sufficient action;
- fresh proof when making a completion claim; and
- `DONE` or a typed non-success result.

Do not create a Loop Map, convergence history, TODO list, child loop, or durable
ledger. Persist an effect receipt only if recovery or ambiguity requires it.

Examples: correct a typo and run its direct check; answer from current evidence;
change one static value with a parser validation.

### L1 — Minimal Loop

Use for bounded inspection, bug finding, triage, fact search, review, diagnosis,
or a sandbox probe where one focus and a small number of adaptive evidence
steps suffice.

```text
scope -> probe -> validate evidence -> report or select next probe
```

Minimum mechanics:

- compact DoD with scope and evidence standard;
- exactly one current focus;
- an in-session evidence record;
- one cost/coverage boundary; and
- residual uncertainty or risk in the result.

Do not create child loops or durable project state by default. A repeated probe
must target a named evidence gap; do not broaden aimlessly.

For “find bugs,” `DONE` means the declared evidence-coverage criteria pass,
every candidate has a validated disposition, every reported finding meets its
evidence rule, and the required residual-risk statement is complete. Finishing
a probe plan is activity, not proof. “No findings” means no validated findings
within the declared scope, coverage, and budget, never proof that no defects
exist.

### L2 — Simple Loop

Use for single-owner local delivery with a known or mostly stable route and
deterministic feedback: normal code changes, TDD/BDD slices, focused repair,
small spec-to-code work, or routine maintenance.

```text
smallest route slice -> act -> targeted verify -> integrate -> done or replan
```

Minimum mechanics:

- compact DoD;
- small route graph or lightweight plan;
- one Current Iteration Contract;
- targeted verification after each behavior-affecting cycle;
- compact failure, progress, and replan record; and
- an in-session checkpoint, raised to durable state only when needed.

Do not build a full dependency graph, durable ledger, convergence window, or
subagent organization merely because the task has several sequential steps.
Replan only when evidence invalidates the current route.

### L3 — Managed Loop

Use when simple work must survive or coordinate across process boundaries: PR
and CI cycles, review waits, external integrations, resumable delivery, shared
resources, human gates, or independently verifiable child work.

```text
map -> act -> persist receipt -> pause/reconcile -> verify/integrate -> replan
```

Minimum mechanics:

- complete DoD and integration criteria;
- versioned Loop Map and current focus;
- durable single-writer ledger or checkpoint;
- semantic scheduling and event-driven pause/resume;
- ownership and resource claims where relevant;
- stable idempotency keys for ambiguous external retries;
- explicit child contracts when work is delegated; and
- compact convergence and stall responses.

A route may begin at L2 and escalate immediately before its first external
push, long wait, handoff, or parallel child. Earlier local work remains valid.

### L4 — Complex Loop

Use for adaptive, governed programs: coupled subsystems, architecture or
contracts evolving during delivery, high-impact migrations and releases,
security remediation across boundaries, staged rollout, or success measured by
noisy and interacting signals.

```text
contract and risk model
  -> architecture and rollback
  -> partially ordered child loops
  -> integrate interfaces and artifacts
  -> verifier portfolio
  -> staged release and observation
  -> advance, repair, reframe, or roll back
```

Minimum mechanics:

- full DoD, Convergence Contract, authority, budget, and stop policy;
- hierarchical Loop Maps and dependency/interface governance;
- transactional or otherwise race-safe ledger and fenced ownership;
- isolated child loops, each using its own cheapest adequate profile;
- best verified checkpoints and rollback or compensation plans;
- multi-layer and, when justified, independent verification;
- explicit human and external-effect gates; and
- staged observation with cause-labelled repair, reframe, and rollback paths.

An L4 parent must not force every child to pay L4 overhead.
