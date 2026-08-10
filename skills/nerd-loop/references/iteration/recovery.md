# Iteration Control: Recovery

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

## Contents

- [Ledger Placement and Identity](#ledger-placement-and-identity)
- [Placement priority](#placement-priority)
- [Unique identity](#unique-identity)
- [Race Safety and Parallel Agents](#race-safety-and-parallel-agents)
- [Storage choices](#storage-choices)
- [Single-writer streams](#single-writer-streams)
- [Expected revision and idempotency](#expected-revision-and-idempotency)
- [Leases and fencing](#leases-and-fencing)
- [Artifact races](#artifact-races)
- [Crash Recovery and Resumption](#crash-recovery-and-resumption)
- [Ambiguous effects](#ambiguous-effects)
- [Snapshots and bounded history](#snapshots-and-bounded-history)

## Ledger Placement and Identity

### Placement priority

Use this order:

1. Runtime-provided durable workflow/checkpoint storage.
2. Explicitly configured durable database or state URI.
3. Repository-approved state location excluded from version control.
4. Per-user application-state directory keyed by a workspace fingerprint.
5. Secure runtime or temporary directory only when restart survival is not required.

On systems following the XDG Base Directory specification, histories and restartable state belong under XDG_STATE_HOME; sockets, leases, and disposable login-lifetime coordination belong under XDG_RUNTIME_DIR. Do not place authoritative resumable state in a general temporary directory.

Use a layout like:

~~~text
<state-root>/nerd-loop/
  workspaces/<workspace-fingerprint>/
    workflows/<workflow-id>/
      runs/<run-id>/
        ledger database or event streams
        checkpoints/
        evidence references/
~~~

Do not write hidden state into the repository merely because it is convenient. Repository-local placement needs repository policy or user authorization, an ignore rule, and a cleanup contract.

### Unique identity

For S2/S3, use opaque, collision-resistant IDs such as UUIDv7:

- workflow_id: stable logical user task across resumed physical runs.
- run_id: one physical execution generation.
- loop_id: one root or child loop instance.
- iteration_id: one logical bounded focus.
- attempt_id: one execution or retry of that iteration.
- event_id: one immutable event and idempotency identity.
- ordinal: display order local to a loop, allocated transactionally.

Do not use timestamps, process IDs, prompt slugs, agent names, or iteration numbers alone as unique identity. Keep human-readable labels separate from IDs.

For an ephemeral file-only ledger, create the run directory atomically with a secure unique-directory primitive. Unique naming prevents two independent runs from sharing a path; it does not solve concurrent writes within one run.
## Race Safety and Parallel Agents

### Storage choices

- **Single agent, one host:** A private append-only stream with atomic snapshots can be sufficient.
- **Several local processes:** Prefer one SQLite database per workspace with transactional writes; WAL allows concurrent readers but SQLite still intentionally serializes writers.
- **Several hosts or shared service:** Use a transactional server database or durable workflow engine with optimistic concurrency, leases, and retries.

Do not use shared Markdown, YAML, JSON, or uncoordinated NDJSON appends as an authoritative multi-writer ledger.

### Single-writer streams

Prefer one writer per loop stream:

- The parent coordinator owns the parent stream.
- Each parallel child owns a different child-loop stream.
- A child sends a result command or receipt to the parent; it does not append directly to the parent history.
- The parent records CHILD_ACCEPTED or CHILD_REJECTED with the exact child revision and result hash.

### Expected revision and idempotency

Every append should provide:

- Expected current stream revision.
- Owner identity and ownership epoch when applicable.
- Stable command or operation ID.
- Stable event IDs and payload hashes.

If the expected revision changed, reload and recompute. Never override the conflict with last-writer-wins.

If commit acknowledgement is ambiguous, retry with the same IDs. A duplicate with identical content may return the original receipt; the same ID with different content must be rejected.

### Leases and fencing

Use a renewable lease to recover abandoned ownership, and a monotonically increasing fencing epoch to reject stale writers. A lease alone is insufficient: an old paused worker can resume after expiry unless the ledger and affected resource reject its older epoch.

If fencing cannot be enforced on an external resource, combine idempotency keys, base-revision checks, isolated workspaces, and explicit reconciliation. Record the limitation.

### Artifact races

A unique ledger prevents metadata collision, not code, file, deployment, or database collision. Before parallel mutation, claim the affected resource set or provide isolated worktrees/sandboxes. Revalidate the artifact base revision before integration.
## Crash Recovery and Resumption

On resume:

1. Reopen the exact workflow and run identity; never guess from the newest directory alone.
2. Verify ledger and snapshot schema versions and hashes.
3. Replay from the latest verified checkpoint through later committed events.
4. Find nonterminal attempts and inspect their ownership lease.
5. Acquire a higher fencing epoch before takeover.
6. Reconcile planned external effects with target-system receipts.
7. Append ATTEMPT_ABANDONED or RECOVERY_STARTED as appropriate.
8. Rebuild the Loop Map, invalidate stale evidence, and resume from committed facts.

### Ambiguous effects

A crash after an external effect but before its receipt creates an unknown outcome. Do not blindly repeat it.

- Query the target with the stable operation ID when possible.
- Retry only if the operation is idempotent or the target proves it did not occur.
- Compensate only under explicit authority.
- Otherwise retain `OUTCOME_UNKNOWN` and escalate or repair the reconciler.

Exactly-once invocation across an independent ledger and external system is generally unavailable without a shared transaction. Design for idempotent effects and exactly-once recording of accepted receipts.

### Snapshots and bounded history

Snapshots are derived acceleration structures, not truth replacements. Include:

- Ledger revision covered.
- Contract and plan versions.
- Current Loop Map and focus.
- DoD criterion vector and fresh evidence references.
- Best verified checkpoint.
- Budgets, open children, blockers, and ambiguous effects.
- State schema and content hashes.

When history becomes too large, close the physical run with an explicit continuation event and start a new run generation carrying the minimum verified state plus predecessor links. Never silently truncate active history.
