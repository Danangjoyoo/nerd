# Extended KISS Rationale

Nerd Plan defines KISS inline; routine planning work must not load this
reference. Use it only when the meaning of simplicity is disputed or a design
looks small locally while moving complexity elsewhere.

## Meaning

KISS means the simplest sufficient design, not the fewest changed lines, files,
checks, or minutes. A solution is not simple when it hides coupling, duplicates
a durable contract, shifts complexity to callers, or omits required failure and
compatibility behavior.

Prefer the clearest direct path with fewer concepts, dependencies, and new
boundaries when that path remains correct and maintainable. Do not add layers,
services, dependencies, generalized interfaces, configuration systems, or
extension points without an explicit requirement, established convention,
observed duplication, or concrete correctness, security, or measured
performance reason.

## YAGNI Is Included

Defer speculative features, options, backends, hooks, and abstractions. This is
part of KISS rather than a separately selected workflow. Deferral never removes
work required by the requested outcome, repository convention, or a correctness,
security, accessibility, data-integrity, or compatibility constraint.

## Whole-Path Simplicity

Judge simplicity across the affected path. Investigation, integration work,
migration, cleanup, and verification remain necessary when evidence requires
them. A focused check is sufficient only when it proves the requested result at
the risk of the change.

Optional nearby improvements stay deferred and may be reported. Restore a
deferred item when evidence makes it necessary; confirm first only when doing so
crosses the resolved Focus Record's authority boundary.
