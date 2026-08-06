# Implementation Plan Template

## Use When

Use this template to turn a confirmed outcome into ordered implementation work
with file-level changes and proof. Do not use it to discover requirements or to
record work already being executed.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown` or explicit blockers; never invent
  repository state or approvals.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

````markdown
# [Required: Outcome Name] Implementation Plan

## Outcome

[Required: State the complete observable result this plan will produce.]

## Confirmed Inputs

- [Required: Record approved requirements, decisions, and source artifacts.]

## Delivery Breakdown

- **Approach:** [Required: KISS plus any evidence-selected Comprehensive or DRY companion.]
- **Required outcome:** [Required: Requested behavior or artifact.]
- **Simplest sufficient design:** [Required: Direct design with no accidental complexity.]
- **Required surfaces:** [Required: Supporting work needed for correctness or integration.]
- **Proof:** [Required: Evidence suited to behavior and risk.]
- **Deferred:** [Required: Optional or speculative work intentionally excluded.]

## Constraints and Non-goals

- [Required: Record repository, compatibility, safety, and scope constraints.]

## Worktree and Baseline

- [Optional: Record existing changes and pre-implementation check results.]

## Ordered Work

### Task [Required: Number]: [Required: Outcome-focused title]

**Files:**

- Create: `[Optional: path]`
- Modify: `[Required: path]`

**Change:**

- [Required: Describe the exact behavior or contract to implement.]

**Proof:**

- [Required: Give the command or inspection suited to the affected behavior and risk, plus its expected result.]

## Final Validation

```bash
[Required: Fresh focused and repository-relevant commands]
```

## Acceptance Criteria

- [Required: List observable completion conditions.]

## Self-Review

- **Completeness:** [Required: Confirm every approved outcome is covered.]
- **Simplicity:** [Required: Confirm speculative work is excluded.]
- **Risks:** [Optional: Record remaining material risks or blockers.]
````

## Completion Check

- Order tasks by dependency and make each task independently verifiable.
- Name exact files, changes, proof, and stopping conditions without under-building the outcome.
- Preserve unrelated worktree changes and distinguish baseline failures.
- Stop before execution; the plan itself does not authorize edits.
