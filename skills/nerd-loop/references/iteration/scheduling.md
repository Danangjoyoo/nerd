# Iteration Control: Scheduling

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

## Contents

- [Finding the Next Iteration](#finding-the-next-iteration)
- [Lookup and reconciliation order](#lookup-and-reconciliation-order)
- [Selection priority](#selection-priority)
- [Next action versus next iteration](#next-action-versus-next-iteration)
- [Scheduling Subtasks](#scheduling-subtasks)
- [Inline action or child loop](#inline-action-or-child-loop)
- [Execute now](#execute-now)
- [Defer until a condition](#defer-until-a-condition)
- [Avoid “N iterations later”](#avoid-n-iterations-later)
- [Parallel execution](#parallel-execution)
- [Initiative When the Plan Is Insufficient](#initiative-when-the-plan-is-insufficient)
- [Discovery record](#discovery-record)
- [Admission classes](#admission-classes)
- [Plan revision](#plan-revision)

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
