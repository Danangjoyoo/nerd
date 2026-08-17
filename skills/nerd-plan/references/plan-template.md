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

## Context

- **Focus:** Intention: [outcome]; Expectation: Plan; Scope: [boundary]; Role: [when material].
- **Goal `[ID]`:** [Outcome]; scope: [boundary]; depends on: [IDs or None]; status: [Active or Queued].
- [Omit Goal bullets for single-goal work. Preserve Smart's IDs; keep one active.]

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

## Task Dependency Graph (TDG)

- **`T1`:** Depends on: [IDs or None]; owns: `[files/resources]`; gate: [proof]; enables: [IDs].
- **Critical path:** [Dependency chain.]
- **Waves:** [Ready independent IDs; dependent or overlapping IDs stay sequential.]
- **Mode:** [Parallel by TDG unless the user requires sequential work; explain exceptions.]
- **Integration owner:** [Required for parallel work.]

## Ordered Work

### [Required: Task ID] — [Required: Outcome-focused title]

- **Depends on:** [Task IDs or None.]
- **Execution:** [Batch, wave, or sequential; ownership and subagent if used.]
- **Files:** Create/modify `[exact paths]`.
- **Change:** [Exact behavior or contract.]
- **Red:** [Smallest failing test; otherwise baseline check and why TDD does not apply.]
- **Green:** [Minimal passing change.]
- **Refactor:** [Green-preserving cleanup or None.]
- **Verify:** [Focused command/result and regression proof.]

## Parallel Worktree and Integration Strategy

- [Omit unless independent TDG nodes mutate repository state.]
- **`T1`:** Worktree: `[path]`; branch: `[name]`; commit: [boundary]; push: [Authorized, Approval required, or None].
- Branch from one recorded base. Edit, test, and commit sequentially per worktree.
- Push only with explicit authority.
- Cherry-pick one branch at a time into the originating target, in TDG order.
- Validate each pick; resolve conflicts before continuing; run final proof.
- Never guarantee conflict-free or defect-free integration.

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
- Preserve Focus Record and Goal Ledger boundaries.
- Make TDG dependencies, critical path, parallel waves, and serialized integration explicit.
- Use red-green-refactor for testable behavior and equivalent proof otherwise.
- Name exact files, changes, proof, and stopping conditions without under-building the outcome.
- Preserve unrelated worktree changes and distinguish baseline failures.
- Require explicit authorization before any planned remote push.
- Stop before execution; the plan itself does not authorize edits.
