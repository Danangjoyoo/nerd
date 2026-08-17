# Hang or Timeout

Use for work that stops making observable progress or exceeds a deadline; route completed-but-slow work to performance regression, and diagnose any earlier crash, rejection, or retry-loop symptom first.

## Capture

- Record the trigger, start time, expected completion, configured deadline, elapsed time, and whether the client, proxy, server, job, or test owns the timeout.
- Record nested deadlines and remaining budget at every boundary.
- Timestamp the path through callers, queues, services, storage, and dependencies; mark the last completed boundary, the first entered but incomplete boundary, and its awaited operation or signal.
- Prefer existing traces, structured logs, request or job IDs, metrics, queue depth, lock views, and dependency latency.
- When relevant, collect thread, task, coroutine, or goroutine stacks; process, connection, scheduler, and event-loop state; and at least two comparable runtime snapshots during the same stall.
- Sanitize secrets and payloads. Under load, prefer sampled profiles, bounded dumps, and existing telemetry over unbounded tracing or repeated full dumps.

## Diagnose

1. Locate the last completed boundary. Treat a downstream timeout as budget-exhaustion evidence, not proof that its owner caused the stall.
2. Trace each blocked unit to what it awaits and who can release or complete it. Mark that owner runnable, blocked, missing, saturated, cancelled, or external; continue until the chain closes, reaches a dependency, or evidence ends.
3. Compare repeated snapshots: stable waits and ownership suggest blocking; changing state without completion suggests livelock or unbounded work.
4. Keep one active hypothesis and use the smallest non-corrective check that separates it from the nearest alternative.
5. Check cancellation propagation, retry multiplication, queue residence time, and budget spent before the visible timeout; earlier congestion, a lost completion signal, or a shorter upstream deadline may be causal.
6. Report the first condition that explains both the stalled path and elapsed budget, with boundary timings, runtime state, wait ownership, and dependency-side evidence when available.

Signals and mechanisms:

- **Deadlock:** a stable waiter-owner cycle cannot advance; show the ownership cycle, not merely blocked threads.
- **Livelock:** participants stay runnable and state changes, but the completion condition does not advance across snapshots.
- **Starvation or saturation:** ready work gets no worker, connection, CPU, memory, or scheduler time; correlate capacity, queueing, and wait duration.
- **Backpressure:** a producer waits on a bounded downstream queue or consumer; show flow-control state and the slow or absent consumer.
- **Slow dependency:** local waiting is normal, but a database, network, filesystem, service, or subprocess exceeds remaining budget; use boundary timings and dependency-side evidence.
- **Unbounded or blocked local work:** CPU, iteration, retry, lock, channel, future, event, or I/O remains inside the local boundary; show repeated execution or a stable wait site and its unmet completion condition.

## Guardrails

- Diagnose only: do not increase timeouts, restart or kill work, release locks, drain queues, change concurrency or traffic, repair source, or mutate durable data, infrastructure, or production.
- Allow only disposable local artifacts required to observe the failure.
- Obtain approval before remote or production collection, and avoid collection whose overhead could materially affect a loaded system.
- Apply the parent **Confirmed / Probable / Unknown** gate; name the exact evidence gap and one bounded next check when confirmation is missing.
