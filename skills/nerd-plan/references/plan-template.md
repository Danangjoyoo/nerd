# Implementation Plan Template

## Use When

Use this template to turn a confirmed outcome into ordered implementation work
with file-level changes and proof. Do not use it to discover requirements or to
record work already being executed.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown` or explicit blockers; never invent
  repository state or approvals.
- Prefer tables, then bullets, then short paragraphs.
- State each fact once. Do not restate task details in summaries, acceptance
  criteria, or self-review sections.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

````markdown
# [Required: Outcome Name] Implementation Plan

## Summary

| Item | Details |
| --- | --- |
| Outcome | [Required: complete observable result] |
| Approach | [Required: simplest sufficient design] |
| Scope | [Required: affected boundary and surfaces] |
| Proof | [Required: focused and regression evidence] |
| Deferred | [Optional: explicitly excluded work] |

[For multi-goal work only, add one row per Smart Goal Ledger ID with its
boundary, dependency, and status. Do not copy the full ledger.]

## Constraints and Non-goals

- [Record only constraints not already captured by the summary or tasks.]

## Tasks

| Task | Depends on | Produces |
| --- | --- | --- |
| T1 | None | [Concrete outcome consumed by later work] |
| T2 | T1 | [Concrete outcome] |

[Add critical path, waves, integration owner, or worktree strategy only when
they materially change execution.]

### Task [N]: [Component Name]

**Focus:** [One independently verifiable outcome. Use **Multi Goal Focus:** with
the Smart Goal ID only when needed.]

**Files:**

- Create: `exact/path/to/file.ts`
- Modify: `exact/path/to/existing.ts:123`
- Test: `tests/exact/path/to/file.spec.ts`

**Interfaces:**

- Consumes: `[Exact names, signatures, types, or artifacts from earlier tasks]`
- Produces: `[Exact names, signatures, types, or artifacts later tasks use]`

- [ ] **Step 1: Write the failing test**

```ts
it('describes the behavior', () => {
  expect(functionName(input)).toEqual(expected);
});
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `test command targeting this behavior`

Expected: FAIL with `[specific missing behavior or diagnostic]`.

- [ ] **Step 3: Implement the minimum change**

- [Concrete implementation action.]

- [ ] **Step 4: Run focused and regression proof**

Run: `focused test command`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add exact/path/to/file.ts tests/exact/path/to/file.spec.ts
git commit -m "type: concise outcome"
```

[For non-testable work, replace red/green steps with a baseline check, minimal
change, and post-change proof. Omit commit steps when commits are outside the
confirmed scope.]

## Final Validation

```bash
[Required: Fresh focused and repository-relevant commands]
```

## Acceptance Criteria

- [List only end-to-end conditions not already used as a task gate.]
````

## Completion Check

- Order tasks by dependency and make each task independently verifiable.
- Preserve Focus Record and Goal Ledger boundaries.
- Keep the dependency table compact; add critical path, waves, or serialized
  integration only when they affect execution.
- Use red-green-refactor for testable behavior and equivalent proof otherwise.
- Name exact files, interfaces, changes, proof, and stopping conditions without
  under-building the outcome.
- Preserve unrelated worktree changes and distinguish baseline failures.
- Require explicit authorization before any planned remote push.
- Self-review internally; do not add a visible self-review section.
- Stop before execution; the plan itself does not authorize edits.
