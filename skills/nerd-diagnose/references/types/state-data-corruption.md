# State or Data Corruption

- Use when stored, cached, replicated, event-derived, or in-memory state violates one invariant, or readers disagree about one entity.
- Do not use for valid state rendered incorrectly, pure calculation errors, or transport failures outside a state boundary.

## Capture

- One falsifiable invariant, its scope, and expected value or shape.
- One entity/version, earliest known-valid observation, and first known-invalid observation.
- Source, observed time, event/transaction ID, writer/build/schema version, and exact read-only query or command.
- Raw encoding and decoded value only when safe; hash retained local copies.
- Distinguish source timestamps from collection time; a screenshot or current value alone is not causal evidence.

## Diagnose

1. **Prove the violation.** If no invariant can be stated, record the gap and apply the parent confidence gate.
2. **Preserve provenance.** Capture immutable, identity-linked snapshots before reasoning about mechanism.
3. **Locate the affected layer:**
   - Invalid authoritative storage → write, transformation, commit, migration, or replication path.
   - Valid storage but invalid application view → mapping, deserialization, cache, or presentation state.
   - Readers, primary/replica, or cache/store disagree → version, visibility, invalidation, lag, and serialization.
   - Valid history but invalid current state → adjacent versions, audit events, and writer deployments.
4. **Find the first bad boundary.** Trace decode → validation → transformation → write → commit → replication → cache → read → deserialization.
5. **Compare adjacent snapshots.** Identify the earliest boundary with valid input and invalid output; later readers are consequences.
6. **Test the mechanism against provenance:**
   - Concurrency/transaction: overlaps, lost update, non-atomic work, isolation anomaly, partial commit, lock/transaction ordering.
   - Retry/idempotency: duplicates, missing/reused key, ambiguous acknowledgement, replay, or out-of-order event IDs.
   - Schema/version: reader-writer mismatch, null/default coercion, precision/timezone loss, enum incompatibility, migration or mixed deployment.
   - Transformation/write: deterministic bad mapping, skipped validation, or an already-invalid write payload.
7. **Reject or preserve gaps.** Missing required signals defeat a hypothesis only when evidence is complete; otherwise name the missing artifact.
8. **Bound impact.** Derive the smallest cohort by writer, schema version, event range, partition, and time window.
9. **Estimate safely.** Prefer indexed counts, metrics, or audit metadata; report lower/upper bounds and assumptions. Stop before unbounded or sensitive reads.
10. **Classify and stop.** Report invariant, affected layer, first bad boundary, provenance, bounded impact, and next needed evidence; apply the parent confidence gate.

## Guardrails

- Diagnose only: never repair, normalize, delete, backfill, re-save, replay, or rewrite suspect data.
- Read-only first; scope production reads by identifier, partition, writer version, and smallest time window.
- Redact secrets and personal data; preserve access controls and avoid raw records in the diagnosis.
- Preserve originals. Use only sanitized, disposable local copies, hashes, or derived reports.
- Do not restore or test recovery in place. Inspect backup/recovery evidence read-only; use an isolated disposable copy only when already authorized.
- Never modify source, durable data, backups, infrastructure, or production.
