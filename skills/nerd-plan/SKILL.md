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

## Explicit Plan Contract

This is the highest-priority contract within Nerd Plan. Apply it before interpreting inheritance, prerequisites, Multi-Goal Intake, or other planning rules.
Explicitly invoking `nerd-plan` is sufficient instruction to create and save the plan artifact. Do not ask whether the user wants a plan file or require a separate write or save command.
Once Plan owns the endpoint, you must always create and save the plan artifact; do not end with only a Focus Record, intake, prerequisite handoff, or discussion when the confirmed inputs are sufficient.
Fill the Plan Format template below; neither a Focus Record nor Multi-Goal Intake may replace the persisted plan. Multi-Goal Intake may organize independently completable outcomes as ordered tasks within one cohesive plan; keep the required size-based files below as one cohesive plan, even without a separate request to split files.
Treat related outputs, including master and subordinate artifacts, as task deliverables rather than reasons to leave or fragment the Plan endpoint.
Follow-up questions, feedback, and revisions about the plan remain on the **Plan** endpoint; update the same plan artifact whenever its content changes.
Leave **Plan** only when the user explicitly requests another endpoint. Execution requires a direct request to execute, implement, apply, or start work on the plan. Mentioning execution inside the plan never authorizes it.

## Inheritance

Use `nerd-smart` first and consume its resolved Focus Record. This route accepts only the **Plan** endpoint. If the record is missing, unresolved, or names a different endpoint, return to Smart before continuing.

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
- For Multi-Goal Intake, keep every accepted outcome under **Plan** and map it to one or more ordered tasks in the cohesive plan.
- Map changed files and responsibilities before splitting work into tasks.
- Make each task one independently reviewable deliverable with its own proof.
- Order tasks by dependency. State `Depends on` only when the order is not
  obvious; do not add execution topology or coordination machinery by default.
- For behavior changes, plan the failing test, observed failure, minimum
  implementation, focused pass, and relevant regression proof. For static work,
  use a baseline check, minimum change, and post-change proof.
- Name exact file paths, symbols, and changes. Give exact commands and expected
  results.
- Every plan must create a multi-goal ledger, including a one-goal plan. Follow
  [artifact layout and ledger](references/artifact-layout.md) for line thresholds,
  file responsibilities, and goal-to-task traceability.
- Every code-changing task must include a fenced code skeleton with the actual
  class and method names, or standalone function names, plus input/output types.
  Write pseudocode showing input validation, transformations, outputs, and
  relevant failure paths. Specify contracts when a boundary requires them;
  otherwise typed inputs and outputs suffice. Keep snippets illustrative, not a
  full implementation. For a task without code changes, state that no code
  skeleton is applicable and identify the artifact or configuration contract.
- Do not use `TBD`, vague follow-ups, empty sections, or speculative work.
- Do not duplicate facts across the summary, tasks, and final verification.

## Plan Format

Save plans to `docs/plans/YYYY-MM-DD-<feature-name>.md`. A user-requested
location wins. This is the default for plans under 300 lines; use the
[size-based layout](references/artifact-layout.md) for larger plans.
Create the parent directory, save Markdown, and report the path and ledger.

Use this compact shape and omit optional fields that add no information:

````markdown
# [Feature] Implementation Plan

**Goal:** [Observable outcome]
**Approach:** [Simplest sufficient design]
**Scope:** [Included boundary and explicit non-goals]
**Proof:** [How completion will be verified]
**Spec:** [Optional path to the source spec]
**Sub-Agent Driven**: [YES/NO; default to NO and continue asking unless the user explicitly requests sub-agent-driven planning]

## File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `exact/path` | Create / Modify / Test | [Why this file changes] |

## Goal Ledger

[Embed the ledger below 300 lines; otherwise link ledger.md. Use the schema in
references/artifact-layout.md.]

## Tasks

### Task N: [Deliverable]

**Outcome:** [One independently reviewable deliverable]
**Files:** `exact/path`, `tests/exact/path`
**Depends on:** [Optional task IDs]

**Focus Record**
- **Intention:** [Real goal]
- **Expectation:** [One endpoint from Endpoint Mapping]
- **Scope:** [Core task plus at most three approved adjacents]
- **Role:** [Single best role]
- **Skills:** [skills to be used, bullet points]
- **Review Required:** [YES/NO; use `nerd-review` when the task is independently reviewable]
- **Sub-agent Model**: [only if enabled; value: inherit/<selected-model>; ALWAYS USE INHERIT MODEL UNLESS USER MENTION EXPLICITLY whether to decide the model manually or let use decide automatically via [mapping](references/subagent-model-mapping.md)]


**Code skeleton and contract:** [Required for code changes; use repository language]
```text
class ExistingOrProposedClass:                  # omit for standalone functions
    function actualName(input: InputType) -> OutputType:
        validate input; on invalid input return/raise the specified error
        apply the named rule or transformation
        return the specified output, including the empty-result behavior
```
[Define concrete InputType/OutputType shapes and required boundary contracts;
replace example names and pseudocode with task-specific names and behavior.]

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
- every requirement is owned by a task and traced in the multi-goal ledger;
- total plan lines select the correct layout, including exact 300/500 boundaries;
- all ledger, index, master, and task links resolve without duplicated task bodies;
- code-changing tasks name real class/functions, types, pseudocode, and required contracts;
- paths, symbols, interfaces, and commands match repository evidence;
- task outputs satisfy later dependencies;
- testable behavior follows red-green proof;
- no placeholder, duplicated fact, speculative abstraction, or unrelated work remains.

Fix findings inline. Preserve genuine unknowns as blockers.

## Stop

Stop before execution.

Do not execute the plan, mutate the repository, commit, push, or perform an external write. After saving, report the path and stop. Execution requires a new **Execute** Focus Record through `nerd-smart`.
