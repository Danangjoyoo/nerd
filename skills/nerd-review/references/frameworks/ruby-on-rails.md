# Ruby on Rails Review

- **Use:** Rails boundary; pair with Ruby and crossed DB/Redis/Sidekiq references.
- **Level 1:** Check routes, middleware, callbacks, params, auth, rendering,
  validations, associations, queries, transactions, Zeitwerk, cache, and jobs.
- **Level 2:** Match controller/model/service, policy, serializer, error, scope,
  and spec conventions; test auth, callbacks, transactions, queries, and jobs.
- **Level 3:** Check policy/persistence/HTTP/job separation, callback/mixin coupling,
  globals, default scopes, cross-model writes, and uncommitted job inputs.
- **Proof:** Prefer focused specs/static evidence; inspect boot effects first.
- **Escalate:** Auth gap, data corruption, unbounded query, migration break,
  state leak, or lost job.
- **Avoid:** Migrations, tasks, consoles, retries, cache clears, and Rails style.

