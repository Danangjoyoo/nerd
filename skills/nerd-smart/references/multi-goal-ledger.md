# Multi-Goal Intake and Ledger Protocol

## Use When

Use Multi-Goal Intake only when a request contains two or more independently
completable outcomes. Structure is a scan boundary, not proof of multiple goals.
Inspect likely boundaries such as:

- multiple numbered or bulleted instruction items;
- multiple instruction sentences; or
- multiple instruction paragraphs separated by whitespace.

Split only boundaries that remain independently completable after reading their
meaning. Constraints, examples, acceptance criteria, and substeps stay with
their parent outcome even when they are bullets or separate paragraphs. A
qualifying intake may queue endpoint work, but it must never replace the active
endpoint's required deliverable.

## Create and Show the Intake

Create one Markdown ledger in the runtime-provided temporary directory, or use
`~/.agent/tmp/` when none is available. Use a stable conversation, thread, or
task identifier in its filename and retain the absolute path until the queue is
complete.

Preserve each original command line and its listed position beside a concise
normalized goal. Redact credential and secret values while retaining useful
placeholders, and do not store unrelated conversation.

Before substantive work, show the complete intake in the session using this
structure. The displayed intake and persisted ledger must match:

> **Multi-Goal Intake**
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

Keep one visible Focus Record for every goal and exactly one goal **active**.
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
path, show the current Multi-Goal Intake in the session, and treat it as the
source of truth. If it is missing or unreadable, reconstruct it from explicit
user input and do not continue from memory.

Update the ledger before acting when the user adds, removes, reorders, or changes
a goal. Record every status and dependency change immediately. At the active
endpoint, mark the goal done, reread the ledger, and activate the next eligible
goal. If work drifts, ask whether to switch goals or return before acting.

Companion selection is per active Plan or Execute goal, never per queue. Do not
carry a previous goal's delivery approach forward.
