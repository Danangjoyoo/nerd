# Behavioral Memory in Task-Completion Loops

Use this reference only when the current user explicitly invokes Nerd Memory
for the current request. Installation, relevance, prior use, remembered
preferences, or another skill's mention never activates it. Without that
direct invocation, Nerd Loop remains memory-free and does not load or query
Nerd Memory. Once explicitly invoked, load Nerd Memory's own `SKILL.md` and
runtime contract before performing a memory operation; this reference defines
only the composition boundary.

Use [the Nerd Loop Runtime Contract](../runtime-contract.md) as the normative
source for authority precedence, selected state, and terminal behavior. This
reference owns remembered-routing composition. Nerd Memory's own runtime
contract remains authoritative for proposal, confirmation, consumption,
observation, and memory lifecycle.

## Routing Rule

Read only the matching chunk or smallest matching bundle. Do not preload siblings. If S2/S3 durability is involved, load `durable-runtime.md` from the parent references directory before any specialized ledger or recovery chunk.

| Chunk | Load when |
| --- | --- |
| [Admission](admission.md) | always after explicit activation; planes, safety, and fast paths |
| [Behavior contract](contract.md) | proposal acceptance or compiling the seven pattern types |
| [Operation](operation.md) | applying memory during an iteration or invalidating revisions |
| [Children](children.md) | nested or parallel work |
| [Learning](learning.md) | current user guidance may revise remembered behavior |
| [Durable recovery](durable-recovery.md) | ledger integration, resume, or ambiguous consumption |
| [Routing](routing.md) | an admitted multi-profile deterministic cursor |
| [Examples](examples.md) | a concrete composition example is needed |
| [Conformance](conformance.md) | failure diagnosis or integration completion checks |
