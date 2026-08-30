# Iteration 004 — Reproducibility Semantics

## Hypothesis

A verifier contract that compares deterministic functional/metric evidence
exactly, while evaluating real timing by predeclared bounds and tolerance, will
produce an honest repeatability verdict even though the complete verification
JSON documents remain different.

## Artifact and data revision

- Behavioral model: frozen `M3`; no learner or fixture change.
- Verifier schema: `behavioral-memory-verification/v2`.
- Deterministic evidence digest:
  `sha256:f50be1bb7444961712a8fb7228dce161eb17798c94a88ef1ba5c58b32ddfced2`.
- Verification-contract digest:
  `sha256:03a38af27ea576c4d6d03f309ed9978b92a38f532ba5101569921455440aed4b`.
- Development seeds: `11`, `17`, `23`; holdout seeds: `101`, `103`, `107`.
- Behavioral dataset and holdout artifact remain unchanged.

## Control and intervention

- Control: v1 emitted a passing document containing raw median/p95 timing but
  provided no semantic rule for comparing two such documents.
- Intervention: only reproducibility semantics change. V2 hashes an exact
  deterministic projection that excludes C10/timing, preserves raw timing,
  requires each 500-sample run to satisfy median `<5 ms` and p95 `<10 ms`, and
  limits each cross-run delta to
  `max(0.05 ms, 25% of the slower measurement)`.

## Evidence and metrics

| Measure | Run A | Run B | Comparison |
| --- | ---: | ---: | ---: |
| Deterministic evidence digest | `f50be1...fced2` | `f50be1...fced2` | exact |
| Median prediction | 0.016208 ms | 0.016250 ms | delta 0.000042 ms; allowed 0.05 ms |
| P95 prediction | 0.016375 ms | 0.016416 ms | delta 0.000041 ms; allowed 0.05 ms |
| Runtime bounds | PASS | PASS | PASS |
| Complete raw JSON equality | — | — | false, expected |
| C8 deterministic evidence | PASS | PASS | PASS |
| C10 runtime evidence | PASS | PASS | PASS |

The table records the iteration decision pair. The terminal verifier is rerun
after report integration; its raw timing may differ and is preserved in
`results/iteration-004.json` under the same unchanged policy.

Focused red/green coverage also proves that a bound failure cannot hide behind
tolerance, excessive timing drift fails even below the absolute bounds, and a
functional evidence difference fails exact comparison. H7 remains `UNTESTED`.

## Result and disconfirming evidence

The hypothesis is supported. Exact functional evidence and bounded noisy
evidence can coexist without fabricating timing determinism. The complete files
are still unequal, directly disconfirming the prior implicit whole-document
repeatability assumption. A tolerance pass establishes only local measurement
repeatability under this workload; it does not establish H7 latency/token
overhead or performance portability.

## Decision and next focus

Accept verifier v2 and invalidate the earlier convergence claim as
`FALSE_CONVERGENCE` at the point the defect was found. With two fresh v2 runs,
exact deterministic evidence, bounded timing, all mandatory criteria, and a
new Loop receipt passing, classify the corrected POC as `SETTLING` and stop.
The next experiment remains a preregistered real-session shadow ablation, not
another synthetic verifier iteration.
