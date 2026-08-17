# Ruby on Rails Diagnosis

## Scope

- Use when Rails owns the active boundary.
- Pair with Ruby; add database, Redis, Sidekiq, or integration guidance only at that boundary.

## Capture

- Rails/Ruby versions, Bundler lockfile, revision, boot command, `RAILS_ENV`.
- Process: server, worker, console, task; request/job ID and full cause/backtrace.
- Config/credential source names; eager-load/cache settings; routes and middleware.
- Database role/shard, relevant components, expected/observed lifecycle event.
- Redacted logs, params, SQL/bind types, job metadata, and timestamps.

## Diagnose

1. **Freeze one event.** Identify boot, request, job, or task and its first divergence.
2. **Trace boot in order.** Check Bundler -> railties/engines -> initializers ->
   credentials/config -> Zeitwerk/eager load -> database setup -> server binding.
3. **Check constants.** Compare constant/namespace, inflector/acronyms, expected path,
   autoload/eager-load paths, engine isolation, and loaded source.
4. **Trace dispatch.** Follow proxy/server -> route/verb/constraints -> middleware ->
   params/auth -> callbacks -> action -> render/serialize -> exception handling.
5. **Trace Active Record.** Record validations/callbacks, transaction boundary,
   connection role/shard, sanitized SQL/binds, query cache, associations, locks,
   commit/rollback, and serialization; load database guidance at server evidence.
6. **Trace cache/jobs.** Check cache key/version/store/invalidation. For Active Job,
   record adapter, class/arguments, enqueue/perform IDs, queue, retry, and commit timing.
7. **Compare environments.** Diff defaults, initializers, credential presence,
   assets/build, locale/timezone, cache class, eager loading, and database endpoint.
8. **Validate safe introspection.** `bin/rails zeitwerk:check`, `bin/rails routes`, and
   `bin/rails middleware` boot the app; inspect side effects before local/disposable use.
9. **Classify and stop.** Record first divergent lifecycle boundary, provenance,
   direct evidence, and missing confirmation; apply the parent confidence gate.

## Signals

- Boot-only: initializer, config/credential, eager-load, or dependency boundary.
- Environment-only: effective setting matters only when it predicts the symptom path.
- Request-only: routing, middleware, callback, authorization, render, or serialization.
- Data-only: callback/transaction/cache/connection behavior or database-owned evidence.

## Guardrails

- Never run migrations, seeds, repair tasks, `rails runner`, mutating console commands,
  job replays, cache clears, or production requests during Diagnose.
- Do not enable production debug/query tags, verbose SQL, or broader log levels.
- Redact params, sessions, cookies, credentials, SQL binds, logs, and job arguments.
- Diagnose only; stop before route, initializer, callback, autoload, data,
  dependency, configuration, or deployment changes.

Anchors: [debugging](https://guides.rubyonrails.org/debugging_rails_applications.html),
[autoloading](https://guides.rubyonrails.org/autoloading_and_reloading_constants.html),
[initialization](https://guides.rubyonrails.org/initialization.html).
