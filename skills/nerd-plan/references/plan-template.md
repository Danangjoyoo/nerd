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
- Give tables purposeful columns that answer the reader's next question. Do not
  use a one-column table or move narrative prose into cells.
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

| Type | Constraint |
| --- | --- |
| Preserve | `[Existing API, schema, behavior, or compatibility contract]` |
| Exclude | `[Explicit non-goal or deferred capability]` |
| Safety | `[Mutation, data, deployment, or authorization boundary]` |

[Omit rows already captured by the summary or a task.]

## Task Dependency Graph (TDG)

| Task | Wave | Depends on | Produces |
| --- | --- | --- | --- |
| T1 | 1 | None | Contract and failing tests |
| T2 | 2 | T1 | Runtime implementation |
| T3 | 2 | T1 | Documentation update |
| T4 | 3 | T2, T3 | Integrated proof |
| T5 | 4 | T4 | Delivery handoff |

```text
Wave 1            Wave 2 (parallel)       Wave 3              Wave 4
T1 Contract ------+--> T2 Runtime ----+
                  |                    +--> T4 Integration ---> T5 Delivery
                  +--> T3 Docs -------+
```

Legend: `-->` dependency; split branches run in parallel; joined branches wait
for every parent. Use plain ASCII and the same task IDs as the table. Omit the
diagram only for a single-task plan. Add critical-path, integration-owner, or
worktree notes only when they change execution.

## Ordered Work

### Task [N]: [Component Name]

**Focus:** [One independently verifiable outcome. Use **Multi Goal Focus:** with
the Smart Goal ID only when needed.]

**Files:**

| Action | Path |
| --- | --- |
| Create | `exact/path/to/file.ts` |
| Modify | `exact/path/to/existing.ts:123` |
| Test | `tests/exact/path/to/file.spec.ts` |

**Interfaces:**

| Direction | Contract |
| --- | --- |
| Consumes | `[Exact names, signatures, types, or artifacts from earlier tasks]` |
| Produces | `[Exact names, signatures, types, or artifacts later tasks use]` |

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

## Self Review

[Apply `nerd-review` to the completed plan. Use its Level 1–3 lenses and
evidence discipline; do not write praise, a walkthrough, or unsupported
confidence statements. Resolve findings before finalizing the validation
matrix; preserve genuine unknowns as blockers.]

| Checkpoint | Nerd Review lens | Evidence question | Status |
| --- | --- | --- | --- |
| Executability | Level 1 — concrete defects | Are every path, symbol, signature, command, dependency, and expected result exact and internally consistent? | Pass / Finding / Unknown |
| Repository fit | Level 2 — consistency and proof | Does each task follow repository rules and cover every changed contract with the right test or documentation proof? | Pass / Finding / Unknown |
| Architecture | Level 3 — harmful complexity | Does any task introduce avoidable coupling, unclear ownership, duplicated behavior, or speculative abstraction? | Pass / Finding / Unknown |
| Scope integrity | Adversarial evidence check | Is every task required by the outcome, and is every acceptance criterion owned and proven exactly once? | Pass / Finding / Unknown |

- **Findings:** `[None, or severity-ranked actionable findings with task IDs and correction direction.]`
- **Unknowns:** `[None, or evidence gaps that an implementer must resolve before execution.]`

## Final Validation

| Check | Command | Expected |
| --- | --- | --- |
| Focused behavior | `[Exact focused test command]` | PASS |
| Regression | `[Exact affected-suite command]` | PASS |
| Repository quality | `[Typecheck, lint, build, or equivalent command]` | Exit 0 |
| Diff hygiene | `git diff --check` | No output |

[Keep only relevant rows. Put conditional setup or environment requirements in
one bullet below the table.]

## Acceptance Criteria

| ID | Criterion | Evidence |
| --- | --- | --- |
| AC1 | `[Observable end-to-end behavior]` | `[Test, command, artifact, or inspection]` |
| AC2 | `[Compatibility or safety invariant]` | `[Regression proof]` |

[List only end-to-end conditions not already used as task gates.]
````

## Completion Check

| Concern | Requirement |
| --- | --- |
| Ordering | Tasks follow dependencies and remain independently verifiable. |
| Boundaries | Focus Record and Goal Ledger scopes remain separate. |
| Dependencies | Critical path, waves, or serialized integration appear only when they affect execution. |
| Proof | Testable behavior uses red-green-refactor; other work has equivalent baseline and post-change proof. |
| Precision | Tasks name exact files, interfaces, changes, commands, expected results, and stopping conditions. |
| Safety | The plan preserves unrelated changes and distinguishes baseline failures. |
| Authority | Require explicit authorization before any planned remote push or external write. |
| Brevity | Facts appear once; optional sections and narration are absent. |
| Self review | The plan applies Nerd Review Levels 1–3 and records evidence-backed status, findings, and unknowns. |
| Stop | Planning ends before execution; the plan does not authorize implementation. |
