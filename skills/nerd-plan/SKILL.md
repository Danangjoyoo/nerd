---
name: nerd-plan
description: Use when turning a confirmed outcome into actionable, ordered implementation steps with file-level changes and proof, then stopping before execution.
---

# Nerd Plan

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

<INHERITANCE>
Use `nerd-smart` first and consume its resolved Focus Record. This route accepts
only the **Plan** endpoint. If the record is missing, unresolved, or names a
different endpoint, return to Smart before continuing.
</INHERITANCE>

## Delivery

- **KISS:** Plan simplest sufficient design. Defer speculative features,
  options, and abstractions.
- **Comprehensive:** Load [guidance](references/comprehensive.md) only for
  module/service boundaries, durable contracts/data shapes, or inconsistent
  partial delivery.
- **DRY:** Load [guidance](references/dry.md) only for 3+ maintained behavior
  copies or 2 contract copies across a boundary.
- **Selection:** If ambiguous, read the
  [selection reference](references/principle-selection.md).
- **Rationale:** Read extended [KISS](references/kiss.md) or legacy
  [YAGNI](references/yagni.md) only when disputed.

## Plan

Read the [implementation plan template](references/plan-template.md). Produce
ordered, independently verifiable tasks with exact files, changes, proof, and
stopping conditions. Preserve confirmed inputs, mark material unknowns, and
self-review once for completeness and simplicity.

## Planning Discipline

| Discipline | Rule |
| --- | --- |
| **Context** | Copy the Focus Record. For multiple goals, preserve Goal Ledger IDs, boundaries, dependencies, and one active goal. Never merge goals or proof. |
| **TDD** | Testable work: red, green, refactor, focused proof, regression proof. Other work: baseline check, minimal change, post-change proof. |
| **Task Dependency Graph (TDG)** | Give each task an ID, dependencies, ownership, gate, and dependents. Mark critical path and execution waves. Keep only dependent work sequential. |
| **Speed** | Unless the user requires sequential work, batch known operations and parallelize independent TDG nodes when net faster. Subagents need disjoint ownership, environment support, and one integration owner. Keep adaptive work sequential. |
| **Worktrees** | For parallel mutations, use one worktree and branch per node. Edit and commit sequentially inside each. Push only with explicit authority. Cherry-pick into the originating target one branch at a time in TDG order; validate each pick, resolve conflicts, then run final proof. Isolation lowers risk; it cannot guarantee conflict-free or correct integration. |
| **Boundary** | Plan batching, delegation, worktrees, commits, pushes, and cherry-picks. Do not execute them. |

## Persistence

- Always save Markdown.
- Smart route: runtime temp directory such as `/tmp`; fallback `~/.agent/tmp/`.
- Direct user invocation: `./docs/plans/` in the current repository.
- Direct stays direct after Smart resolves Focus.
- Create the directory; use a descriptive, collision-resistant filename; show
  the path.

Stop before execution. The plan does not authorize its implementation; require
an Execute endpoint through Smart.
