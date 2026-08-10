# Behavioral Memory: Operation

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Behavioral Memory router](index.md) and load it only for its named trigger.

## Using Memory During Iteration

Do not retrieve Nerd Memory on every iteration. After admission, use the frozen
Behavior Contract and the profile's selected S1–S3 execution state. Do not
create a Loop Map or ledger merely to carry memory into D0–L2 work.

At each boundary:

1. load the current Loop/Behavior Contract revision;
2. for S2/S3, replay committed execution events after the checkpoint;
3. reconcile actual workspace, verifier, user, and relevant child state;
4. inject only relevant behavior into the compact S1 packet or Current
   Iteration Contract;
5. select and execute inside the effective action and boundary fields, using
   the committed routing cursor's active profile when one exists;
6. verify with the effective verification policy and current DoD; and
7. record evidence in S1 or commit it in S2/S3 before selecting the next cycle.

The iteration packet should reference the Behavior Contract revision rather
than restating historical memories. Include only the relevant rules, their
source tags, and any current override.

The following normally stay within one consumed contract and require no new
memory proposal:

- selecting the next dependency-ready iteration;
- retrying an idempotent verifier;
- changing a failed causal strategy within the accepted action policy;
- admitting a mandatory repair or evidence probe inside the existing endpoint;
- crash recovery from committed facts;
- resuming after context condensation; and
- completing a bounded internal child task fully specified by the parent.

These cases may still require ordinary platform or action approval. “No new
memory proposal” does not mean “unconditionally authorized.”
## Revision and Invalidation

Rebuild the memory-blind baseline when a material field changes. A material
change includes the goal, task endpoint, action policy, result shape, boundary,
verification contract, ordered routing chain, stable applicability scope, or
independent root task.

Use this decision rule:

- If the user explicitly supplies the changed field, use it directly and
  record its source as `current_explicit`; memory may not override it.
- If the changed field remains absent and memory could fill it, create a fresh
  proposal and require a fresh confirmation before using the remembered value.
- If the change is only execution state inside the accepted contract, update
  the Loop Map or ledger without querying memory.

On direct correction:

1. stop before another affected mutation;
2. version the Loop/Behavior Contract;
3. mark contradicted confirmed patterns contested through Nerd Memory;
4. invalidate uncommitted decisions and stale evidence derived from the old
   field;
5. preserve independent verified evidence; and
6. replan from the corrected contract.

A task-local difference is not automatically a durable correction. Record
`user_correction` only when the user explicitly changes or retracts recurring
guidance.

If a linked pattern is forgotten, superseded, or contested during a live task,
never use it to form new uncommitted behavior. Preserve completed execution
facts, rebaseline affected future work, and ask only when the user's desired
current-task behavior is genuinely ambiguous.

Do not re-query or re-consume merely because an iteration restarted, a model
context was condensed, or the process crashed. Recovery uses the committed
effective contract.
