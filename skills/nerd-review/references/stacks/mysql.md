# MySQL Review

- **Use:** MySQL schema/SQL/migration boundary; preserve version, SQL mode,
  charset/collation, engine, isolation, topology, and driver.
- **Level 1:** Check types, signedness, defaults, constraints, coercion, nulls,
  joins, ordering, indexes, plans, transactions, locks, and migration compatibility.
- **Level 2:** Match schema, keys, indexes, migrations, transactions, and queries;
  test results, constraints, rollback, concurrency, and representative data size.
- **Level 3:** Check invariant ownership, racing app-only checks, table ownership,
  long transactions, lock cycles, unbounded scans, and deploy coupling.
- **Proof:** Prefer source, schema snapshots, focused integration tests, and saved plans.
- **Escalate:** Data loss/truncation, broken uniqueness, deadlock, blocking deploy,
  or core query outage.
- **Avoid:** Production SQL/migrations/locks/maintenance and naming-only findings.

