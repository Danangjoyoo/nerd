# Behavioral Memory: Routing

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Behavioral Memory router](index.md) and load it only for its named trigger.

## Deterministic Routing Cursor

Compile a consumed remembered `routing` value as one ordered chain of atomic
profiles. Resolve every agent, skill, tool, and MCP identifier in every profile
before profile zero activates. Use the current authenticated registry,
authenticated `primary | modifier | middleware | controller` role and
incompatibility metadata, and explicit agent-bound authority map. Admit at most
one primary specialty per profile. Fail closed on a missing, renamed,
disallowed, incompatible, or ambiguous component; never drop, substitute,
reorder, install, or activate only a valid prefix.
A selected incompatible pair fails admission.

Bind the reducer cursor to the consumed proposal and immutable chain:

```text
routing.proposal_ref
routing.admission_hash
routing.status = PENDING | ACTIVE | COMPLETE | BLOCKED
routing.profile_index
routing.chain_size
routing.active_iteration_id
routing.revision
routing.budget_revision
routing.last_event
routing.chain_hash
routing.registry_hash
routing.authority_hash
```

Start with `ROUTING_BOUND` at pending/index zero/revision zero. Activation binds
the current index to one iteration. A committed failed attempt may repeat that
same index with a new iteration ID. Advance exactly one index only after an
authenticated completion receipt binds the admission, proposal, budget,
profile/index/hash, verified iteration/attempt, guard evidence, and hashed
identity of its exact `ITERATION_COMMITTED` event. The last satisfied profile
emits `ROUTING_COMPLETED`; registry or authority drift emits
`ROUTING_BLOCKED`. Route completion never proves the task DoD.

On recovery, use `loop.py routing` to validate schema, hashes, budget and cursor
revisions, chain bounds, status/active-iteration coherence, last event, and
reachable revision. `PENDING` and terminal cursors carry no active iteration;
`ACTIVE` carries exactly one; only `COMPLETE` points one past the chain. Resume
the committed index and reconcile any ambiguous effect before repeat or
advancement. S1 keeps the cursor in the session packet; S2/S3 persists each
cursor event with the durable protocol.
