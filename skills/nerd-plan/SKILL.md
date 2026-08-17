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
self-review the finished artifact with `nerd-review` checkpoints before saving.

## Writing

- Prefer **tables**, then **bullets**, then short **paragraphs**. Use tables for
  repeated records, mappings, comparisons, dependencies, commands, and gates;
  use bullets for exceptions or short sequences.
- State each fact once. Merge overlapping outcome, input, constraint, proof,
  and acceptance material instead of restating it in multiple sections.
- Keep the dependency table structural; keep implementation detail inside its
  owning task.
- Omit narration, repeated rationale, and empty or non-applicable sections.
- Keep the visible Self Review evidence-based: apply Nerd Review Levels 1–3 to
  executability, repository consistency, and harmful complexity. Record only
  passed checkpoints, material findings, and unresolved evidence gaps.
- Optimize for the implementer who sees one task: give that task exact files,
  interfaces, steps, commands, and expected results.

## Planning Discipline

| Discipline | Rule |
| --- | --- |
| **Context** | Copy the Focus Record. For multiple goals, preserve Goal Ledger IDs, boundaries, dependencies, and one active goal. Never merge goals or proof. |
| **TDD** | Testable work: red, green, refactor, focused proof, regression proof. Other work: baseline check, minimal change, post-change proof. |
| **Task Dependency Graph (TDG)** | Use one compact table with task ID, dependency, and produced outcome. Add critical path or waves only when they change execution. Do not repeat the table inside tasks. |
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
