# Multi-Goal Ledger Protocol

## Use When

Use this reference for two or more independently completable goals, each with
its own endpoint or stopping condition. Do not split constraints, examples,
acceptance criteria, or substeps from their parent goal.

## Create the Ledger

Create one Markdown ledger in the runtime-provided temporary directory, or use
`~/.agent/tmp/` when none is available. Use a stable conversation, thread, or
task identifier in its filename and retain the absolute ledger path until the
queue is complete.

Preserve each original command line and its listed position beside a concise
normalized goal. Redact credential and secret values while retaining useful
placeholders, and do not store unrelated conversation.

Use this structure:

> **Goal Ledger**
> - **Path:** [Absolute ledger path]
> - **Order basis:** [Explicit, listed, or dependency-adjusted with reason]
>
> **Goal [ID] — [Short name]**
> - **Source:** [Original bullet, number, or command line]
> - **Status:** [Queued, active, blocked, done, or cancelled]
> - **Depends on:** [Goal IDs or none]
> - **Focus Record:**
>   - **Intention:** [Smallest real goal]
>   - **Expectation:** [One endpoint]
>   - **Scope:** [Only this goal and approved adjacents]
>   - **Role:** [Single best role]

## Queue Invariants

Status is **queued**, **active**, **blocked**, **done**, or **cancelled**. Keep one
Focus Record for every goal and exactly one goal **active**. Never collapse
independent goals or borrow scope, assumptions, endpoint, principle, or proof
from queued goals.

Preserve explicit user order; otherwise default to listed order. Reorder only
for a hard dependency. If that conflicts with explicit order or materially
changes outcome, safety, cost, or rework, verify the order with one question.
Otherwise record the dependency and reason in the ledger.

## Lifecycle

Before starting, resuming, switching, or completing a goal, and at the beginning
of every later turn while the queue exists, reread the ledger from its absolute
path and treat it as the source of truth. If it is missing or unreadable,
reconstruct it from explicit user input and do not continue from memory.

Update the ledger before acting when the user adds, removes, reorders, or changes
a goal. Record every status and dependency change immediately. At the active
endpoint, mark the goal done, reread the ledger, and activate the next eligible
goal. If work drifts, ask whether to switch goals or return before acting.

Principle selection is per goal, never per queue. Run it from the active goal's
own evidence when that goal reaches Plan or Execute; select no principle at other
endpoints and never carry a previous goal's principle forward.
