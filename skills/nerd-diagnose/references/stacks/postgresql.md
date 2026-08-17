# PostgreSQL Diagnosis

## Provenance and Scope

- Use only when evidence reaches PostgreSQL; stop at cause and apply the parent confidence gate.
- Record environment, server/version, database/schema/search path, role/session, primary/replica route, client/ORM/pool, release, trace, and timezone-aware window.
- Record SQL fingerprint/query ID, bind **types and redacted classes**, prepared/literal mode, transaction/isolation, retries/timeouts, SQLSTATE, timing, rows, and expected result.
- Redact secrets, raw binds, SQL literals, customer data, client addresses, logs, policies, hosts, and topology.

## Diagnose

1. **Authorize and pin the target.** Start with repository config and sanitized logs/traces; use an existing role and bounded production reads only. Missing access is evidence, never permission to elevate.
2. **Capture connection and effective session state** without changing it:
   ```sql
   \conninfo
   SELECT version(),current_database(),current_user,session_user,current_schema(),current_schemas(true),inet_server_addr(),inet_server_port(),inet_client_addr(),current_setting('application_name');
   SHOW search_path; SHOW TimeZone; SHOW transaction_isolation; SHOW transaction_read_only; SHOW statement_timeout; SHOW lock_timeout;
   SELECT name,setting,unit,source FROM pg_settings WHERE name IN ('search_path','TimeZone','DateStyle','lc_collate','default_transaction_isolation','statement_timeout','lock_timeout','work_mem','effective_cache_size') ORDER BY name;
   ```
3. **Reconstruct semantics.**
   - Match SQL shape, typed binds, role/database/schema, transaction state, and route.
   - Inspect casts, `NULL` logic, timestamps/timezone, collation, ordering, affected rows, savepoints, aborted transactions, retries, and timeout ownership.
4. **Resolve objects and access.** Verify qualified names, `search_path`, ownership/grants/default privileges, RLS policies, extensions, types/functions/operators, and actual role. Compare a working session; never grant or bypass RLS to test.
5. **Inspect named structure/statistics.** Use bounded catalogs, `pg_stats`, `pg_stat_user_tables`, and `pg_stat_user_indexes`; compare types, constraints, predicates, expressions/operator classes, index shape, estimated tuples, and analyze/vacuum timestamps.
   ```sql
   SELECT schemaname,relname,seq_scan,idx_scan,n_live_tup,n_dead_tup,last_analyze,last_autoanalyze,last_vacuum,last_autovacuum FROM pg_stat_user_tables WHERE schemaname='<schema>' AND relname IN ('<table>');
   SELECT schemaname,relname,indexrelname,idx_scan,pg_size_pretty(pg_relation_size(indexrelid)) FROM pg_stat_user_indexes WHERE schemaname='<schema>' AND relname IN ('<table>');
   ```
   - Statistics and cumulative counters are estimates/window-dependent; size alone does not prove bloat.
6. **Inspect a plan only for known side-effect-free SQL.** Use plain `EXPLAIN (VERBOSE, SETTINGS, FORMAT JSON) ...`; compare first cardinality divergence, scans/joins, filters/casts, sort/spill risk, parallelism, pruning, and index usability.
   - Plain `EXPLAIN` does not execute. `EXPLAIN ANALYZE` executes and may preserve side effects; never use it or execute suspect SQL/DML here. A rollback wrapper is not a safety proof.
7. **Inspect waits and transactions** with identified PIDs/database, selected columns, and limits; omit query text:
   ```sql
   SELECT pid,usename,datname,application_name,state,wait_event_type,wait_event,xact_start,query_start,backend_xid,backend_xmin FROM pg_stat_activity WHERE datname=current_database() AND (state<>'idle' OR wait_event IS NOT NULL) ORDER BY query_start NULLS LAST LIMIT 50;
   SELECT pid,pg_blocking_pids(pid) AS blocking_pids,wait_event_type,wait_event,xact_start,query_start FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' ORDER BY query_start LIMIT 50;
   SELECT locktype,database,relation,page,tuple,virtualxid,transactionid,classid,objid,objsubid,virtualtransaction,pid,mode,granted,fastpath FROM pg_locks WHERE pid IN (<identified_pid>) LIMIT 100;
   ```
   - Correlate blockers, transaction age, isolation, deadlock/serialization SQLSTATE, and server logs; separate lock wait from pool exhaustion or application-held transactions.
8. **Correlate resources and topology.** Align CPU, memory, cache/I/O, temp files, checkpoints/WAL, connections, pool waits, and retries to the same window. Prove primary/replica routing and compare receive/replay state with commit/read timestamps:
   ```sql
   SELECT pg_is_in_recovery(),pg_last_wal_receive_lsn(),pg_last_wal_replay_lsn(),now()-pg_last_xact_replay_timestamp() AS replay_delay;
   ```
   - Separate replica lag from MVCC snapshot age, transaction visibility, cache, and ORM identity maps.
9. **Use existing instrumentation only.** If `pg_stat_statements` is already installed/visible, inspect bounded normalized `queryid` counters and timings; never enable/reset it or expose query text. Timestamp snapshots because restarts/resets change meaning.
10. **Compare and classify.**
    - Compare one dimension across matched fingerprints/windows: role, schema, release, plan, parameter class, traffic, or endpoint.
    - Separate server time from pool/network/ORM/retry time; report **Confirmed**, **Probable**, or **Unknown** and stop.

## Fast Signals

- Wrong rows: SQL + typed binds + snapshot + role/RLS + schema/timezone/collation + route.
- Error: original SQLSTATE/detail/constraint + server log; unwrap client/ORM/retry failures.
- Slow/hang: matched workload + plain plan + estimates/stats age + wait edge + pool/resource window.
- Connection/replica: endpoint/database/role/TLS-auth evidence + pool limits; recovery/replay state + commit/read timestamps.

## Guardrails

- No writes/DDL, suspect execution, explicit locks, transaction/role/session changes, backend cancel/terminate, or privilege/RLS bypass.
- No `ANALYZE`, `VACUUM`, `REINDEX`, extension/config/pool/replication/routing/failover changes, stats reset, or production mutation.
- Bound activity, locks, catalogs, statistics, logs, and table reads to named objects/PIDs/windows; never reproduce waits with `LOCK`.
- Treat hidden activity, denied fields, missing logs/extensions, counter resets, and absent runtime plans as evidence gaps.

## Official Anchors

- [EXPLAIN](https://www.postgresql.org/docs/current/sql-explain.html)
- [Statistics views](https://www.postgresql.org/docs/current/monitoring-stats.html)
- [Locks](https://www.postgresql.org/docs/current/view-pg-locks.html)
- [Replication monitoring](https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION-MONITORING)
