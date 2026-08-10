# Cost-Proportional Loop Profiles and Route Mapping

Use this reference to decide whether a task needs Nerd Loop and, if so, the
cheapest control profile and route capable of reaching its Definition of Done
(DoD). Profile selection reduces orchestration cost; it never weakens the
endpoint, authority, DoD, or required proof.

Use [the Nerd Loop Runtime Contract](../runtime-contract.md) as the normative
source for hard-floor precedence, state capability requirements, status
vocabularies, budgets, and terminal decisions. This reference owns route
selection and examples, not an alternative state machine.

## Routing Rule

Read only the matching chunk or smallest matching bundle. Do not preload siblings. If S2/S3 durability is involved, load `durable-runtime.md` from the parent references directory before any specialized ledger or recovery chunk.

| Chunk | Load when |
| --- | --- |
| [Selection](selection.md) | value gate, signals, hard floors, or routing record |
| [Catalog](catalog.md) | comparing D0 through L4 |
| [Persistence](persistence.md) | choosing S0 through S3 |
| [Endpoint map](endpoint-map.md) | mapping a Nerd Smart endpoint |
| [Route templates](routes.md) | choosing or inspecting a route sequence |
| [Lifecycle](lifecycle.md) | escalation, de-escalation, or orchestration cost |
| [Composition](composition.md) | specialty/memory composition or routing failures |
| [Examples](examples.md) | worked routing decisions or router conformance |
