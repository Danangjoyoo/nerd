# Iteration Control: Continuity

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

## Preventing Forgetting

### Deterministic iteration packet

At the start of every iteration, inject or render a concise packet from authoritative state:

~~~text
workflow / run / loop / iteration identity
root goal and DoD version
parent outcome and integration target
current focus and why now
workspace and plan revisions
allowed scope and forbidden effects
entry evidence and latest failure fingerprint
local verifier and exit rules
best verified checkpoint
ready alternatives, blockers, and remaining budget
~~~

This packet should be generated from the ledger and contracts, not reconstructed from model recollection.

### Commit-before-switch

For S2/S3, before switching focus, delegating, compacting context, pausing, or
yielding, durably commit the following. For S1, update the compact session
packet before choosing another focus:

- Record the current artifact or environment revision.
- Record action receipts and verifier results.
- Record unresolved uncertainty and failure fingerprints.
- Update task status and invalidated evidence.
- Persist the next trigger candidates and why they are eligible.
- Create a committed checkpoint.

For S2/S3, no durable outcome commit means the iteration is still in flight.
For S1, do not switch focus until its compact packet contains the outcome and
fresh evidence.

### Separate memory kinds

Keep distinct:

- **Execution truth:** Contracts, current state, evidence, ownership, and ledger events.
- **Plan projection:** Revisable future work and ready set.
- **Episodic lessons:** Failed strategies and reusable verified observations.
- **Semantic knowledge:** General facts and skills reusable across loops.
- **Transcript:** Communication record.

Only execution truth and fresh evidence may authorize mutation or completion. Lessons and semantic retrieval can suggest actions but must be checked against the current state.

### Context condensation

Condensation may shorten model-visible history, but:

- Keep immutable source events and evidence outside the summary.
- Preserve IDs and source revisions in every condensed statement.
- Never summarize away the root goal, DoD, current focus, pending approvals, ambiguous side effects, or blockers.
- Treat a summary conflict as a reason to reload the source, not choose the more convenient wording.
## Failure Modes and Anti-Patterns

| Anti-pattern | Failure | Stronger rule |
| --- | --- | --- |
| Fixed full execution script | Later steps use assumptions invalidated by earlier results | Use a full outcome map with a one-iteration committed horizon |
| One giant iteration | The agent cannot isolate progress, failure, recovery, or evidence | Bound one primary objective and verification decision |
| One tool call equals one iteration | Mechanical operations fragment useful state transitions | Define iterations by decision and evidence boundaries |
| Static next-action string | Cursor becomes stale after changes or parallel work | Recompute readiness from contracts, ledger, and actual state |
| Schedule “five iterations later” | Ordinals shift and parallel loops have no global N | Use semantic triggers, dependencies, deadlines, or dwell rules |
| Start every discovered subtask | Agenda explodes and scope drifts | Classify, trace to DoD, admit, defer, or reject explicitly |
| Never alter the initial plan | Counterexamples and changed state cannot be incorporated | Version and minimally repair the route |
| Replan from scratch after every observation | Valid work is lost and the controller thrashes | Preserve verified work and invalidate affected descendants |
| Child says done | Local success is mistaken for parent integration | Parent accepts exact child evidence and reruns integration |
| Shared TASKS.md as multi-writer truth | Lost updates and interleaving corrupt the cursor | Use transactional state with per-loop ownership |
| Unique filename only | Same-run writers still race | Add single-writer streams, CAS, leases, and fencing |
| Timestamp as ordering authority | Concurrent clocks do not express causality | Use per-stream revision and causal event IDs |
| Transcript as memory | Context trimming or handoff loses critical state | Regenerate a focus packet from durable contracts and ledger |
| Snapshot overwrites history | Audit and recovery branches disappear | Keep append-only events; snapshots remain derived |
| Replay all tool calls | Side effects duplicate after recovery | Replay recorded outcomes; new execution is a new attempt |
| Save while agents mutate shared state | Snapshot may be internally inconsistent | Checkpoint at controlled boundaries or transactionally |
| Ledger stores secrets and raw reasoning | Persistence expands exposure and noise | Store minimal structured facts, receipts, hashes, and references |
| Plan completion equals task completion | Route checkboxes substitute for outcome proof | Only the root DoD can authorize DONE |
