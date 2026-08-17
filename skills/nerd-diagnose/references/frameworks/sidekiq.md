# Sidekiq Diagnosis

- Load when Sidekiq owns the active job boundary.
- Pair with Ruby and Redis; add Rails only for Rails or Active Job execution.

## Capture

- Record Sidekiq/Ruby versions and edition, process command, environment, deployment identity, and configuration precedence.
- Record effective queues/order/weights, concurrency, capsules, fetch strategy, middleware, and connection-pool limits.
- Record Redis endpoint, database, topology, and evidence from the exact server process.
- Fingerprint one job: JID/provider ID, displayed and underlying class, queue, timestamps, retry count, process/thread, and sanitized argument shape.

## Diagnose

1. **Locate the phase:** Separate client serialization/enqueue, Redis persistence, scheduled/retry promotion, server fetch, middleware, deserialization/perform, acknowledgement, retry, and dead handling.
2. **Resolve routing:** Compare process arguments, environment YAML, queue names/order/weights, capsules, and process identity. Use existing inventory, metrics, or read-only UI evidence.
3. **Measure backlog:** Compare latency, size, enqueued/busy counts, throughput/failures, scheduled/retry/dead counts, and heartbeats in one time window.
4. **Trace failure:** Preserve the original exception/cause chain, job and middleware frames, attempt timeline, external calls, and database transaction state.
5. **Check concurrency:** Compare busy threads, Ruby thread state, CPU/memory, database and Redis pool waits, network latency, timeouts, and shutdown signals.
6. **Check delivery:** Verify argument compatibility, retry/backoff, idempotency assumptions, uniqueness/locking extensions, and whether enqueue preceded the surrounding database commit.
7. **Classify:** Record the first divergent phase, exact job/process provenance, direct evidence, and missing confirmation; apply the parent confidence gate.

## Read Signals Carefully

- A Redis-visible job does not prove that a server can or should fetch it.
- Queue size alone does not distinguish bursts from starvation; large-set iteration is costly and race-prone.
- Separate deterministic job failure from thread safety, starvation, shutdown, and dependency failure.
- A Redis timeout may originate in CPU, pools, network, or Redis; cross only at the first evidenced boundary.
- Eventual retry success does not prove the original cause is gone.

## Guardrails

- Bound read-only queue/retry/dead lookups by queue, JID, and time window; redact arguments and payloads.
- Never retry, delete, kill, reschedule, enqueue, clear, pause, quiet, stop, or reassign jobs or processes.
- Do not change concurrency, queues, retry policy, Redis settings, pool sizes, or start a replacement worker.
- Do not enable persisted backtraces or verbose argument logging as a live probe.
- Stop before code, job, Redis, database, or operational changes.

Official anchors: [monitoring](https://github.com/sidekiq/sidekiq/wiki/Monitoring), [error handling](https://github.com/sidekiq/sidekiq/wiki/Error-Handling), and [Redis usage](https://github.com/sidekiq/sidekiq/wiki/Using-Redis).
