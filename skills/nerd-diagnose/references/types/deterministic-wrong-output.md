# Deterministic Wrong Output

Scope: Use when one controlled input repeatedly completes with the same wrong value, document, response, or rendering; remap exceptions, timeouts, varying results, disputed expectations, or already-wrong input data.

## Capture

- Exact input and actual output, preserving meaningful bytes, types, order, precision, encoding, and metadata.
- Expected output from an authoritative contract, fixture, example, or independent calculation—not the suspected path.
- Smallest reproducer plus repeated outputs from the same entry point.
- Command, runtime/dependency versions, effective configuration, relevant state identity, locale/time zone, and flags.
- Boundary values, first violated invariant, and the suspected mechanism's predicted output.
- Sanitized evidence only; exclude secrets and personal data.

## Diagnose

1. **Fix the oracle.** Resolve expected versus actual before tracing.
   If expectations are ambiguous or contradictory, record the missing contract evidence and stop unknown.
2. **Prove determinism.** Repeat the smallest existing entry point while holding input,
   configuration, versions, state, locale/time zone, and flags fixed; capture commands and outputs.
   Remap varying output to intermittent/flaky and crashes or stalls to their symptom type.
3. **Minimize faithfully.** In a disposable local copy, remove one field, record, or operation at a time.
   Rerun the same assertion after every reduction and retain the last reproducer with the identical mismatch.
4. **Locate the first divergence.** Trace acquisition, parsing, normalization, state reads,
   domain transforms, adapters, and serialization/rendering. Use existing traces, a debugger,
   read-only queries, or a disposable harness to bisect boundary values against explicit invariants.
   Without an intermediate oracle, record the gap; the last observed component is not automatically causal.
5. **Challenge the boundary.** Verify its traced input, required state/configuration, and preconditions,
   then inspect the implementation and dependency/version actually loaded. Distinguish invalid upstream
   value, stale/unexpected state, environment selection, transform logic, and encoding/serialization.
6. **Seek causal evidence.** Predict the exact wrong value from one mechanism and compare it with capture.
   Use only an authorized, faithful read-only or disposable check that varies one diagnostic factor.
   Reject mechanisms that cannot explain the exact divergence; correlation or code suspicion is insufficient.

## Guardrails

- Keep one controlled symptom and one active hypothesis; preserve evidence gaps when a faithful check is unavailable.
- Do not modify source, durable data, infrastructure, or production; allow only read-only inspection or disposable local cache/build output.
- Stop at cause and evidence. Do not repair or prescribe an implementation change under Diagnose.
- Report the evidence and, when unresolved, exactly one highest-signal uncertainty check.
- Apply the parent Confirmed/Probable/Unknown gate.
