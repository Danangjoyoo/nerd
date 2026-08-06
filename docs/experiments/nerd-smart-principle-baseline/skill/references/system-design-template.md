# System Design Template

## Use When

Use this template to define internal architecture, component responsibilities,
technical boundaries, and trade-offs. Use `spec-template.md` instead when the
artifact's main purpose is externally observable behavior and acceptance.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown` or explicit open questions; never invent
  constraints or decisions.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

```markdown
# [Required: System or Change Name] Design

## Context and Drivers

[Required: Describe the problem, current system, and forces shaping the design.]

## Goals and Non-goals

- **Goals:** [Required: List outcomes the design must enable.]
- **Non-goals:** [Required: List adjacent concerns intentionally excluded.]

## Constraints

- [Required: Record confirmed technical, operational, regulatory, or delivery
  constraints.]

## Architecture Overview

[Required: Explain the smallest architecture that satisfies the goals.]

## Components and Responsibilities

| Component | Responsibility | Dependencies |
| --- | --- | --- |
| [Required: Name] | [Required: Single responsibility] | [Optional: Direct dependencies] |

## Data and Control Flow

[Required: Describe the important request, event, or state transitions.]

## Interfaces and Persistence

- [Optional: Define APIs, messages, schemas, storage, and compatibility rules.]

## Failure and Recovery

- [Required: Describe material failure modes, detection, and recovery behavior.]

## Security and Privacy

- [Optional: Describe trust boundaries, authorization, sensitive data, and
  abuse controls.]

## Observability

- [Optional: Define signals needed to operate and verify the design.]

## Rollout and Migration

- [Optional: Define sequencing, compatibility, rollback, and data migration.]

## Alternatives and Trade-offs

| Direction | Benefit | Cost | Decision |
| --- | --- | --- | --- |
| [Required: Selected or rejected direction] | [Required: Main benefit] | [Required: Main cost] | [Required: Why] |

## Proof

- [Required: Map design claims to tests, measurements, or operational checks.]

## Open Questions

- [Optional: Record unresolved decisions that materially affect the design.]
```

## Completion Check

- Give every component one clear responsibility and explicit boundaries.
- Trace critical flows, failures, security concerns, and rollout implications.
- Explain why the selected design is simpler or better suited than alternatives.
- Stop at the Specify endpoint; do not turn the design into an implementation
  plan or edit.
