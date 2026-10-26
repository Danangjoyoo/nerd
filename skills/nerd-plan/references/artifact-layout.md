# Plan Artifacts and Ledgers

Every plan has **one goal ledger table plus exactly one task ledger table per
goal**, including single-goal plans. Preserve accepted outcomes; constraints,
examples, and substeps do not create independent goals. Smart's temporary intake
cannot replace these durable ledgers. Use the canonical tables and full example in `templates/templates.md`
(relative to the skill root), linked from Plan Format in `SKILL.md`.

## Size-Based Layout

Count logical Markdown lines across the complete substantive plan, including
blanks, code fences, skeletons, and task bodies. Exclude ledgers and navigation
wrappers. Record the count and layout in the entry document; never pad or omit
content to alter thresholds. Estimate while drafting, then verify once before saving.

| Complete plan length | Required artifacts under `docs/plans/` |
| --- | --- |
| Under 300 | `YYYY-MM-DD-<feature>.md`, with embedded ledgers |
| 300–500 inclusive | `YYYY-MM-DD-<feature>/plan.md` and `ledger.md` |
| Over 500 | Same directory: `master.md`, `ledger.md`, `index.md`, one file per task |

Exactly 300 uses two files; exactly 500 still uses two; 501 splits by task.
A requested location wins, preserving these file roles beside it. Splitting
does not reduce the count: count substantive master/task content without copies.
On revision, retain the artifact set unless a threshold requires migration;
update inbound links, remove superseded copies, and report new entry/ledger paths.

## File Roles

- `plan.md`: complete plan and task bodies; links to `ledger.md`.
- `master.md`: goal, approach, scope, shared types/contracts, file map, dependency
  order, final verification, and task links; no repeated task bodies.
- `task-NN-<name>.md`: exactly one task in Plan Format, including Focus Record,
  outcome, goal, files, dependencies, skeleton, typed pseudocode, contracts,
  steps, and proof. Link shared contracts from master instead of copying.
- `index.md`: entry point linking master, ledger, and tasks in dependency order;
  concise labels, no second plan copy.
- `ledger.md`: goal ledger followed by one task ledger section/table per goal;
  sole durable status source in split layouts. No separate per-goal files needed.

## Traceability and Status

- Use stable goal/task IDs and relative links to task files or anchors. Link each
  goal row to its task ledger. Store goal dependencies/status/proof in the goal
  ledger and task dependencies/status/proof in its task ledger.
- Every goal maps to tasks; each task appears once in its owning goal's table
  and names that goal in its body. Reference shared work through dependencies,
  not duplicated rows or bodies. Preserve source order unless dependencies differ.
- Always list dependencies in ledgers, even if order is obvious: goal IDs for
  goal dependencies, task IDs for task dependencies, including cross-goal tasks.
- New goal/task statuses start `queued`; drafting or self-review never means
  implementation is `active` or `done`. Preserve verified status on revision.
- The later executor uses `queued`, `active`, `blocked`, `done`, or `cancelled`,
  with at most one active goal. Record blockers beside blocked rows. Replace
  planned proof with actual evidence before marking a task or goal done.
  A goal is done only when all required tasks are done and goal proof is verified.
  Ledgers never authorize execution.

Before finishing, check goal/task coverage, one task table per goal, agreement
with task bodies, dependencies, links, file roles/count, and complete skeletons.
Report the entry plus embedded ledger anchors or `ledger.md`; stop at Plan.
