# Iteration Control: Ledger

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

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
