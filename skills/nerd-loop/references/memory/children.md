# Behavioral Memory: Children

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Behavioral Memory router](index.md) and load it only for its named trigger.

## Nested and Parallel Work

Use one `episode_id` for one independent root task. Iterations, retries, and
internal child loops are not independent evidence roots and must not inflate
support.

An internal child may inherit the parent's Behavior Contract without a new
memory operation when all of these hold:

- it exists only to satisfy the same root endpoint;
- its scope and authority are a strict subset of the parent;
- its inputs, deliverable, DoD, and integration rule are fully specified by the
  parent contract; and
- it introduces no new memory-derived field.

Give the child its own Current Iteration Contract, DoD, ledger stream, owner,
budget, and mutation scope, but retain the root memory episode reference.

Create a separate episode and proposal when work has an independently
completable goal or endpoint, when the user could accept or reject it
separately, or when the child needs memory to supply a new material field. One
goal's memory confirmation never confirms another independent goal.

Designate one parent or coordinator as the memory-transition owner. Parallel
agents may return possible direct-user observations or detected conflicts, but
they must not independently confirm, consume, deny, promote, split, or forget
the same memory state. Serialize those transitions through the deterministic
runtime and committed parent ledger.
