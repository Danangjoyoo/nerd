# Redis Review

- **Use:** Redis cache/coordination/queue/session/data boundary; preserve version,
  topology, client, key schema, serialization, and durability role.
- **Level 1:** Check command/key type, reply, TTL, slots, encoding, collisions,
  missing keys, atomicity, retries, locks, scans, growth, blocking, and hot keys.
- **Level 2:** Match naming, serialization, TTL, client, errors, metrics, and
  cleanup; test expiry, compatibility, concurrency, retry, eviction, and fallback.
- **Level 3:** Define Redis role; check invalidation ownership, fencing, cluster
  design, cardinality, fallback load, and hidden atomicity.
- **Proof:** Prefer source, tests, fixtures, and sanitized traces.
- **Escalate:** Tenant collision, coordination loss, unbounded memory, data
  corruption, unsafe locks, or fallback outage.
- **Avoid:** Shared/live commands, key scans, scripts, config/data mutation, and key style.

