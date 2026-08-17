# jOOQ Diagnosis

## Scope

- Use when jOOQ owns SQL construction, code generation, or execution.
- Pair with Java or Kotlin and the database reference; match one configuration because attached objects carry context.

## Capture

- jOOQ version/edition; database dialect/version; JDBC or R2DBC path; driver and endpoint.
- `DSLContext`/`Configuration` origin, `Settings`, connection/transaction providers, and listeners.
- Generated-code version, schema/catalog mapping, build artifact, exact command or request.
- Operation, expected/actual result, first exception, SQLState/vendor code, trace/request ID.
- Transaction state, timing split, fetched shape, and normalized query fingerprint.
- Bind type, nullability, and count; redact values.

## Diagnose

1. **Freeze one event**
   - Keep every observation tied to the same query, configuration, and transaction.
2. **Locate the first divergent phase**
   - Separate DSL construction, rendering, binding, connection acquisition, execution,
     fetching, conversion/mapping, listener behavior, and transaction completion.
   - Treat wrapper exceptions as location clues, not proof of query or database causality.
3. **Check rendered semantics**
   - Compare dialect, quoting/name mapping, statement type, parameter mode,
     converters/bindings, settings, and prepared SQL actually sent.
   - Do not replace prepared SQL evidence with inlined SQL; semantics may differ.
4. **Check generated-code provenance**
   - Match classes to generator/jOOQ version, schema snapshot, catalog/schema mapping,
     target package, classpath, and build artifact.
   - Distinguish stale generation, wrong schema, classpath skew, and runtime mapping.
   - Do not regenerate during diagnosis.
5. **Trace configuration and transactions**
   - Prove the executing `DSLContext`, connection, tenant/schema, listeners, scope, and async/nested context ownership.
6. **Use diagnostics conditionally**
   - Prefer existing sanitized telemetry and configured `ExecuteListener` evidence.
   - `LoggerListener` may expose SQL/binds/results; diagnostics adds overhead. Enable neither in production.
7. **Cross the database boundary**
   - Use its stack reference for plans, locks, statistics, permissions, and server state.
   - Rendered SQL alone does not prove database behavior; do not run suspect statements.
8. **Classify and stop**
   - Record the divergent phase, provenance, evidence, and gap; apply the parent confidence gate.

## Guardrails

- Do not change dialect/settings, listeners, transactions, schema, configuration, or data.
- Do not regenerate sources, inline binds, enable verbose logging, or execute suspect SQL.
- Redact SQL values, results, credentials, endpoints, schemas, and generated metadata.
- Allow disposable build output only when tracked generated sources cannot be overwritten.
- Stop at diagnosis; do not repair.

Official anchors: [bind values](https://www.jooq.org/doc/latest/manual/sql-building/bind-values/),
[execution logging](https://www.jooq.org/doc/latest/manual/sql-execution/logging/),
[diagnostics](https://www.jooq.org/doc/latest/manual/sql-execution/diagnostics/).
