# jOOQ Review

- **Use:** jOOQ SQL/generation/mapping boundary; pair with Java/Kotlin and database.
- **Level 1:** Check dialect, generated schema, binds, nulls, joins, order,
  cardinality methods, mapping, context/connection, tenant, and transaction scope.
- **Level 2:** Match query/repository/mapping/transaction conventions; test SQL,
  nulls, duplicate rows, rollback, dialect behavior, and representative plans.
- **Level 3:** Check persistence leakage, transaction ownership, duplicated query
  policy, dynamic complexity, N+1 calls, listeners, and schema coupling.
- **Proof:** Prefer metadata, integration tests, sanitized SQL/types, and saved plans.
- **Escalate:** Transaction escape, tenant/schema mix-up, cardinality error,
  unsafe SQL, mapping loss, or unbounded query.
- **Avoid:** Regeneration, value logging, shared-system SQL, and DSL style.

