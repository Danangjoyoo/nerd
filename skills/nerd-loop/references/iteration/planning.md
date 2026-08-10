# Iteration Control: Planning

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

## Contents

- [Representing the Whole Plan](#representing-the-whole-plan)
- [Readiness](#readiness)
- [Bounded decomposition](#bounded-decomposition)
- [Iteration Sequence](#iteration-sequence)
- [Before the first iteration](#before-the-first-iteration)
- [At every iteration boundary](#at-every-iteration-boundary)
- [Horizon policy](#horizon-policy)

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
