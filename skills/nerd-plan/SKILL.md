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

## Inheritance

Use `nerd-smart` first and consume its resolved Focus Record. This route accepts
only the **Plan** endpoint. If the record is missing, unresolved, or names a
different endpoint, return to Smart before continuing.

## Prerequisites

Plan from confirmed inputs. When a required input is missing, route through
`nerd-smart`, bring the result back, and resume **Plan** through `nerd-smart`:

- `nerd-brainstorm` owns material design choices through **Ideate**. Bring back
  the selected direction, trade-off, constraints, and choice-changing unknowns.
- `nerd-explore` owns repository evidence through **Explore**. Bring back exact
  paths, symbols, interfaces, commands, constraints, and remaining unknowns.
- `nerd-diagnose` with `nerd-surgery` owns root-cause work through **Diagnose**.
  Bring back the cause, evidence, smallest prescription, and proof experiment.

Use only prerequisites the work genuinely needs, one resolved endpoint at a
time. Reuse current handoffs. Mark unresolved material facts as `Unknown`; do
not invent them or hide alternatives inside conditional tasks.

## Planning Rules

- Use KISS by default. Read [Comprehensive](references/comprehensive.md) only
  for cross-boundary completeness and [DRY](references/dry.md) only for proven
  duplication. Use the [selection guide](references/principle-selection.md)
  when the right rule is unclear.
- If the request contains independent outcomes, write one plan per outcome.
- Map changed files and responsibilities before splitting work into tasks.
- Make each task one independently reviewable deliverable with its own proof.
- Order tasks by dependency. State `Depends on` only when the order is not
  obvious; do not add execution topology or coordination machinery by default.
- For behavior changes, plan the failing test, observed failure, minimum
  implementation, focused pass, and relevant regression proof. For static work,
  use a baseline check, minimum change, and post-change proof.
- Name exact file paths, symbols, and changes. Give exact commands and expected
  results.
- Include code or interface snippets only when prose would leave the
  implementer guessing.
- Do not use `TBD`, vague follow-ups, empty sections, or speculative work.
- Do not duplicate facts across the summary, tasks, and final verification.

## Plan Format

Save plans to `docs/plans/YYYY-MM-DD-<feature-name>.md`. A user-requested
location wins. Create the parent directory, save Markdown, and report the path.

Use this compact shape and omit optional fields that add no information:

````markdown
# [Feature] Implementation Plan

**Goal:** [Observable outcome]
**Approach:** [Simplest sufficient design]
**Scope:** [Included boundary and explicit non-goals]
**Proof:** [How completion will be verified]
**Spec:** [Optional path to the source spec]
**Sub-Agent Driven**: [YES/NO; use `nerd-smart` when the task is independently completable; by default its NO, but always ask user -> 'do you want to use a sub-agent driven? if no it will be executed in this session']

## File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `exact/path` | Create / Modify / Test | [Why this file changes] |

## Tasks

### Task N: [Deliverable]

**Outcome:** [One independently reviewable deliverable]
**Focus Record**
- **Intention:** [Real goal]
- **Expectation:** [One endpoint from Endpoint Mapping]
- **Scope:** [Core task plus at most three approved adjacents]
- **Role:** [Single best role]
- **Skills:** [skills to be used, bullet points]
- **Review Required:** [YES/NO; use `nerd-review` when the task is independently reviewable]
- **Sub-agent Model**: [only if enabled; value: inherit/<selected-model>; ALWAYS USE INHERIT MODEL UNLESS USER MENTION EXPLICITLY whether to decide the model manually or let use decide automatically via [mapping](references/subagent-model-mapping.md)]
**Outcome:** [One independently reviewable deliverable]
**Files:** `exact/path`, `tests/exact/path`
**Depends on:** [Optional task IDs]

1. Add the failing test or baseline check.
2. Run `[exact command]`; expect `[specific failure or baseline]`.
3. Make `[specific code or artifact change]`.
4. Run `[exact focused command]`; expect `[specific success]`.
5. Run `[exact regression command]`; expect `[specific success]`.

**Proof:** `[command or inspection]` → `[expected result]`

## Final Verification

- `[exact command]` → `[expected result]`
````

Use the file map only when multiple files make ownership unclear. Collapse or expand task steps to fit the work, but never omit the change, proof, or stopping condition. Include commit, push, deployment, or other external-write steps only when the user explicitly requested them; planning those steps does not authorize their execution.

## Self-Check

Before saving, verify that:
- every requirement is owned by a task;
- paths, symbols, interfaces, and commands match repository evidence;
- task outputs satisfy later dependencies;
- testable behavior follows red-green proof;
- no placeholder, duplicated fact, speculative abstraction, or unrelated work remains.

Fix findings inline. Preserve genuine unknowns as blockers.

## Stop

Stop before execution.

Do not execute the plan, mutate the repository, commit, push, or perform an external write. After saving, report the path and stop. Execution requires a new **Execute** Focus Record through `nerd-smart`.
