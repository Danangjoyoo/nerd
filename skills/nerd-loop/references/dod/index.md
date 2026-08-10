# Defining a Good Definition of Done

Use [the Nerd Loop Runtime Contract](../runtime-contract.md) as the normative
source for authority precedence, criterion states, transition priority, and
terminal outcomes. This reference supplies construction and evidence
techniques; it does not redefine runtime state.

## Routing Rule

Read only the matching chunk or smallest matching bundle. Do not preload siblings. If S2/S3 durability is involved, load `durable-runtime.md` from the parent references directory before any specialized ledger or recovery chunk.

| Chunk | Load when |
| --- | --- |
| [Foundation](foundation.md) | goal/DoD distinctions, authority, or quality layers |
| [Construction](construction.md) | drafting or reviewing atomic, traceable criteria |
| [Evidence](evidence.md) | choosing credible verifiers or a risk-specific proof portfolio |
| [Task guidance](task-guidance.md) | task recipes or diagnosing weak/gameable criteria |
| [Template](template.md) | emitting a DoD record or running the final challenge |
| [Research](research.md) | rationale or citations are explicitly needed |
