# Redis Diagnosis

## Scope and provenance

- Use for an implicated Redis boundary; keep the active diagnosis-type reference authoritative.
- Record product/version, deployment, endpoint/node, environment/window, role, database, shard, and standalone/replication/Sentinel/Cluster mode.
- Record client/library, direct/proxy/discovery mode, TLS/DNS, pool limits, timeouts, retries, pipelines, transactions, scripts/functions, and release/config.
- Confirm endpoint, node role, and database before every check; unlike provenance is not comparable.
- Use established secrets and approved read-only access; record sanitized key namespace/fingerprint, never values.
- Official anchors: `INFO`, `ROLE`, `SLOWLOG`, `LATENCY`, `MEMORY`, `CLIENT`, Cluster, Sentinel, and key metadata commands.

## Diagnose

1. **Split latency:** capture pool wait, connect/TLS/DNS, command, decode, retry, and end-to-end time with the exact sanitized error.
2. **Bound the operation:** record command, key pattern/database, routed node, attempts, expected/actual result; use a non-production fixture when possible.
3. **Snapshot twice:** during symptom and at a comparable baseline; compare deltas/rates, not lifetime counters.

- Core snapshots: `INFO clients`, `INFO memory`, `INFO stats`, `INFO persistence`, `INFO replication`, and `ROLE`.
- Targeted counters: `INFO commandstats`, `INFO errorstats`, `INFO latencystats`, and `INFO keyspace`; missing fields are version/product evidence, not zero.

4. **Choose one branch:** inspect only evidence implicated by client timing, errors, snapshots, or topology.
5. **Correlate:** align application, Redis, host/container, storage, network, and failover evidence to one window.
6. **Classify:** apply the parent **Confirmed / Probable / Unknown** gate; one counter, node, or sample is not proof.

## High-signal branches

- **Type/TTL/encoding:** for known keys only, use `TYPE`, `PTTL`, `OBJECT ENCODING`, `MEMORY USAGE`, then type-specific cardinality (`STRLEN`/`LLEN`/`HLEN`/`SCARD`/`ZCARD`/`XLEN`).
- **TTL semantics:** `PTTL -2` means absent; `-1` means no expiry. Timestamp observations and exclude expiry, deletion, database/prefix drift, and failover before eviction.
- **Memory/eviction:** compare `INFO memory`, `MEMORY STATS`/`MEMORY DOCTOR`, policy/limit evidence, evictions/OOM, dataset, RSS, buffers, backlog, fork/COW, cgroup, swap, and fragmentation.
- **Latency:** use bounded `SLOWLOG GET 64`, `LATENCY LATEST`, command/latency stats, CPU, blocked clients, cardinality, persistence, and Lua/function duration.
- **Timing caveat:** Slow Log measures server execution, not pool, network, proxy, client I/O, decoding, or retry time.
- **Connections:** compare pool active/idle/waiters, acquisition, reconnects/rejections, `INFO clients`, `maxclients`, buffers, blocked state, and timeout owner.
- **Known client:** with authorization, prefer `CLIENT LIST ID <client-id>`; avoid fleet-wide enumeration.
- **Persistence:** align `INFO persistence`, logs, disk latency, loading, RDB/AOF status/rewrite, fork duration, and COW memory.
- **Replication/Cluster/Sentinel:** compare labeled `ROLE`, `INFO replication`, `CLUSTER INFO`, `CLUSTER SHARDS`, `SENTINEL MASTER <service-name>`, `SENTINEL REPLICAS <service-name>`, and `SENTINEL SENTINELS <service-name>` when supported.
- **Auth/network:** preserve redacted `NOAUTH`/`WRONGPASS`/`NOPERM`, TLS/DNS/reset/timeout errors; `ACL WHOAMI` may confirm identity when permitted.
- **Pub/Sub:** inspect subscription ownership, reconnect gaps, delivery contract, buffers, and publisher/subscriber timing; do not infer durable delivery.
- **Streams:** compare stream/group metadata, IDs, pending/claim state, consumer ownership, trimming, and retry timing without reading sensitive entries.
- **Lua/functions/transactions:** correlate blocking duration, error, `WATCH` conflicts, retries, idempotency, and pipeline head-of-line/buffer pressure.
- **Healthy Redis:** test wrong DB/prefix, codec drift, TTL units/defaults, stampede, stale discovery, retry amplification, races, or cache-aside semantics.

## Bounded discovery

- Prefer existing telemetry, redacted traces, and metadata for already-known keys.
- If explicitly authorized, bound namespace, calls, keys, time, and output; stop at budget even when cursor is nonzero.
- `SCAN 0 MATCH <narrow-pattern> COUNT 100 TYPE <type>`: `COUNT` is a work hint; results can be empty, oversized, duplicated, and non-snapshot.
- Never use `KEYS *`, fetch discovered values, or default to `--hotkeys`, `--bigkeys`, `--memkeys`, profiling, or `MONITOR`.

## Guardrails

- Obtain explicit production authorization; use least privilege and stop on unexpected load, latency, volume, or sensitive output.
- Never write/delete keys; change TTL/config/ACL; flush; kill clients; reset stats; purge memory; trigger persistence/failover; move slots; reshard; or run recovery.
- Never expose values, command arguments, credentials, connection strings, personal data, certificates, addresses, or client/key names; redact or hash identifiers.
- Treat `MONITOR`, broad scans, sampling/profiling, and fleet-wide enumeration as high-impact; require a duration/output budget.
- Stop after the parent confidence gate; repair requires a separately authorized Execute endpoint.
