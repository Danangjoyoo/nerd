# Performance Regression

- Use when an operation is measurably slower or more resource-intensive than a comparable baseline.
- Route non-completion to hang/timeout, environment-only differences to environment mismatch, and upstream failures to integration/API.

## Capture

- Operation, workload shape, data volume, concurrency, cache state, background load.
- Runtime, configuration, hardware/limits, baseline and candidate revision or window.
- Metric, unit, scope, percentile, sample window, and absolute or relative threshold.
- Raw samples and distributions; retain sensitive profiles and payloads securely.
- If no comparable baseline exists, record the gap and apply the parent skill's confidence gate.

## Diagnose

1. **Reproduce the delta.** Run the same workload on baseline and candidate, preferably alternating order; match warmup and steady state.
2. **Measure variance.** Repeat enough runs; compare median and relevant tails such as p95/p99, not averages alone.
3. **Validate the harness.** Check throttling, noisy neighbors, background jobs, telemetry gaps, clocks, and harness overhead.
4. **Establish regression.** Require the delta to exceed both the declared threshold and normal run-to-run spread.
5. **Find the consumed budget.** Compare CPU versus wall time, allocation/GC, disk/database I/O, locks/queues, network/retries, and downstream time.
6. **Separate mechanisms.** Distinguish saturation—utilization, queue depth, throttling, wait—from higher service latency without saturation.
7. **Profile the implicated layer.** Sample first; instrument only when needed. Record profiler type, rate, scope, and overhead.
8. **Compare equivalent profiles.** Profile baseline and candidate identically; distrust hotspots that move when overhead changes materially.
9. **Account for the delta.** Rank changes in self/inclusive time, allocation, I/O, locks, queries, or network. High cost without baseline increase is not causal.
10. **Bound the window.** Correlate first-bad timing with code, dependency, runtime, configuration, data shape, infrastructure, and traffic changes.
11. **Discriminate one factor.** Use an existing revision, artifact, fixture, or isolated diagnostic setting; hold the measurement contract constant.
12. **Re-measure.** Require the suspected signal and end-to-end metric to change as predicted; timing correlation alone is only a lead.

## Evidence

- Workload contract and environment fingerprint.
- Sample count, distribution, threshold, and baseline/candidate delta.
- Profile overhead, attributed bottleneck, and how much of the end-to-end delta it explains.
- Regression window, candidate changes, one-factor comparison, and remaining evidence gap.
- Apply the parent skill's **Confirmed / Probable / Unknown** confidence gate.

## Guardrails

- Diagnose only: do not optimize, patch, tune, scale, roll back, change limits, clear caches, or rewrite queries.
- Do not edit source or mutate durable data, infrastructure, or production to manufacture confirmation.
- Disposable local profiles, traces, caches, or build output are allowed; remove nothing durable.
