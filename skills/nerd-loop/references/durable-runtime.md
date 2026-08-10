# Durable Runtime for S2 and S3

Load this extension only after `loop.py route` admits `S2` or `S3`, including a
lower-profile route raised by `durable_checkpoint_only`. Read the
[Core Runtime Contract](runtime-contract.md) first. This extension adds durable
mechanics; it cannot redefine core authority, DoD completion, budget identity,
transition priority, or terminal meaning.

## Contents

1. [Host Capability Floor](#host-capability-floor)
2. [Durable Admission](#durable-admission)
3. [Two-Phase Effect Protocol](#two-phase-effect-protocol)
4. [Unknown Effects and Recovery](#unknown-effects-and-recovery)
5. [Durable Wait and Resume](#durable-wait-and-resume)
6. [Children and Handoffs](#children-and-handoffs)
7. [Identity and Rollover](#identity-and-rollover)
8. [Adapter Conformance](#adapter-conformance)

## Host Capability Floor

Use host-provided private state before creating any repository or external
artifact. A unique path prevents naming collision but is not locking,
authentication, atomicity, or fencing.

| State | Required trusted-host capability | If unavailable |
| --- | --- | --- |
| `S2` | Authorized durable single-writer storage, schema/version checks, stable IDs, idempotency, atomic append or compare-and-set, and resume lookup | `BLOCKED` or accepted `HANDOFF` |
| `S3` | Every S2 capability plus transactional expected-revision append, authenticated ownership claims, affected-resource fencing, and effect reconciliation | `BLOCKED` or accepted `HANDOFF` |

Require authenticated wake-event registration for a durable `monitor` or
`pr_delivery` route. Require effect reconciliation for `pr_delivery`, external
receipts, staged rollout, or any effect whose acknowledgement can be ambiguous.
Do not claim that a prose ledger, ordinary shared file, model-generated token,
or reducer output supplies these capabilities.

The host adapter authenticates capability, registry, authority, evidence,
approval, wake, ownership, receipt, and fence inputs against the actual
platform. `loop.py` verifies their structure and bindings only.

## Durable Admission

Persist the exact reducer-produced admission envelope and cumulative
`budget_state` as one identity. Record the workflow, run, loop, contract, DoD,
artifact, plan/base, and ledger revisions needed by the selected route. Bind
the complete trusted host-capability set and state-class requirements before
the first durable selection.

For S2, enforce one writer for the loop stream. For S3, enforce expected
revisions, ownership epoch, and the affected resource's current fence in both
the ledger and the resource operation. A database transaction that protects
only the ledger is insufficient when the external resource ignores the fence.

Reject reconstructed or downgraded admission, stale budget state, a changed
DoD hash, missing capability, stale owner, duplicate sorted-set member, unknown
schema field, or noncanonical identity before performing an effect.

## Two-Phase Effect Protocol

Commit intent before every durable effect and outcome after it. Use the
reducer's `effect` command to validate the exact event sequence.

1. **Intent commit:** Atomically append one complete `INTENT_COMMITTED` event.
   Bind event, commit, iteration, attempt, focus, owner, epoch, resource,
   operation, idempotency, admission, budget, contract, DoD, artifact,
   verifier, expected-result, abort-rule, and expected-revision identities.
   For S3 also bind the trusted fence token. The event must freeze the exact
   accepted DoD definition and mandatory criterion/integration sets. If a
   remembered route is active, bind its exact proposal, chain, and profile.
2. **Execute:** Perform the authorized action outside the ledger transaction,
   using the committed operation/idempotency identity and current resource
   fence. Never execute an uncommitted durable or external intent.
3. **Outcome observation:** Append exactly one `ACTION_OBSERVED` record carrying
   an applied receipt, failure, or `OUTCOME_UNKNOWN`, bound to the same
   iteration, attempt, operation, idempotency key, expected revision, owner,
   and fence. Include observed costs, invalidations, discoveries, best-state
   effect, and ownership disposition.
4. **Verification:** Append `VERIFICATION_RECORDED` with complete authenticated
   criterion and integration evidence. Its DoD hash/revision and artifact
   revision must exactly match the intent, and its displayed statuses and
   completion verdict must be derived from those evidence records.
5. **Iteration commit:** Append `ITERATION_COMMITTED` referencing the resolved
   observation and verification. Consume exactly one authenticated budget unit
   and retain the reducer-produced next budget state and hashed commit identity.
   Accept `VERIFIED` only when an applied receipt exists and the bound
   iteration-scoped DoD passes.
6. **Edge:** Append exactly one cause-labelled successor, authenticated pause,
   accepted handoff, `LOOP_DONE`, or `LOOP_TERMINATED` after the iteration
   commit. A passing loop-scoped DoD must choose `LOOP_DONE`; every non-success
   terminal requires its typed receipt.

Never require a receipt before its action. Every event carries the next
expected revision. An exact duplicate event ID with byte-equivalent canonical
payload is idempotent; the same ID with different content, a stale revision,
changed owner/fence, mismatched receipt, or edge before commit is invalid.

## Unknown Effects and Recovery

When acknowledgement is ambiguous, keep the same iteration, attempt,
operation, idempotency key, owner, and fence. Reconcile against the affected
system before retrying. Do not mint a new attempt for a possibly completed
non-idempotent effect.

- `NOT_APPLIED` permits retry under the committed identities.
- `APPLIED` becomes the resolved observation and proceeds to verification.
- `FAILED` becomes the resolved failure observation.
- Still-unknown state keeps the loop in reconciliation or reaches an honest
  non-success result; it never becomes success.

On recovery, validate admission and budget hashes, schema, every expected
revision, owner/fence, in-flight intent, observation, verification, and edge.
Resume at reconciliation, not directly at active execution. Optional context
condensation may occur only after the committed edge.

Keep the latest state distinct from the best verified checkpoint. A rollback
or recovery action is a new authorized iteration with its own evidence; do not
rewrite committed history.

## Durable Wait and Resume

Enter `PAUSED` only after atomically registering an authenticated wake
condition and deadline supported by the admitted host. Mark work nodes
`WAITING`; waiting consumes no active iteration budget. Never busy-poll or
claim a resumable pause from session text alone.

A wake event enters `RECONCILING`. Recheck authority, cancellation, contract
and artifact revisions, ownership, budget, external facts, and evidence
freshness before deriving ready work. An expired deadline follows the core
transition priority and cannot silently extend the budget or DoD.

## Children and Handoffs

A genuine child has a narrower endpoint, its own DoD, budget, owner, state,
artifact/input revision, and terminal receipt. It never writes the parent
stream directly. Accept child completion only after validating its exact
contract, evidence references, and parent integration rule. Parent `DONE`
still requires the parent DoD.

A handoff packet contains schema and contract versions, workflow/run/loop
identities, endpoint, DoD, current and best verified revisions, criterion
vector, committed and ambiguous effects, budget state, ready/waiting/blocked
work, and exact resume rule. Give it a canonical reference, integer revision,
and content hash. `HANDOFF` is valid only when an authenticated record says
`ACCEPTED`, names the recipient, and binds that exact reference, revision, and
hash. Packet presence is not acceptance or success.

## Identity and Rollover

Use opaque unique workflow, run, loop, iteration, attempt, commit, and event IDs.
A workflow may span physical runs. Resume the same run only from exact
compatible committed state. After terminal closure, incompatible runtime
upgrade, or explicit continuation rollover, start a new run and link it to the
predecessor with a committed continuation event. Never recover by choosing the
newest directory.

Identity-bearing strings are canonical and nonempty. Reject whitespace-only or
leading/trailing whitespace rather than trimming it. Sorted-set fields reject
duplicates so hashes and replay checks remain unambiguous.

## Adapter Conformance

Reducer unit tests are necessary but do not prove durable-host conformance. A
conforming adapter must integration-test atomic append/compare-and-set, crash
recovery at every protocol boundary, idempotent duplicate delivery, ambiguous
effect reconciliation, authenticated wake/resume, real ownership enforcement,
and affected-resource fencing. It must also prove that stale admission, budget,
revision, owner, receipt, or fence inputs fail before an effect.

Without those platform-backed tests and capabilities, fail S2/S3 admission
closed as `BLOCKED` or use an explicitly accepted `HANDOFF`; never downgrade
while the hard floor remains.
