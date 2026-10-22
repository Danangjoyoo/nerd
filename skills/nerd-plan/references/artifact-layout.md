# Plan Artifacts and Multi-Goal Ledger

Every saved plan includes a durable multi-goal ledger. Preserve each accepted
outcome as a goal; a one-goal plan has one row. Do not invent independent goals
from constraints, examples, or substeps. Smart's temporary intake is an input,
not a substitute for the plan's ledger.

## Choose by Complete Plan Length

Count the complete plan's logical Markdown lines, including blank lines, code
fences, skeletons, and task bodies, before splitting. Exclude the ledger and
navigation-only wrappers from this count. Record the count and chosen layout in
the entry document. Never pad or omit content to influence a threshold.

| Complete plan length | Required artifacts |
| --- | --- |
| Under 300 lines | `docs/plans/YYYY-MM-DD-<feature-name>.md`, with an embedded goal ledger |
| 300–500 lines inclusive | `docs/plans/YYYY-MM-DD-<feature-name>/plan.md` and `ledger.md` |
| Over 500 lines | Same directory with `master.md`, `ledger.md`, `index.md`, and one Markdown file per task |

A user-requested location wins; preserve the required file roles beside that
location. At exactly 300 lines use two files; at exactly 500 retain two files;
at 501 split by task. Estimate while drafting, then verify the actual complete
content once before saving. The split does not make the plan smaller: count
its substantive content across master and task files without navigation copies.

For follow-up revisions, update the same artifact set. If the complete content
crosses a threshold, migrate it to the required layout, update inbound links,
and remove superseded copies. Report the new entry and ledger paths.

## File Responsibilities

- `plan.md`: the complete plan and task bodies; link to `ledger.md`.
- `master.md`: goal, approach, scope, shared types/contracts, file map,
  dependency order, and final verification. Link to each task; do not repeat
  task bodies here.
- `task-NN-<name>.md`: exactly one task, using the task portion of Plan Format,
  including its Focus Record, outcome, files, dependencies, code skeleton,
  input/output pseudocode, required contracts, steps, and proof. Link shared
  contracts from master rather than copying them.
- `index.md`: entry point linking master, ledger, and every task in dependency
  order, with concise labels. It contains no second copy of the plan.
- `ledger.md`: the only durable source of goal/task status for split layouts.

## Ledger Schema and Lifecycle

Use the same schema for embedded and separate ledgers:

| Goal ID | Source requirement / outcome | Task IDs and links | Depends on | Status | Completion proof |
| --- | --- | --- | --- | --- | --- |
| G1 | [Accepted outcome] | [T1](relative-task-link) | none | queued | [Planned command and expected result] |

Use stable goal and task IDs and relative links to task files or task anchors.
Every accepted goal maps to tasks; every task maps back to a goal. Preserve
source order unless a dependency requires a different order. Keep dependencies
explicit in the ledger, even when task order makes them obvious.

On a new plan, execution status starts `queued`; writing or self-reviewing a
plan never marks implementation `active` or `done`. Preserve already verified
execution status when revising an existing plan. The later executor updates
`queued`, `active`, `blocked`, `done`, or `cancelled`, keeps at most one goal
active, records blockers, and replaces planned proof with actual evidence before
marking done. This ledger does not authorize execution.

Before finishing, check goal/task coverage, dependency order, all relative
links, correct file count/roles, and code skeleton completeness. Report the entry
file and the embedded ledger anchor or separate `ledger.md`, then stop at Plan.
