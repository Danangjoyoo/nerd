# Multi-Goal Ledger Protocol

## Use When

Use a ledger only for a material goal queue: two or more independently
completable outcomes that need separate endpoints, dependency ordering,
cross-turn tracking, or protection from being dropped.

Do not create a ledger for several bullets that are constraints, examples,
acceptance criteria, or substeps of one outcome. Also skip it for a small
compound request that can be completed safely in one turn without losing state.

## Create the Ledger

Create one Markdown ledger in the runtime-provided temporary directory, or use
`~/.agent/tmp/` when none is available. Use a stable conversation, thread, or
task identifier in its filename and retain the absolute path until the queue is
complete.

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
>   - **Intention:** [Requested outcome]
>   - **Expectation:** [One endpoint]
>   - **Scope:** [Outcome boundary, necessary adjacencies, and mutation boundary]
>   - **Role:** [Only when it materially changes the approach]

## Queue Invariants

Keep one Focus Record for every material goal and exactly one goal **active**.
Status is **queued**, **active**, **blocked**, **done**, or **cancelled**. Never
collapse independent goals or borrow scope, assumptions, endpoint, delivery
approach, or proof from queued goals.

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

Companion selection is per active Plan or Execute goal, never per queue. Do not
carry a previous goal's delivery approach forward.
