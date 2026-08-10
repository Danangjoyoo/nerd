# Iteration Control in Task-Completion Loops

Use [the Nerd Loop Runtime Contract](runtime-contract.md) as the normative
source for authority, state classes, closed status vocabularies, transition
priority, effect ordering, and terminal outcomes. This reference supplies the
full planning, scheduling, persistence, and recovery techniques routed mainly
to S2/S3. D0 has no iteration state; ordinary S1 compresses these concepts into
one current-focus and evidence packet rather than creating durable artifacts.

## Contents

- [Core answer](#core-answer)
- [What counts as one iteration](#what-counts-as-one-iteration)
- [The three synchronized views](#the-three-synchronized-views)
- [Representing the whole plan](#representing-the-whole-plan)
- [Iteration sequence](#iteration-sequence)
- [Finding the next iteration](#finding-the-next-iteration)
- [Scheduling subtasks](#scheduling-subtasks)
- [Initiative when the plan is insufficient](#initiative-when-the-plan-is-insufficient)
- [Iteration ledger](#iteration-ledger)
- [Ledger placement and identity](#ledger-placement-and-identity)
- [Race safety and parallel agents](#race-safety-and-parallel-agents)
- [Crash recovery and resumption](#crash-recovery-and-resumption)
- [Preventing forgetting](#preventing-forgetting)
- [Failure modes and anti-patterns](#failure-modes-and-anti-patterns)
- [Loop Map template](#loop-map-template)
- [Current Iteration Contract template](#current-iteration-contract-template)
- [Ledger event template](#ledger-event-template)
- [Research basis](#research-basis)

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

## Representing the Whole Plan

Represent work as a versioned, partially ordered task network rather than a prematurely fixed list:

~~~text
P_v = (V, E)
~~~

Each node in V should contain:

- Stable work ID and parent ID.
- Kind: compound, primitive, probe, verification, integration, or approval.
- Intended outcome and mapped DoD criterion.
- Entry preconditions and triggering condition.
- Local DoD and required evidence.
- Inputs, output contract, artifact scope, and resource claims.
- Estimated cost, risk, reversibility, and expiration.
- Status and status evidence.
- Provenance: planned, verifier-discovered, user-added, policy-required, or inferred.

Add an edge in E only for a real constraint:

- Hard prerequisite or causal support.
- Required evidence or approval.
- Safety or authority ordering.
- Shared-resource or mutation conflict.
- Data or artifact dependency.
- Parent integration requirement.

Do not order independent nodes merely because they appeared in that order in the first plan. Partial ordering preserves flexibility, exposes parallelism, and makes local plan repair possible.

Use explicit states such as:

| State | Meaning |
| --- | --- |
| PROPOSED | Discovered but not yet admitted into the authorized plan |
| PLANNED | Admitted, but one or more entry conditions are not satisfied |
| READY | All hard entry conditions are freshly satisfied |
| CLAIMED | Assigned to one owner but not yet executing |
| ACTIVE | Current bounded attempt is executing |
| VERIFYING | Mutation stopped while required checks run |
| VERIFIED | Local DoD passed with current evidence |
| WAITING | Waiting on a declared event, time, approval, or child result |
| BLOCKED | No authorized route can currently satisfy an entry condition |
| SUPERSEDED | Replaced by a recorded plan revision |
| CANCELLED | Explicitly removed by authorized decision |

“Worked on” and “agent says complete” are not plan states.

### Readiness

At committed state t, calculate:

~~~text
Ready_t = {
  w |
  w is admitted and not terminal
  and every hard predecessor is freshly verified
  and its trigger is true
  and its inputs still match their declared revisions
  and required authority and resources are available
  and no unresolved conflict or threat applies
}
~~~

If Ready_t is empty while the DoD remains unmet, classify why. The result may be BLOCKED, WAITING, INCONCLUSIVE, or a need to repair or extend the plan. Do not invent an action merely to keep the loop moving.

### Bounded decomposition

Every child must be strictly narrower than its parent in outcome, scope, uncertainty, or abstraction level. Give recursive decomposition a maximum depth and budget. Reject a child that simply restates its parent without adding a new verifier, capability, boundary, or tractable unit.

## Iteration Sequence

### Before the first iteration

1. Baseline the user goal, Focus Record, DoD, profile-sized convergence rule,
   authority, and finite budget; run deterministic route admission and freeze
   its envelope/hash plus initial authenticated cumulative budget state.
2. Observe the initial workspace or environment revision.
3. Build the minimum useful Loop Map: mandatory outcomes, dependencies, known probes, verification, and integration.
4. Create unique run and root-loop identity when S2/S3 requires recovery or coordination.
5. Record the S1 packet, or persist S2/S3 contracts and the initial plan revision, before mutation.

Do not attempt to predict every future action. Plan the full outcome structure and enough near-term detail to choose a safe first focus.

### At every iteration boundary

1. **Rehydrate.** Load the exact admission envelope, cumulative budget state,
   last committed checkpoint, contract versions, active ownership, and later
   ledger events.
2. **Recover.** Resolve any selected or started attempt without a terminal receipt before selecting new work.
3. **Reconcile.** Observe actual workspace, environment, user updates, children, and external effects. Mark contradictions and stale evidence.
4. **Gate.** Apply safety, authority, cancellation, DoD, convergence, and hard-limit rules.
5. **Repair the map.** Invalidate affected descendants, restore threatened prerequisites, and admit justified discoveries.
6. **Compute readiness.** Derive the ready set from current facts; do not trust a stale next-action pointer.
7. **Select and claim.** Choose one focus, record why now, claim its mutation scope, and persist the Current Iteration Contract.
8. **Execute.** Perform only the bounded method. Record external-effect intent and receipts durably.
9. **Verify.** Stop mutation and run the local DoD, affected regressions, and required integration checks.
10. **Commit.** Append observations, evidence, outcome, cost, best checkpoint,
    new work, invalidations, release or transfer ownership, authenticated
    one-unit budget consumption, and the next cumulative budget revision.
11. **Replan.** Recompute plan status and candidate successors. Do not execute a successor until the commit is durable.

Use this compact lifecycle:

~~~text
define contracts -> map work
-> [rehydrate -> reconcile -> select -> execute -> verify -> commit -> replan]
-> parent integration
~~~

### Horizon policy

Maintain three horizons:

- **Strategic horizon:** The whole Loop Map and root-DoD coverage.
- **Tactical horizon:** A small set of plausible next focuses checked for downstream feasibility.
- **Committed horizon:** Exactly one current iteration per loop.

Shorten the tactical horizon when observations are volatile, actions are risky, measurements are uncertain, or downstream assumptions are fragile. Lengthen it when the environment is stable, dependencies are deterministic, and setup costs make batching valuable.

## Finding the Next Iteration

The next iteration is derived, not remembered.

### Lookup and reconciliation order

At every boundary, look up:

1. Current mandatory constraints and the latest authorized user direction.
2. Run and loop identity, ownership epoch, interruption, and cancellation state.
3. Versioned Focus Record, DoD, Convergence Contract, common admission hash,
   and authenticated cumulative budget state.
4. Latest committed ledger checkpoint plus all later valid events.
5. Actual workspace, external-system, child-loop, and verifier state.
6. Current plan revision, open conditions, and ready-set candidates.
7. Relevant verified lessons or, only after explicit current-user activation
   and confirmation, the frozen Nerd Memory contract, revalidated against
   current reality.

If these sources disagree, pause selection and reconcile them. Actual external state may reveal that the ledger is stale; the ledger may reveal that an apparent artifact is unverified or belongs to another run. Preserve both observations and resolve the inconsistency explicitly.

Never use a prose field named “next action” as sole authority. Treat it as a cached proposal whose preconditions, plan version, base revision, and ownership must still pass.

### Selection priority

Use hard eligibility gates first, then a lexicographic priority rather than one weighted score that could trade a mandatory constraint for convenience:

1. Resolve safety, authority, cancellation, or ambiguous external-effect state.
2. Repair invalid measurement, corrupted state, or a broken mandatory invariant.
3. Perform required current-state verification or parent integration.
4. Advance a blocker or earliest mandatory dependency on the root critical path.
5. Select work expected to close the largest mandatory gap or unlock the most required work.
6. Select a bounded information probe when its answer can change the next mandatory decision.
7. Prefer lower risk, lower cost, reversibility, and context locality among otherwise equivalent choices.
8. Apply aging or a deadline rule so difficult necessary work cannot starve.
9. Break remaining ties deterministically by stable work ID.

Record the chosen node, rejected alternatives, and why-now reason. Selection is itself a decision that must be auditable.

### Next action versus next iteration

A tool action may be the next operation inside the current contract. The next iteration begins only after the current iteration reaches a committed boundary. Do not switch focus because a newly noticed task looks interesting; first record it, classify it, and finish or safely suspend the current focus.

## Scheduling Subtasks

### Inline action or child loop

Keep a subtask inside the current iteration only when it is a small, tightly coupled action with no independently useful outcome.

Create a child loop when the subtask has one or more of:

- Its own multi-step uncertainty or convergence.
- An independent deliverable or verifier.
- A different owner, capability, authority, or mutation scope.
- Parallel execution value.
- Meaningful pause, retry, or recovery needs.
- A result that the parent can accept or reject through a defined interface.

Every child loop needs a local DoD, parent criterion, input revision, output contract, verifier, budget, ledger namespace, and parent integration rule.

### Execute now

Start the subtask now when:

- It is a hard prerequisite for the current focus.
- It resolves an ambiguous side effect or broken verifier.
- It removes a safety, feasibility, or authority risk before irreversible work.
- Its result is high-information and can materially change the next decision.
- It unlocks mandatory critical-path work and its inputs are current.
- Delay would make evidence stale or increase cost materially.

### Defer until a condition

Keep the subtask PLANNED or WAITING when:

- Its prerequisite, input revision, approval, resource, or child result is unavailable.
- Current work is likely to invalidate its output.
- It is useful only after another criterion reaches a declared state.
- It conflicts with an active mutation scope.
- It is optional improvement that does not advance the current DoD.
- Batching later is cheaper without increasing risk or blocking mandatory work.

Write the wake-up condition, not merely “later.”

### Avoid “N iterations later”

Iteration ordinals are local and plans change. Parallel children make a global N ambiguous. Prefer:

~~~text
when DOD-3 is VERIFIED
when artifact revision R is committed
when child loop C emits an accepted terminal receipt
after the performance metric remains in range for duration T
at deadline D
when resource or approval A becomes available
~~~

Use “after N iterations” only when iteration count is itself a valid experimental condition, retry policy, sampling interval, or mandated dwell rule. Even then, attach it to a specific loop and starting iteration ID, and recheck all semantic preconditions when it fires.

### Parallel execution

Parallelize only ready child loops that have:

- Independent or explicitly coordinated dependencies.
- Disjoint mutation scopes, isolated workspaces, or enforced resource claims.
- Frozen input revisions and defined output artifacts.
- Separate ledgers, owners, budgets, and cancellation behavior.
- A deterministic parent merge and integration verifier.

A child’s self-declared completion does not close its parent. The parent records acceptance or rejection of the child’s terminal evidence, then verifies the integrated state.

## Initiative When the Plan Is Insufficient

A plan is a route hypothesis, not an outcome authority. New mandatory work may be discovered through observations, failed preconditions, counterexamples, integration failures, or changed external state.

### Discovery record

Before inserting work, record:

~~~yaml
discovered_work:
  proposed_id:
  because:
  source_event_or_evidence:
  root_dod_trace:
  closes_or_unlocks:
  authority_and_scope:
  estimated_cost_and_risk:
  required_verifier:
  expiration_or_exit_condition:
~~~

### Admission classes

| Class | Initiative rule |
| --- | --- |
| Mandatory repair | Auto-admit when it restores a violated invariant or prerequisite, resolves a causal threat or counterexample, repairs required verification, or integrates a verified child within existing authority |
| Information probe | Auto-admit only when the answer can change a mandatory decision; timebox it and define its exit condition first |
| Route adaptation | Auto-revise sequencing, decomposition, or strategy when the outcome, DoD, authority, external effects, and hard budget remain unchanged |
| Optional improvement | Keep outside the mandatory path unless the user admits it or unused budget explicitly permits it after the DoD |
| Endpoint change | Ask for authorization when it adds, removes, weakens, or materially reinterprets the goal, DoD, scope, safety, approval, external effects, or hard budget |

The agent may take initiative over the route inside the authorized action space. It may not silently take authority over the endpoint.

### Plan revision

For every revision:

- Increment the plan version.
- Preserve the previous plan and completed evidence.
- State the trigger, added or removed nodes, changed dependencies, invalidated evidence, budget effect, and authority.
- Invalidate only affected descendants when a local repair is credible.
- Fully replan when the root contract changes, the model is fundamentally wrong, or local repair cannot restore feasibility.
- Recompute the ready set and critical path.

Do not interpret honest discovery as task failure. Also do not permit infinite backlog growth: bound decomposition depth, revision count, discovery budget, and optional work.

## Iteration Ledger

Use a durable ledger for a task that must survive interruption or context loss,
coordinates independent children or writers, spans expensive work whose
recovery matters, or has externally consequential effects or ambiguous
receipts. Multiple in-session iterations alone do not require durability. S1
uses a compact in-memory packet and cannot claim restart recovery.

Call the authoritative record a **run ledger**, not a temporary scratch note. Scratch data may be temporary; the execution cursor and evidence receipts must survive for as long as resumption or audit is required.

### Event-sourced core

Prefer immutable events plus derived snapshots:

~~~text
authoritative events -> replay/projection -> current checkpoint and Loop Map
~~~

Useful event types include:

- RUN_STARTED and LOOP_DEFINED.
- CONTRACT_BASELINED or CONTRACT_VERSIONED.
- PLAN_BASELINED, WORK_DISCOVERED, and PLAN_REVISED.
- `INTENT_COMMITTED`, atomically containing iteration selection, attempt claim,
  action intent, stable operation/idempotency identity, expected revisions,
  owner/epoch, resource scope, verifier, abort rule, common admission hash,
  current budget revision, `ITERATION | LOOP` DoD scope, the exact accepted DoD
  contract, optional proposal/chain/profile routing binding, and fence when
  required.
- `ACTION_OBSERVED` with receipt, failure, or `OUTCOME_UNKNOWN` plus references
  for cost, invalidation, discovery, best state, and ownership disposition.
- `ACTION_RECONCILED` under the same identity when outcome was unknown.
- `VERIFICATION_RECORDED`, bound to the resolved observation and carrying the
  complete DoD result: structured authenticated evidence for every mandatory
  criterion and integration check, exact accepted definition hash/revision,
  current artifact revision, criterion verifier and observed verdict, explicit
  approval decision when required, and a derived completion verdict.
- ITERATION_COMMITTED (including its hashed commit identity for routing,
  authenticated one-unit budget consumption, and next cumulative budget state),
  ITERATION_ABORTED, or ATTEMPT_ABANDONED.
- CHILD_STARTED, CHILD_TERMINAL_OBSERVED, CHILD_ACCEPTED, or CHILD_REJECTED.
- CHECKPOINT_CREATED.
- ROUTING_BOUND, ROUTING_PROFILE_ACTIVATED, ROUTING_PROFILE_REPEATED,
  ROUTING_PROFILE_SATISFIED, ROUTING_COMPLETED, or ROUTING_BLOCKED.
- `LOOP_DONE` with an authenticated receipt bound to the loop-scoped DoD,
  admission, commit, and next budget state, or `LOOP_TERMINATED` with an
  authenticated typed non-success receipt.

Store concise decisions and evidence references, not private chain-of-thought. Redact credentials, secrets, sensitive payloads, and unnecessary raw transcripts.

### Transaction boundary

Persist selection before executing:

1. Atomically append one complete `INTENT_COMMITTED` event with contract/plan/
   base revisions, event/iteration/attempt/focus IDs, owner/epoch, scope,
   intended evidence, abort rules, stable operation/idempotency keys, common
   admission hash, current cumulative budget revision, DoD scope, the exact
   accepted DoD contract, any exact routing proposal/chain/profile binding, and
   an S3 fence before an external side effect.
2. Execute outside the ledger transaction.
3. Append exactly one revisioned `ACTION_OBSERVED` receipt, failure, or
   `OUTCOME_UNKNOWN`, with the same attempt/operation/idempotency/fence identity
   and its cost, invalidation, discovery, best-state, and ownership references.
4. Reconcile an unknown outcome under those same identities, then append
   verification bound to the resolved observation, the intent's accepted
   DoD hash/artifact revisions, authenticated per-criterion observed verdicts,
   explicit approval decisions, and a completion verdict derived from the full
   result.
5. Commit the iteration with a reference to that verification. Accept
   `VERIFIED` exactly when the action receipt exists and the bound DoD verdict
   passes. Consume exactly one budget unit, emit the next authenticated budget
   state and hash-bound commit/event/revision identity used by a routing
   receipt, then select exactly one cause-labelled successor, registered pause,
   handoff, `LOOP_DONE`, or typed `LOOP_TERMINATED`. Condense context only after
   the next edge is committed.

Every event uses expected revision. Exact canonical duplicate event IDs are
idempotent; conflicting reuse, stale writers, fence changes, or cross-attempt
receipts fail closed. The pure reducer validates this projection; the durable
adapter must separately prove atomic append/CAS and crash recovery.

Never hold a database transaction open during model inference, tests, network calls, or human approval.

## Ledger Placement and Identity

### Placement priority

Use this order:

1. Runtime-provided durable workflow/checkpoint storage.
2. Explicitly configured durable database or state URI.
3. Repository-approved state location excluded from version control.
4. Per-user application-state directory keyed by a workspace fingerprint.
5. Secure runtime or temporary directory only when restart survival is not required.

On systems following the XDG Base Directory specification, histories and restartable state belong under XDG_STATE_HOME; sockets, leases, and disposable login-lifetime coordination belong under XDG_RUNTIME_DIR. Do not place authoritative resumable state in a general temporary directory.

Use a layout like:

~~~text
<state-root>/nerd-loop/
  workspaces/<workspace-fingerprint>/
    workflows/<workflow-id>/
      runs/<run-id>/
        ledger database or event streams
        checkpoints/
        evidence references/
~~~

Do not write hidden state into the repository merely because it is convenient. Repository-local placement needs repository policy or user authorization, an ignore rule, and a cleanup contract.

### Unique identity

For S2/S3, use opaque, collision-resistant IDs such as UUIDv7:

- workflow_id: stable logical user task across resumed physical runs.
- run_id: one physical execution generation.
- loop_id: one root or child loop instance.
- iteration_id: one logical bounded focus.
- attempt_id: one execution or retry of that iteration.
- event_id: one immutable event and idempotency identity.
- ordinal: display order local to a loop, allocated transactionally.

Do not use timestamps, process IDs, prompt slugs, agent names, or iteration numbers alone as unique identity. Keep human-readable labels separate from IDs.

For an ephemeral file-only ledger, create the run directory atomically with a secure unique-directory primitive. Unique naming prevents two independent runs from sharing a path; it does not solve concurrent writes within one run.

## Race Safety and Parallel Agents

### Storage choices

- **Single agent, one host:** A private append-only stream with atomic snapshots can be sufficient.
- **Several local processes:** Prefer one SQLite database per workspace with transactional writes; WAL allows concurrent readers but SQLite still intentionally serializes writers.
- **Several hosts or shared service:** Use a transactional server database or durable workflow engine with optimistic concurrency, leases, and retries.

Do not use shared Markdown, YAML, JSON, or uncoordinated NDJSON appends as an authoritative multi-writer ledger.

### Single-writer streams

Prefer one writer per loop stream:

- The parent coordinator owns the parent stream.
- Each parallel child owns a different child-loop stream.
- A child sends a result command or receipt to the parent; it does not append directly to the parent history.
- The parent records CHILD_ACCEPTED or CHILD_REJECTED with the exact child revision and result hash.

### Expected revision and idempotency

Every append should provide:

- Expected current stream revision.
- Owner identity and ownership epoch when applicable.
- Stable command or operation ID.
- Stable event IDs and payload hashes.

If the expected revision changed, reload and recompute. Never override the conflict with last-writer-wins.

If commit acknowledgement is ambiguous, retry with the same IDs. A duplicate with identical content may return the original receipt; the same ID with different content must be rejected.

### Leases and fencing

Use a renewable lease to recover abandoned ownership, and a monotonically increasing fencing epoch to reject stale writers. A lease alone is insufficient: an old paused worker can resume after expiry unless the ledger and affected resource reject its older epoch.

If fencing cannot be enforced on an external resource, combine idempotency keys, base-revision checks, isolated workspaces, and explicit reconciliation. Record the limitation.

### Artifact races

A unique ledger prevents metadata collision, not code, file, deployment, or database collision. Before parallel mutation, claim the affected resource set or provide isolated worktrees/sandboxes. Revalidate the artifact base revision before integration.

## Crash Recovery and Resumption

On resume:

1. Reopen the exact workflow and run identity; never guess from the newest directory alone.
2. Verify ledger and snapshot schema versions and hashes.
3. Replay from the latest verified checkpoint through later committed events.
4. Find nonterminal attempts and inspect their ownership lease.
5. Acquire a higher fencing epoch before takeover.
6. Reconcile planned external effects with target-system receipts.
7. Append ATTEMPT_ABANDONED or RECOVERY_STARTED as appropriate.
8. Rebuild the Loop Map, invalidate stale evidence, and resume from committed facts.

### Ambiguous effects

A crash after an external effect but before its receipt creates an unknown outcome. Do not blindly repeat it.

- Query the target with the stable operation ID when possible.
- Retry only if the operation is idempotent or the target proves it did not occur.
- Compensate only under explicit authority.
- Otherwise retain `OUTCOME_UNKNOWN` and escalate or repair the reconciler.

Exactly-once invocation across an independent ledger and external system is generally unavailable without a shared transaction. Design for idempotent effects and exactly-once recording of accepted receipts.

### Snapshots and bounded history

Snapshots are derived acceleration structures, not truth replacements. Include:

- Ledger revision covered.
- Contract and plan versions.
- Current Loop Map and focus.
- DoD criterion vector and fresh evidence references.
- Best verified checkpoint.
- Budgets, open children, blockers, and ambiguous effects.
- State schema and content hashes.

When history becomes too large, close the physical run with an explicit continuation event and start a new run generation carrying the minimum verified state plus predecessor links. Never silently truncate active history.

## Preventing Forgetting

### Deterministic iteration packet

At the start of every iteration, inject or render a concise packet from authoritative state:

~~~text
workflow / run / loop / iteration identity
root goal and DoD version
parent outcome and integration target
current focus and why now
workspace and plan revisions
allowed scope and forbidden effects
entry evidence and latest failure fingerprint
local verifier and exit rules
best verified checkpoint
ready alternatives, blockers, and remaining budget
~~~

This packet should be generated from the ledger and contracts, not reconstructed from model recollection.

### Commit-before-switch

For S2/S3, before switching focus, delegating, compacting context, pausing, or
yielding, durably commit the following. For S1, update the compact session
packet before choosing another focus:

- Record the current artifact or environment revision.
- Record action receipts and verifier results.
- Record unresolved uncertainty and failure fingerprints.
- Update task status and invalidated evidence.
- Persist the next trigger candidates and why they are eligible.
- Create a committed checkpoint.

For S2/S3, no durable outcome commit means the iteration is still in flight.
For S1, do not switch focus until its compact packet contains the outcome and
fresh evidence.

### Separate memory kinds

Keep distinct:

- **Execution truth:** Contracts, current state, evidence, ownership, and ledger events.
- **Plan projection:** Revisable future work and ready set.
- **Episodic lessons:** Failed strategies and reusable verified observations.
- **Semantic knowledge:** General facts and skills reusable across loops.
- **Transcript:** Communication record.

Only execution truth and fresh evidence may authorize mutation or completion. Lessons and semantic retrieval can suggest actions but must be checked against the current state.

### Context condensation

Condensation may shorten model-visible history, but:

- Keep immutable source events and evidence outside the summary.
- Preserve IDs and source revisions in every condensed statement.
- Never summarize away the root goal, DoD, current focus, pending approvals, ambiguous side effects, or blockers.
- Treat a summary conflict as a reason to reload the source, not choose the more convenient wording.

## Failure Modes and Anti-Patterns

| Anti-pattern | Failure | Stronger rule |
| --- | --- | --- |
| Fixed full execution script | Later steps use assumptions invalidated by earlier results | Use a full outcome map with a one-iteration committed horizon |
| One giant iteration | The agent cannot isolate progress, failure, recovery, or evidence | Bound one primary objective and verification decision |
| One tool call equals one iteration | Mechanical operations fragment useful state transitions | Define iterations by decision and evidence boundaries |
| Static next-action string | Cursor becomes stale after changes or parallel work | Recompute readiness from contracts, ledger, and actual state |
| Schedule “five iterations later” | Ordinals shift and parallel loops have no global N | Use semantic triggers, dependencies, deadlines, or dwell rules |
| Start every discovered subtask | Agenda explodes and scope drifts | Classify, trace to DoD, admit, defer, or reject explicitly |
| Never alter the initial plan | Counterexamples and changed state cannot be incorporated | Version and minimally repair the route |
| Replan from scratch after every observation | Valid work is lost and the controller thrashes | Preserve verified work and invalidate affected descendants |
| Child says done | Local success is mistaken for parent integration | Parent accepts exact child evidence and reruns integration |
| Shared TASKS.md as multi-writer truth | Lost updates and interleaving corrupt the cursor | Use transactional state with per-loop ownership |
| Unique filename only | Same-run writers still race | Add single-writer streams, CAS, leases, and fencing |
| Timestamp as ordering authority | Concurrent clocks do not express causality | Use per-stream revision and causal event IDs |
| Transcript as memory | Context trimming or handoff loses critical state | Regenerate a focus packet from durable contracts and ledger |
| Snapshot overwrites history | Audit and recovery branches disappear | Keep append-only events; snapshots remain derived |
| Replay all tool calls | Side effects duplicate after recovery | Replay recorded outcomes; new execution is a new attempt |
| Save while agents mutate shared state | Snapshot may be internally inconsistent | Checkpoint at controlled boundaries or transactionally |
| Ledger stores secrets and raw reasoning | Persistence expands exposure and noise | Store minimal structured facts, receipts, hashes, and references |
| Plan completion equals task completion | Route checkboxes substitute for outcome proof | Only the root DoD can authorize DONE |

## Loop Map Template

~~~markdown
## Loop Map — [workflow / loop]

- **Workflow ID / run ID / loop ID:** [...]
- **Focus Record / DoD / convergence versions:** [...]
- **Root outcome:** [...]
- **Workspace or environment revision:** [...]
- **Plan version:** [...]
- **Best verified checkpoint:** [...]
- **Global budget remaining:** [...]
- **Admission / budget:** [Admission hash; initial limit; current budget hash,
  revision, authenticated consumption records, and derived remaining units]
- **Routing cursor:** [Admission/proposal; chain/registry/authority hashes;
  status, profile index, active iteration, last event, cursor revision, and
  budget revision; or none]

### DoD Coverage

| Criterion | Current status | Fresh evidence | Remaining gap | Work nodes |
| --- | --- | --- | --- | --- |

### Task Network

| Work ID | Parent | Outcome / kind | Preconditions / trigger | Scope / owner | Local verifier | State |
| --- | --- | --- | --- | --- | --- | --- |

### Dependency Edges

| From | To | Type | Current support / threat |
| --- | --- | --- | --- |

### Current Control View

- **Active focus:** [...]
- **Ready set:** [...]
- **Waiting / wake-up conditions:** [...]
- **Blocked and exact unblockers:** [...]
- **Open children:** [...]
- **Ambiguous external effects:** [...]
- **Plan assumptions and threats:** [...]
~~~

## Current Iteration Contract Template

~~~markdown
## Current Iteration — [iteration ID]

- **Run / loop / ordinal / attempt:** [...]
- **Admission hash / budget revision:** [...]
- **Plan version / base revision / ownership epoch:** [...]
- **Routing profile / cursor revision:** [Active atomic profile and expected revision, or none]
- **Root DoD trace:** [...]
- **Parent outcome and integration target:** [...]
- **Primary focus:** [...]
- **Why now:** [...]
- **Hypothesis or expected information:** [...]

### Entry

- **Freshly verified preconditions:** [...]
- **Inputs and revisions:** [...]
- **Relevant latest failure / uncertainty:** [...]

### Boundary

- **Allowed mutation and tools:** [...]
- **Forbidden or preserved state:** [...]
- **Artifact / resource claim:** [...]
- **Time, cost, token, and risk budget:** [...]

### Proof and Exit

- **Expected observable result:** [...]
- **Local DoD and verifier:** [...]
- **Affected regressions / parent checks:** [...]
- **Verified exit:** [...]
- **Abort, pause, inconclusive, and handoff rules:** [...]
- **Commit payload:** [facts, receipts, evidence, new work, invalidations]
~~~

## Ledger Event Template

~~~yaml
event:
  schema_version:
  event_id:
  stream_id:
  expected_revision:
  recorded_revision:
  workflow_id:
  run_id:
  loop_id:
  iteration_id:
  attempt_id:
  ordinal:
  event_type:
  actor_id:
  owner_epoch:
  command_or_operation_id:
  causation_event_id:
  correlation_id:
  contract_versions:
  admission_hash:
  budget_revision:
  budget_consumption_ref:
  routing_proposal_ref:
  routing_chain_hash:
  routing_registry_hash:
  routing_authority_hash:
  routing_profile_index:
  routing_cursor_revision:
  plan_version:
  workspace_or_input_revision:
  recorded_at:
  observed_at:
  payload_or_artifact_reference:
  payload_hash:
  evidence_event_ids:
  decision_reason:
~~~

For terminal success, reference the exact admission, iteration commit, next
budget hash, accepted loop-scoped DoD hash/revision, fresh verifier events, and
artifact revision in an authenticated receipt. A terminal label without those
bindings is not a completion receipt.

## Research Basis

- [Receding Horizon Task and Motion Planning](https://arxiv.org/abs/2009.03139): plan over a future action window, execute only the first action, re-observe, and add newly discovered infeasibility predicates before replanning.
- [D* Lite](https://aaai.org/papers/00476-aaai02-072-d-lite/): incremental replanning reuses valid prior search effort instead of restarting similar planning problems.
- [HTN planning complexity and expressivity](https://aaai.org/papers/01123-aaai94-173-htn-planning-complexity-and-expressivity/): compound and primitive task decomposition, process constraints, and the need to bound recursive task networks.
- [A systematic approach to partial-order planning](https://cdn.aaai.org/AAAI/1991/AAAI91-099.pdf): causal support, open prerequisites, and threat resolution without unnecessary total ordering.
- [Planning landmarks](https://doi.org/10.1613/JAIR.1492): partially ordered facts that every valid solution must achieve provide global scaffolding without prescribing every low-level action.
- [The options framework](https://doi.org/10.1016/S0004-3702(99)00052-1): temporally extended actions defined by initiation conditions, a bounded policy, and termination conditions.
- [Principles of intention reconsideration](https://doi.org/10.1145/375735.376326): commitment to a plan should be reconsidered dynamically when the environment changes, rather than fixed only at design time.
- [Anytime Dynamic A*](https://auld.aaai.org/Papers/ICAPS/2005/ICAPS05-027.pdf) and [ARA*](https://papers.nips.cc/paper/2382-ara-anytime-a-with-provable-bounds-on-sub-optimality.pdf): retain a usable incumbent, improve it as budget permits, and reuse prior planning work.
- [Kubernetes controllers](https://kubernetes.io/docs/concepts/architecture/controller/): continuously reconcile observed state with desired state instead of trusting an open-loop script.
- [Airflow tasks and scheduler](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html): make dependencies explicit and schedule task instances only when their upstream conditions are satisfied.
- [LangGraph Pregel runtime](https://docs.langchain.com/oss/python/langgraph/pregel): each super-step plans eligible actors, executes selected work, publishes updates, and repeats.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence): checkpoint state, pending next tasks, lineage, interrupts, parallel writes, and recovery at step boundaries.
- [LangGraph subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs): give subgraphs isolated checkpoint namespaces and choose per-invocation, per-thread, or stateless persistence deliberately.
- [OpenHands conversation persistence](https://docs.openhands.dev/sdk/guides/convo-persistence): separate auto-saved base state from incrementally appended event history and restore by unique conversation ID.
- [OpenHands task tracker](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-tools/openhands/tools/task_tracker/definition.py): maintain visible task states and a single in-progress focus, while noting that prompt-only invariants still need runtime enforcement.
- [AutoGen Magentic-One orchestrator](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py): combine an outer facts-and-plan loop with an inner progress ledger and replan after repeated stalls.
- [SWE-agent trajectories](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/trajectories.md): persist action-observation trajectories and model-visible history separately so audit history survives context processing.
- [OpenAI Agents SDK RunState](https://openai.github.io/openai-agents-python/ref/run_state/): serialize the active agent, generated items, approvals, interruptions, usage, and current step for durable pause and resume.
- [ReAct](https://arxiv.org/abs/2210.03629): interleave reasoning, action, and environment observations so plans can be tracked and updated through execution.
- [Voyager](https://arxiv.org/abs/2305.16291): automatic curriculum, reusable skill memory, and iterative refinement from execution feedback and self-verification.
- [Reflexion](https://arxiv.org/abs/2303.11366): retain bounded evaluator-grounded episodic lessons across trials rather than rediscovering the same failure.
- [MemGPT](https://arxiv.org/abs/2310.08560): use explicit memory tiers and control flow instead of assuming the full long-horizon history remains in the active context window.
- [Temporal workflow history architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md): reconstruct workflow state from an ordered event history while using snapshots and fenced ownership for efficient durable execution.
- [Temporal Workflow ID policies](https://api-docs.temporal.io/): distinguish stable workflow identity from physical executions and prohibit two active executions with the same logical ID.
- [Microsoft event-sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing): immutable event history, derived projections, replay, audit, optimistic concurrency, and the complexity cost of the pattern.
- [SQLite isolation and WAL](https://www.sqlite.org/isolation.html): transactional local persistence with serialized writers; do not treat WAL as unrestricted multi-writer or network-filesystem coordination.
- [RFC 9562 UUIDs](https://www.rfc-editor.org/info/rfc9562/): UUIDv7 supplies standardized time-ordered identifiers with random bits for distributed uniqueness.
- [Lamport on event ordering](https://www.microsoft.com/en-us/research/publication/time-clocks-ordering-events-distributed-system/): concurrent events form a causal partial order; wall-clock timestamps alone do not establish happens-before.
- [The Chubby lock service](https://research.google.com/archive/chubby.html): coarse-grained distributed ownership requires reliable lock and lease semantics.
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/): distinguish persistent application state from disposable runtime coordination.
- [Python tempfile](https://docs.python.org/3/library/tempfile.html): create ephemeral directories with secure unique-name primitives when durability is not required.

Treat these as transferable mechanisms, not a requirement to build a full workflow platform for every task. Choose the lightest implementation that still preserves the task's authority, recovery, concurrency, evidence, and forgetting risks.
