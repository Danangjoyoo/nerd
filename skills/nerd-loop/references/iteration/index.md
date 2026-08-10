# Iteration Control in Task-Completion Loops

Use [the Nerd Loop Runtime Contract](../runtime-contract.md) as the normative
source for authority, state classes, closed status vocabularies, transition
priority, effect ordering, and terminal outcomes. This reference supplies the
full planning, scheduling, persistence, and recovery techniques routed mainly
to S2/S3. D0 has no iteration state; ordinary S1 compresses these concepts into
one current-focus and evidence packet rather than creating durable artifacts.

## Routing Rule

Read only the matching chunk or smallest matching bundle. Do not preload siblings. If S2/S3 durability is involved, load `durable-runtime.md` from the parent references directory before any specialized ledger or recovery chunk.

| Chunk | Load when |
| --- | --- |
| [Core model](core.md) | iteration boundaries or synchronized views |
| [Planning](planning.md) | task networks, readiness, decomposition, or horizon |
| [Scheduling](scheduling.md) | next focus, defer/delegate/parallel, or discovered work |
| [Ledger](ledger.md) | custom event or commit design beyond the durable core |
| [Recovery](recovery.md) | placement, IDs, races, snapshots, resume, or reconciliation |
| [Continuity](continuity.md) | focus loss, forgetting, or iteration anti-patterns |
| [Templates](templates.md) | materializing Loop Map, current iteration, or ledger records |
| [Research](research.md) | rationale or citations are explicitly needed |
