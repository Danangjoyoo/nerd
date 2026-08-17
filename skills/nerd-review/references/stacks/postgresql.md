# PostgreSQL Review

- **Use:** PostgreSQL schema/SQL/migration boundary; preserve version, extensions,
  collation, isolation, search path, topology, and driver/ORM.
- **Level 1:** Check types/casts, nulls, constraints, joins, ordering, conflicts,
  index method/predicate, plans, transactions, locks, and migration lock/rewrite.
- **Level 2:** Match schema, constraints, indexes, migrations, transactions, and
  queries; test results, rollback, concurrency, and representative data size.
- **Level 3:** Check invariant ownership, racing app checks, table ownership, long
  transactions, lock cycles, queues/advisory locks, replicas, and enum evolution.
- **Proof:** Prefer source, snapshots, integration tests, and saved `EXPLAIN`.
- **Escalate:** Data loss, broken invariant, blocking migration, deadlock,
  incompatible type, or unbounded core query.
- **Avoid:** Production mutation, unsafe `EXPLAIN ANALYZE`, maintenance, and SQL style.

