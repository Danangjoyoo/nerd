# Loop Profiles and Routes: Routes

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Loop Profiles and Routes router](index.md) and load it only for its named trigger.

## Contents

- [Route Templates](#route-templates)
- [Direct Completion — `direct`, base D0](#direct-completion-direct-base-d0)
- [Options and Recommendation — `options`, base L1](#options-and-recommendation-options-base-l1)
- [Draft and Validate — `draft_validate`, base L1](#draft-and-validate-draft_validate-base-l1)
- [Plan and Validate — `plan_validate`, base L1](#plan-and-validate-plan_validate-base-l1)
- [Bug Finding — `inspect`, base L1](#bug-finding-inspect-base-l1)
- [Plan–Implement–Verify — `piv`, base L2](#planimplementverify-piv-base-l2)
- [TDD or BDD Delivery — `tdd`, base L2](#tdd-or-bdd-delivery-tdd-base-l2)
- [Specification to Delivery — `spec_delivery`, base L2](#specification-to-delivery-spec_delivery-base-l2)
- [PR, CI, and Review Lifecycle — `pr_delivery`, base L3](#pr-ci-and-review-lifecycle-pr_delivery-base-l3)
- [Routine Maintenance — `routine`, base L2](#routine-maintenance-routine-base-l2)
- [Monitor — `monitor`, base L3 for durable waiting](#monitor-monitor-base-l3-for-durable-waiting)
- [Experiment or Optimization — `experiment`, base L2](#experiment-or-optimization-experiment-base-l2)
- [Adaptive Complex Program — `adaptive_program`, base L4](#adaptive-complex-program-adaptive_program-base-l4)

## Route Templates

Use one closest route. Do not combine templates into ceremony; add a stage only
when it consumes evidence or produces a required artifact, decision, effect, or
proof.

### Direct Completion — `direct`, base D0

```text
micro-DoD -> one bounded action or answer -> decisive fresh proof -> stop
```

There is no back edge and no Loop state. If proof exposes a material gap that
needs another adaptive cycle, stop D0 admission and select the new minimum
profile before acting again. Never retain `direct` while raising it above D0.

### Options and Recommendation — `options`, base L1

```text
decision frame and constraints
  -> generate materially distinct options
  -> screen infeasible or dominated choices
  -> compare survivors against declared criteria
  -> recommend one with trade-offs and uncertainty
  -> stop at the Ideate endpoint
```

Return to the frame only when evidence exposes a missing decision criterion.
Do not prototype, mutate, or execute an option unless the endpoint changes.

### Draft and Validate — `draft_validate`, base L1

```text
content contract and audience
  -> smallest complete draft
  -> factual, structural, link/schema, or render checks that apply
  -> revise one evidenced gap
  -> deliver when the artifact DoD passes
```

Use for Specify or Document when one bounded validation back edge is useful.
Raise to L2 only if authorized local implementation-style mutation and repeated
deterministic feedback become part of the requested outcome; raise to L3 for a
durable approval/review wait.

### Plan and Validate — `plan_validate`, base L1

```text
confirmed outcome and DoD
  -> dependencies, risks, and proof map
  -> actionable ordered or partial-order plan
  -> coverage, feasibility, and authority review
  -> revise a concrete planning gap
  -> stop before implementation
```

A Plan endpoint never mutates the target system. An implementation discovery
is recorded as an assumption, probe requirement, or blocker unless the user
changes the endpoint.

### Bug Finding — `inspect`, base L1

```text
scope and risk areas
  -> cheapest static/search probes
  -> targeted dynamic probes when needed
  -> reproduce and validate candidates
  -> deduplicate and prioritize
  -> coverage and residual-risk statement
  -> report
```

Back edges:

- unexamined high-risk surface -> next targeted probe;
- disputed candidate -> reproduce or corroborate;
- repair requested -> new Execute contract using `piv` or `tdd`, normally L2.

Use Review for a bounded artifact bug hunt. Use Diagnose and Nerd Surgery for a
known broken behavior whose cause is requested. Use Execute only when repair is
authorized.

### Plan–Implement–Verify — `piv`, base L2

```text
smallest useful plan
  -> bounded implementation
  -> targeted verification
  -> integration/DoD check
  -> done or cause-labelled back edge
```

Route failures by cause:

- implementation defect -> implementation;
- false assumption or missing dependency -> plan;
- broken or insufficient verifier -> verifier repair;
- endpoint or acceptance ambiguity -> user/spec authority.

Do not return to planning after every failure when the plan was not disproved.

### TDD or BDD Delivery — `tdd`, base L2

```text
select one behavior criterion
  -> write the smallest test or scenario
  -> prove RED for the intended reason
  -> minimal GREEN implementation
  -> refactor while green
  -> affected integration/regression evidence
  -> next criterion or done
```

An invalid RED returns to test or behavior definition. A regression returns to
implementation. Requirement ambiguity returns to specification authority.

Nerd Execute owns the test-first micro-workflow. Nerd Loop owns the root DoD,
current criterion, history, budget, and decision to continue or reframe; do not
duplicate Execute's mechanics.

### Specification to Delivery — `spec_delivery`, base L2

```text
baseline specification and criterion traceability
  -> plan one vertical slice
  -> implement
  -> verify against mapped criteria
  -> integrate
  -> next slice or cause-labelled revision
```

Back edges:

- code misses a clear criterion -> plan or implementation;
- specification is contradictory or materially ambiguous -> clarification;
- proposed specification change alters endpoint or DoD -> user confirmation.

Use L3 for several independently delivered components or approval handoffs. Use
L4 when interfaces, data, and architecture materially co-evolve.

### PR, CI, and Review Lifecycle — `pr_delivery`, base L3

```text
plan
  -> code
  -> local verification
  -> authorized push/open PR
  -> PAUSE for CI or review event
  -> classify feedback
  -> update plan or code when relevant
  -> reverify
  -> merge-readiness result or next wait
```

The graph is simple; the profile is managed because the task crosses external
effects, durable waits, and human feedback. Begin local work at L2 if useful,
then commit an L3 checkpoint before the first push or wait.

This route itself requires authenticated event-driven wake and effect
reconciliation capabilities; the caller cannot omit a CI/review or
external-receipt signal to bypass those admission requirements.

Classify feedback:

- related code or CI failure -> plan/implementation;
- flaky or infrastructure failure -> diagnose, policy-governed retry, or wait;
- unrelated failure -> record a blocker instead of changing product code;
- review request changing endpoint or acceptance -> authority checkpoint.

Push, PR creation, review response, merge, and deployment remain separate
external-effect authorities. The route does not grant them.

### Routine Maintenance — `routine`, base L2

```text
load last accepted contract and fresh current state
  -> compute bounded delta
  -> apply authorized routine action
  -> focused verification
  -> record outcome and next semantic trigger
  -> stop
```

Use for recurring dependency updates, queue triage, generated reports, or other
stable daily work. Reuse the route and confirmed behavioral guidance, but use a
fresh root execution episode and verifier evidence. Do not treat yesterday's
success as today's proof.

Raise to L3 when a run crosses PR/CI, human review, remote mutation, or delayed
conditions. A scheduler or recurring monitor is a separate authorized runtime
capability; the route does not create one.

### Monitor — `monitor`, base L3 for durable waiting

```text
observe -> compare with stop/wake conditions -> report change or PAUSE -> observe
```

Use the platform's wait or monitoring mechanism. Persist the condition and last
observation, then consume no active loop budget while waiting. A one-time
immediate recheck may remain L1. Selecting durable `monitor` itself requires an
authenticated wake-event capability.

### Experiment or Optimization — `experiment`, base L2

```text
baseline -> hypothesis -> controlled change -> compare with best checkpoint
  -> accept or revert -> update hypothesis
```

At L2 the experiment is single-owner, local, immediately observed,
deterministic enough for its declared comparison, and reversible to the best
checkpoint. Raise to L3 when it needs managed recovery beyond a simple
single-writer checkpoint, delayed/noisy observation, an external receipt, or
formal human judgment. Use L4 for coupled
SLOs, production experiments, high-consequence interventions, or proxy-only
success. Declare the comparison, noise treatment, improvement-per-cost,
plateau, rollback, and hard-budget rules at the profile that actually needs
them.

Use this route only at Diagnose for a bounded non-repair diagnostic experiment,
or at Execute for authorized mutation. Explore remains `inspect` and
non-mutating.

### Adaptive Complex Program — `adaptive_program`, base L4

```text
contract, DoD, authority, and budget
  -> architecture, threat/data risks, and rollback
  -> partially ordered child-loop map
  -> execute ready children at their cheapest profiles
  -> integrate contracts and artifacts
  -> system, adversarial, and operational verification
  -> staged/canary release when authorized
  -> observe
  -> advance, repair, reframe, or roll back
```

Examples: zero-downtime multi-service/database migration, cross-system security
remediation, staged platform replacement, or regulated release.

Cause-labelled back edges:

- child-local defect -> that child's route;
- interface mismatch -> affected children plus integration contract;
- architecture contradiction -> architecture decision gate;
- rollout regression -> rollback or stabilization;
- endpoint change -> user authority.
