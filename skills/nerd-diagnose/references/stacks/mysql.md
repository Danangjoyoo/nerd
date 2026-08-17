# MySQL Diagnosis

## Provenance and Scope

- Use only when evidence reaches MySQL; stop at cause and apply the parent confidence gate.
- Record environment, endpoint role/UUID, version, schema, account, driver/ORM, pool route, request/time window, SQLSTATE, and expected versus observed behavior.
- Record normalized SQL/digest, bind **types/nullability/classes**, transaction order, isolation/autocommit, retries, and timeout chain.
- Redact credentials, literals, bind values, customer data, hosts, paths, and topology; preserve only discriminating shape.

## Diagnose

1. **Verify target and client.** Confirm authorized environment, writer/replica route, schema, incident window, and `mysql --version`; preserve denied access as an evidence gap.
2. **Capture server/session identity** with version-matched, read-only queries:
   ```sql
   SELECT VERSION(), DATABASE(), CURRENT_USER(), USER(), CONNECTION_ID();
   SELECT @@session.sql_mode, @@session.time_zone, @@session.transaction_isolation, @@session.autocommit, @@session.character_set_connection, @@session.collation_connection, @@session.optimizer_switch;
   SELECT @@global.server_uuid, @@global.read_only, @@global.super_read_only; SHOW GRANTS;
   ```
3. **Reconstruct semantics without executing suspect SQL.** Compare emitted SQL with source/ORM intent:
   - Check placeholders, types, nulls, casts, `NULL` logic, joins, filters, ordering, and pagination.
   - Check affected rows, timezone, collation, `sql_mode`, retries, commit/rollback, and snapshot.
4. **Inspect named schema objects only when metadata-lock/statistics-cache effects are authorized.**
   - Prefer migrations or dumps; for live reads, use validated, quoted identifiers.
   - Compare types, defaults, generated columns, charset/collation, constraints, and index shape.
   - Treat InnoDB row and cardinality values as estimates:
   ```sql
   SHOW CREATE TABLE <quoted_schema>.<quoted_table>\G
   SHOW INDEX FROM <quoted_table> FROM <quoted_schema>;
   SELECT TABLE_NAME,ENGINE,TABLE_ROWS,TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA='<schema>' AND TABLE_NAME IN ('<table>');
   SELECT TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME,CARDINALITY,INDEX_TYPE FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='<schema>' AND TABLE_NAME IN ('<table>') ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX;
   ```
5. **Inspect a plan only after a safety gate.**
   - Prefer captured plans; for sanitized, side-effect-free, non-locking `SELECT`, use plain `EXPLAIN` or `EXPLAIN FORMAT=JSON`.
   - Compare access, indexes/key parts, join order, row estimates, filters, sorts, and temporary work.
   - Plain `EXPLAIN` estimates without executing; `EXPLAIN ANALYZE` executes. Never run `EXPLAIN ANALYZE`, suspect SQL, side-effecting routines, or DML here.
6. **Inspect waits/transactions** with narrow filters, selected columns, and limits:
   ```sql
   SELECT trx_id,trx_state,trx_started,trx_wait_started,trx_mysql_thread_id FROM information_schema.INNODB_TRX WHERE trx_state='LOCK WAIT' ORDER BY trx_wait_started LIMIT 50;
   SELECT REQUESTING_THREAD_ID,BLOCKING_THREAD_ID,REQUESTING_ENGINE_TRANSACTION_ID,BLOCKING_ENGINE_TRANSACTION_ID FROM performance_schema.data_lock_waits LIMIT 50;
   SELECT OBJECT_SCHEMA,OBJECT_NAME,LOCK_TYPE,LOCK_DURATION,LOCK_STATUS,OWNER_THREAD_ID FROM performance_schema.metadata_locks WHERE OBJECT_SCHEMA='<schema>' AND LOCK_STATUS IN ('PENDING','GRANTED') LIMIT 100;
   ```
   - If already authorized, capture `SHOW ENGINE INNODB STATUS\G` once; retain only redacted deadlock/transaction sections. Never enable monitors.
7. **Correlate connections and resources.** Compare pool acquisition/query/socket deadlines and retries with CPU, memory, disk/I/O, network, buffer-pool, and thread telemetry; use two timestamped counter snapshots, never resets.
   ```sql
   SELECT VARIABLE_NAME,VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME IN ('Threads_connected','Threads_running','Connections','Aborted_connects','Connection_errors_max_connections','Max_used_connections');
   SELECT VARIABLE_NAME,VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME IN ('max_connections','wait_timeout','interactive_timeout');
   ```
8. **Use existing statement/replication evidence only.** If already collected, inspect bounded normalized digest counts/timings; missing rows mean instrumentation gap.
   ```sql
   SELECT SCHEMA_NAME,DIGEST,COUNT_STAR,SUM_TIMER_WAIT,MAX_TIMER_WAIT,SUM_ROWS_EXAMINED,SUM_ROWS_SENT,FIRST_SEEN,LAST_SEEN FROM performance_schema.events_statements_summary_by_digest WHERE SCHEMA_NAME='<schema>' AND LAST_SEEN>=NOW()-INTERVAL 15 MINUTE ORDER BY MAX_TIMER_WAIT DESC LIMIT 50;
   ```
   - For stale reads, prove route/role and use version-correct `SHOW REPLICA STATUS\G`; correlate receiver/applier progress, positions/GTIDs, errors, and timestamps—not lag alone.
9. **Separate boundaries and classify.** Distinguish server execution from driver/serialization, ORM mapping, pool/network wait, cache, retry/idempotency, read routing, and result consumption; report **Confirmed**, **Probable**, or **Unknown** and stop.

## Fast Signals

- Wrong rows: emitted SQL + typed binds + transaction/snapshot + schema/collation/timezone + route.
- Error: original code/SQLSTATE + account/session + column definition; unwrap driver/ORM errors.
- Slow/hang: same workload + plan estimates + lock edge + pool/resource window; cumulative counters alone prove nothing.
- Stale data: commit/read timestamps + UUID/role + receiver/applier progress; separate cache and isolation effects.

## Guardrails

- No DML/DDL, suspect execution, locking reads, transactions, session changes, kills, grants, or account switching.
- No `ANALYZE/OPTIMIZE TABLE`, stats/cache reset or refresh, warming, scans, benchmarks, or load tests.
- No Performance Schema/log/monitor enablement or reset; no config, pool, replication, routing, or failover changes.
- Bound and redact every catalog, process, status, statement, lock, and replication read; do not poll aggressively.
- Metadata reads may lock or refresh cached/persistent statistics; skip them when that effect is unauthorized.

## Official Anchors

- [EXPLAIN](https://dev.mysql.com/doc/refman/8.4/en/explain.html)
- [Lock tables](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-lock-tables.html)
- [Statement summaries](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-statement-summary-tables.html)
- [Replica status](https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html)
