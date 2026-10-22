# Product Review Collaboration

Use for an existing product proposal, PRD, feature, flow, prototype, or release
scope. Judge it against the accepted user problem and constraints. Do not turn
review into discovery research or selection of a new product direction.

## Companion Sequence

| Step | Skill | Bounded task | Return to Review |
| --- | --- | --- | --- |
| Establish intended behavior | `nerd-document` | Locate accepted problem, user, scope, requirements, and success criteria | Sourced decisions and unresolved facts |
| Challenge the proposal | `nerd-brainstorm` | Examine one assumption or trade-off against those goals | Counterexample, affected user, alternative explanation, evidence needed |
| Trace the artifact | Review | Follow the supplied flow/prototype or requirement through its outcome | Specific mismatch and consequence |
| Check decision clarity | `nerd-document` | Compare requirement, flow, acceptance, and status statements | Contradictions or unsupported readiness/approval claims |

Read nerd-document's PRD guide and, when relevant, its decision-record guide.
Use nerd-brainstorm's Review Support mode to compare trade-offs; do not run an
Ideate convergence process or request acceptance of a replacement direction.
Use supplied research and observations as evidence; label untested assumptions.

## Review Lenses

| Level | Check | Finding evidence |
| --- | --- | --- |
| 1 | Flow consistency, rule contradictions, reachable dead ends | A named user/input cannot complete the stated task or gets contradictory behavior |
| 2 | Scope, user needs, observable acceptance, success measurement | An accepted requirement is unmet or a claimed outcome cannot be established |
| 3 | Value, incentives, dependencies, lifecycle, material trade-offs | A design choice undermines the accepted problem/outcome under supported conditions |

Follow the primary task and risk-relevant permission, empty, error, cancellation,
and recovery paths. Include them only when the artifact and goals make them
relevant. Separate proposed behavior from implemented behavior and a measurement
plan from observed results. A prototype's absent backend is not a defect unless
functional behavior is in scope or its claims depend on that backend.

## Proof and Completion

A retry flow that can duplicate a paid action may be a finding when the behavior
and trigger are supported. “Users will prefer a wizard” is a preference without
evidence. Missing research limits confidence; it does not prove poor demand.
Identify a concrete contradiction or unsupported material product claim before
assigning severity. Review may recommend a correction outcome, but must not
invent metrics, redesign the feature, approve a release, or write a new PRD.
