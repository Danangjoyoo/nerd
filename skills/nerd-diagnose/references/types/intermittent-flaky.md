# Intermittent or Flaky

- Use when the identical intended workload sometimes passes and sometimes fails.
- Choose another type for deterministic failure, steady regression, or outcomes explained by different input/environment.

## Capture

- Exact command/input, revision, expected result, runtime/dependency versions, effective configuration, host/container identity, retry behavior.
- Per run: pass/fail, seed, order, start time, duration, load, concurrency, retry number, resources, dependency outcome, run ID.
- Observe the unmasked first attempt when scope-safe; never treat one pass as stability proof.

## Diagnose

1. Fix input, revision, and recorded conditions before comparing runs.
2. Establish frequency with identical repetitions: start with 20 or the repository repeat facility; report `failures / runs`.
3. Compare a failure with its nearest success; preserve the earliest divergent event, log, state read, request, scheduler transition, timeout, or resource signal.
4. If it does not reproduce, retry only in the reported context; then report the tested matrix and missing evidence.
5. Interleave baseline and variant runs to limit time drift; change exactly one factor per comparison.
6. Predict the signal and failure-rate change before each A/B check; reject the hypothesis when its discriminator does not move.
7. Apply the parent skill's confidence gate; report the controlled factor, mechanism or missing proof, matrix coverage, and earliest divergence.

## One-Factor Matrix

- **Seed/order:** fixed vs varied -> leaked state, shared fixture, nondeterministic iteration, or data dependence.
- **Concurrency/timing:** serial vs concurrent or controlled delay -> race, missing await/synchronization, scheduling, or timeout sensitivity.
- **Load/resources:** idle vs representative load with telemetry -> quota, pool, memory, CPU, I/O, or GC pressure.
- **Clock:** controlled time/window -> expiry, rollover, timezone, or skew.
- **Environment:** working vs failing fingerprint -> runtime, configuration, dependency, filesystem, locale, or platform.
- **External dependency:** authorized stable substitute/recording vs live -> network, upstream, retry, rate-limit, or consistency layer.

## Retain

- Exact reproducer; run count and `failures / runs` for every matrix cell; raw run IDs.
- Success/failure timeline through the earliest divergence.
- Environment/resource fingerprints and sanitized dependency responses.
- Hypothesis, prediction, observed result, classification, and missing confirmation.

## Guardrails

- Never label randomness as the cause, hide failure with retries, or infer cause from correlation alone.
- Use scope-safe, non-corrective checks; disposable local cache/build output is allowed.
- Get authorization before remote, load-generating, or production experiments.
- Diagnose only: do not change source, durable configuration/data, infrastructure, or production state.
