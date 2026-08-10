# Iteration Control: Core

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

## Contents

- [Core Answer](#core-answer)
- [What Counts as One Iteration](#what-counts-as-one-iteration)
- [Attempts and retries](#attempts-and-retries)
- [The Three Synchronized Views](#the-three-synchronized-views)
- [1. Loop Map — future and whole-task awareness](#1-loop-map-future-and-whole-task-awareness)
- [2. Current Iteration Contract — present awareness](#2-current-iteration-contract-present-awareness)
- [3. Ledger and checkpoint — past and recovery awareness](#3-ledger-and-checkpoint-past-and-recovery-awareness)

## Core Answer

Define an iteration as one bounded, evidence-producing state transition:

~~~text
committed state
-> rehydrate and reconcile
-> select one ready focus
-> perform one bounded attempt
-> verify its result
-> commit facts, evidence, and plan consequences
-> next committed state
~~~

An iteration is not automatically one model turn, one tool call, one file edit, or one plan checkbox. It may contain several tightly coupled actions, but it has exactly one primary objective, one declared boundary, and one verification decision.

Use three synchronized views when S2/S3 durability, dependency management, or
recovery requires them:

1. **Loop Map:** The big picture—root goal, DoD coverage, dependencies, completed work, ready work, blockers, children, and remaining budget.
2. **Current Iteration Contract:** The low-level focus—what this iteration is trying to change or learn, why now, its permitted scope, expected evidence, verifier, and exit conditions.
3. **Iteration Ledger and checkpoint:** The durable factual history—what was selected, attempted, observed, verified, committed, superseded, or left unresolved.

The Loop Map is a revisable forecast. The Current Iteration Contract is the active commitment. The ledger is the history of record. Do not collapse them into one mutable to-do list. For S1, retain their minimum semantics in one compact session packet: root DoD, current focus, allowed boundary, expected evidence, latest result, remaining gap, and next discriminating step.

Use a **receding horizon**: look ahead far enough to avoid local myopia, commit only the next bounded focus, then observe and replan. A long forecast may guide the next decision, but it must not authorize open-loop execution after the world changes.
## What Counts as One Iteration

For S2/S3, one iteration declares the full fields below. For S1, retain only
the fields needed to prevent focus, authority, or evidence drift; opaque durable
identities and ownership metadata are not required.

- **Identity:** Common admission hash and budget revision plus run, loop,
  iteration, and attempt IDs.
- **Parent trace:** Root goal, parent task, and DoD criteria advanced.
- **Entry state:** Workspace or environment revision and verified preconditions.
- **Focus:** One bounded result, gap, hypothesis, or uncertainty.
- **Why now:** Dependency, critical path, risk, evidence, or deadline reason.
- **Authorized action boundary:** Files, systems, tools, side effects, and cost allowed.
- **Expected result:** Observable state or information the attempt should produce.
- **Verifier:** How the result and regressions will be checked.
- **Exit:** Verified, disproved, blocked, inconclusive, interrupted, or exhausted.
- **Commit rule:** Facts, evidence, artifacts, discovered work, and plan changes to persist.

Model a focus as a temporally extended action:

~~~text
Focus = {
  initiation_conditions,
  bounded_method,
  local_DoD,
  abort_conditions,
  parent_integration_target
}
~~~

Use one iteration when several actions are inseparable for useful verification, such as edit plus compile plus focused test. Split the work when it has an independently meaningful outcome, different authority, separate verifier, distinct artifact ownership, substantial uncertainty, or enough complexity to require its own loop.

### Attempts and retries

Keep iteration identity separate from worker attempts:

- Retry the same iteration with a new attempt ID only for the same focus and strategy after a transient or recoverable execution failure.
- Start a new iteration when the hypothesis, strategy, scope, artifact base, or intended evidence materially changes.
- Never erase a failed attempt. Record it and link the successor.
- Do not increment a single global ordinal across parallel children. Ordinals are local presentation order; IDs and causal links carry identity.
## The Three Synchronized Views

### 1. Loop Map — future and whole-task awareness

The Loop Map contains:

- Root contract, DoD version, and Convergence Contract version.
- Common admission envelope/hash and cumulative authenticated budget revision.
- Versioned task network and genuine dependency edges.
- Current status and fresh evidence for every mandatory DoD criterion.
- Completed, active, ready, waiting, blocked, superseded, and optional work.
- Child-loop identities, contracts, ownership, and integration status.
- Consumed Memory proposal reference, routing chain/registry/authority hashes,
  full-chain preflight, and committed cursor, when any.
- Best verified checkpoint and remaining global budget.
- Assumptions, threats, unresolved decisions, and plan-revision history.

It answers: “Where are we in the whole task, and which outcomes can legally become active next?”

### 2. Current Iteration Contract — present awareness

Keep exactly one primary current focus per loop. The contract answers:

- What is this iteration about?
- Which parent result and DoD gap does it advance?
- Why is it selected over other ready work?
- What evidence would count as progress, learning, or failure?
- What may change, and what must remain unchanged?
- When must this iteration stop, pause, or create a child loop?

Parallel work belongs in distinct child loops, each with its own current focus and ledger stream. Do not represent several concurrently mutating agents as one current iteration.

### 3. Ledger and checkpoint — past and recovery awareness

The ledger records immutable events. A checkpoint is a derived, compact view at a committed ledger revision. It answers:

- What actually happened?
- What evidence is current?
- Which side effects may already have occurred?
- Which attempt owns the focus?
- What was the last fully committed boundary?
- Which plan and contract versions produced the decision?

Transcript, summaries, and semantic memory are advisory retrieval surfaces. They are not authoritative execution state.
