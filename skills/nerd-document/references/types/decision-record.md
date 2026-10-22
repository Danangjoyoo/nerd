# Decision Record (ADR or General Decision)

## Purpose and Boundary

Preserve one consequential decision, the context that made it necessary, the
alternatives considered, and the resulting trade-offs. An architecture decision
record (ADR) uses the same structure for a technical choice. Document the real
decision status: proposed is different from accepted or superseded.

## Suggested Structure

- **Title and identity:** Stable decision ID, descriptive title, date if known.
- **Status:** Proposed, accepted, rejected, or superseded; link a replacement.
- **Context:** The problem, constraints, and evidence that drove the decision.
- **Decision:** A direct statement of the selected choice and its boundary.
- **Alternatives:** Credible options actually considered, with relevant criteria.
- **Consequences:** Benefits, accepted costs, and follow-up implications.
- **Revisit conditions:** Established triggers for reconsideration, when useful.

Keep the decision easy to find. Use a small comparison table when readers need
to inspect the reasoning across alternatives. Avoid rewriting the entire design
or making a speculative list of every possible technology.

## Filled Example

Fictional accepted decision:

```markdown
# ADR-007 — Generate Exports in a Worker

Status: Accepted

## Context

Export generation can outlast the API request window. The system already has a
worker service, and users need a job status while the file is generated.

## Decision

The API will record an export job and return its identity. The existing worker
will generate the CSV and update the job state. The API will not generate the
entire file within the initiating request.

## Alternatives Considered

| Option | Benefit | Cost / limitation |
| --- | --- | --- |
| Generate within the request | Fewer asynchronous states | Conflicts with the accepted request-window constraint |
| Use the existing worker | Fits current operation and exposes job progress | Requires job-state and failure handling |

## Consequences

- Users can check progress after the initial request returns.
- The implementation must define failed-job behavior and observability.
- Request retry and worker retry contracts remain unresolved; this decision
  does not imply that retries are safe.

## Related Records

Link the accepted request-window constraint and technical design.
```

Replace evidence prompts with actual source links in a real record. Do not mark
the choice accepted merely because it appears preferable in the example.

## Revision Example

If a later accepted decision replaces the worker architecture:

1. Preserve ADR-007's original context and decision.
2. Change its status to `Superseded by ADR-012` with a real relative or native link.
3. Record the new context and selected replacement in ADR-012.

Do not erase the original rationale and leave the old decision ID attached to a
different choice. Preserve organizational history when it is part of the request.

## Writing Corrections

| Weak statement | Better statement |
| --- | --- |
| This is the best architecture | Name the constraint and accepted trade-off |
| Everyone agreed | Record the actual decision status and evidence |
| Add retries later | State the unresolved retry contract and affected behavior |
| We considered many options | Name the credible options actually evaluated |

## Completion Check

Check that one decision is stated clearly; status and sources are accurate;
alternatives share meaningful comparison criteria; costs are not hidden; and
unknowns are separate from accepted consequences. Writing a record does not
authorize implementing the decision.
