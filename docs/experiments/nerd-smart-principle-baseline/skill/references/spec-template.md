# Behavior Specification Template

## Use When

Use this template to define externally observable requirements, behavior, and
acceptance criteria. Use `system-design-template.md` instead when the artifact's
main purpose is to define internal architecture or technical boundaries.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown` or explicit open questions; never invent
  requirements or decisions.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

```markdown
# [Required: Outcome Name] Specification

## Summary

[Required: State the intended outcome and who benefits in one short paragraph.]

## Problem

[Required: Describe the current problem, evidence, and why it matters.]

## Goals

- [Required: List observable outcomes.]

## Non-goals

- [Required: State nearby outcomes intentionally excluded.]

## Users and Stakeholders

- [Optional: Identify affected users, operators, or decision-makers.]

## Functional Requirements

1. [Required: State each behavior as a testable requirement.]

## Quality Requirements

- [Optional: State measurable reliability, performance, accessibility,
  compatibility, privacy, or security constraints.]

## Behavior and Edge Cases

- [Required: Describe the normal flow.]
- [Optional: Describe boundary conditions, invalid input, and failure behavior.]

## Interfaces and Data

- [Optional: Define externally visible inputs, outputs, states, and data rules.]

## Constraints and Dependencies

- [Optional: Record confirmed limits and dependencies.]

## Acceptance Criteria

- [Required: Map every goal to observable proof.]

## Open Questions

- [Optional: Record only unresolved decisions that materially affect the
  specification.]
```

## Completion Check

- Make every requirement observable or testable.
- Keep internal architecture out unless it changes the external contract.
- Cover relevant failures, constraints, and acceptance proof.
- Stop at the Specify endpoint; do not plan or implement the outcome.
