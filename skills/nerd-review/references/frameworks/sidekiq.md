# Sidekiq Review

- **Use:** Sidekiq job boundary; pair with Ruby/Redis and Rails when relevant.
- **Level 1:** Check queue, JSON-safe arguments, middleware, retries, idempotency,
  partial effects, enqueue-after-commit, concurrency, pools, fan-out, and starvation.
- **Level 2:** Match base class, queue, retry/error, argument, observability, and
  service conventions; test serialization, duplicates, retries, and missing data.
- **Level 3:** Check durable orchestration, enqueue/perform policy split, failure
  ownership, compensation, retry layering, fan-out, and recovery.
- **Proof:** Prefer focused tests and config inspection.
- **Escalate:** Duplicate irreversible effect, job loss, tenant leak, retry storm,
  starvation, or pre-commit execution.
- **Avoid:** Enqueue/retry/delete/reschedule/clear/pause and class-shape opinions.

