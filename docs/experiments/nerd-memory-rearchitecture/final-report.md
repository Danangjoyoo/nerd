# Final Report

## Outcome

M3 is the best frozen behavioral checkpoint and verifier v4 is the best
evidence checkpoint. On the untouched holdout seeds `101`, `103`, and `107`,
H1–H6 passed their predeclared POC thresholds. H7 remains
`UNTESTED`: this simulator contains no faithful live-agent success, token, or
end-to-end latency measurement.

Parent integration invalidated the v1 completion claim because two passing
verification documents differed in noisy timing without a declared comparison
contract. Iteration 4 corrects that defect. Two fresh v2 runs now compare exact
deterministic evidence separately from bounded/toleranced runtime evidence.
Fresh integrated verification passes every mandatory criterion, and the
updated Nerd Loop terminal receipt is `DONE`. It binds correction admission
`sha256:cb56e2a32a9b9acfd7fb631a742a7121f952a35f753e9c2478004a1293527f1a`,
DoD `sha256:de60930f894557ef711f1d8f634096e95ad7b40435f27162391b4400ac0f0411`,
and verification-contract artifact
`sha256:03a38af27ea576c4d6d03f309ed9978b92a38f532ba5101569921455440aed4b`.

Iteration 005 then tested a Python-only shared-memory boundary with real fresh
subagents: one teacher recorded six verified opaque behaviors and three
consumers completed counterbalanced randomized task cards under different
repository labels. H8 passed every predeclared gate. This strengthens the case
for one user/host-local corpus with repository identity as provenance rather
than a storage partition, but it is not evidence that the installed Nerd
Memory runtime already behaves this way.

Iteration 006 added the requested matched comparison: one fresh teacher
recorded one verified opaque task procedure, then five independent rounds each
spawned one memory-enabled and one memory-blind fresh agent on identical input.
H9 passed every preregistered F1–F7 gate. Memory achieved `5/5` exact outputs
versus `0/5` for control, averaged `16.66 s` faster, and consumed `132.6` more
observable lexical-proxy tokens. The proxy is not billed model usage.

Two fresh verifier-v4 runs bind H8 and H9 into the exact evidence projection
and pass C1–C14 with deterministic digest
`sha256:4397fb54f7c3f14343e8275fe47f0e59858dfb8b6b265672fcfcb491c8773713`.
Their comparison-contract digest is
`sha256:b393608d9410c7e0bddaaa35e667c50931bb7a54130e2eba78eaab8b0b74ba03`.
The Nerd Loop receipt remains the historical iteration-004 L2 receipt; it is
not presented as an iteration-006 multi-agent receipt because that route would
require an authenticated L3 durable host adapter not supplied by this POC.

## Simulator holdout evidence

- Holdout digest: `sha256:015cdcf1279d08d0fc989b8c6cd8556d347556e97d5a75c1450b6ff34e10e533`
- Capture reconstruction: `1.0000`; persisted secret leaks: `0`.
- Tool/skill macro set-F1: `1.0000`; gain over best non-oracle baseline:
  `+0.2528`.
- Workflow edge-F1: `1.0000`; gain: `+0.3533`; mandatory-edge violations:
  `0%`.
- Invalid-output recall: `100%`; false rejection: `0%`; high-severity false
  acceptance: `0`.
- Unseen-repository action accuracy: `0.9583`; gain over B2: `+0.9583`;
  cross-context contamination: `0%`.
- Known / unknown abstention: `0% / 100%`.
- Obsolete usage after correction 1 / 2 / 3: `84.72% / 73.54% / 0%`.
- Two-run verifier evidence keeps each raw timing measurement. Both runs pass
  median `<5 ms` and p95 `<10 ms`; cross-run deltas pass
  `max(0.05 ms, 25% slower)`. The fresh raw values remain machine-readable in
  `results/iteration-004.json`. This is not H7 overhead evidence.

## Cross-agent evidence

- Teacher behaviors: `6`; consumers: `3`; known trials: `18`; unknown trials:
  `3`.
- Memory-on exact procedural success: `9/9`; memory-off exact procedural
  success: `0/9`; gain: `+100 percentage points`.
- Shared availability: `9/9`; cross-repository recall: `9/9`, represented in
  all three consumer repositories.
- Unknown-pattern abstention: `3/3`.
- Condition audit: all `12` memory-on trials queried exactly once, including
  unknowns; all `9` memory-off trials made zero queries.
- Secondary invalid-output diagnostic: `3/3` invalid signals rejected and
  `0/6` valid signals falsely rejected.
- SQLite storage-shape audit: no `namespace` table or column.
- H8 result digest:
  `sha256:1e317c5e3dc4001bf2be322ea0c26b02ff27b30acb2904af8df2ab18b0c5357d`.

## Paired-agent evidence

- Teacher: one exact verified procedure; consumers: five matched
  memory/control pairs and ten finalized submissions.
- Exact-output accuracy: memory `100%`; control `0%`; paired gain `+100 pp`.
- Leaf-level accuracy: memory `100%`; control `2.48%`; paired gain
  `+97.52 pp`.
- Mean wall time: memory `63.73 s`; control `80.39 s`; paired difference
  `-16.66 s`. Memory was `20.72%` faster on the mean and faster in `4/5`
  rounds.
- Mean observable lexical-token proxy: memory `878.2`; control `745.6`;
  paired difference `+132.6`. Memory used `17.78%` more on the mean and less
  in only `1/5` rounds.
- Condition audit: all five memory agents recalled exactly once; all five
  control agents made zero recalls; every pair had an identical input digest.
- H9 result digest:
  `sha256:03fdc50d5eba5dd7b1b057517bfbb9d137e1b62d930bdf2892e04bc0f074de62`.

The token proxy counts only the stored protocol, public card, retrieved advice,
and submitted answer. It excludes system/developer prompts, hidden reasoning,
tool traffic, and billed model tokens. The speed and token results are reported
measurements, not preregistered directional pass gates.

## Criterion vector

| Criterion | Fresh status |
| --- | --- |
| C1 Capture | PASS |
| C2 Selection | PASS |
| C3 Workflow | PASS |
| C4 Rejection | PASS |
| C5 Transfer | PASS |
| C6 Drift | PASS |
| C7 Abstention | PASS |
| C8 Exact deterministic projection | PASS |
| C9 Isolation and focused tests | PASS |
| C10 Bounded/toleranced runtime | PASS |
| C11 Artifact manifest | PASS |
| C12 H7 honesty | PASS |
| C13 Cross-agent H8 | PASS |
| C14 Paired-agent H9 | PASS |

## Convergence classification

The trace was `FALSE_CONVERGENCE` when parent integration exposed the missing
timing comparison contract after the original three learner iterations. The
single authorized correction iteration changed only reproducibility semantics.
It is now `SETTLING`: all deterministic projections compare exactly, runtime
passes its declared bounds/tolerance, 26 focused unit tests and all safety
probes pass, and the separately bounded H8 and H9 agent trials pass. H7 remains
explicitly unknown. This is not evidence of production convergence.

## Residual risks

1. Synthetic contexts and output signals are cleanly separable, producing
   ceiling scores that may not survive natural language, missing metadata, or
   tool-registry churn.
2. M3 is a composite intervention, so this experiment cannot attribute gains
   or regressions to verified-only admission, guard learning, abstention, or
   correction retirement independently.
3. Drift retirement is abrupt at the third contradiction; obsolete usage is
   still 73.54% after the second, which may be unacceptable for high-risk
   recommendations.
4. The global corpus is tested for contextual contamination, not malicious
   episode poisoning, identity collisions, concurrency, persistence, or data
   deletion semantics.
5. The `0.05 ms / 25%` repeat tolerance is a local POC noise policy, not a
   portable performance standard. The microbenchmark excludes model prompting,
   retrieval I/O, subagent scheduling, and token cost. H7 is therefore unknown.
6. Iteration 005 explicitly tells consumers whether recall is available, uses
   one host-local SQLite file and one seed, and scores exact stored procedures.
   It proves bounded sharing and usefulness, not automatic activation,
   cross-device availability, or semantic superiority over every reasonable
   memory-off procedure.
7. Iteration 006 uses one opaque procedure, one generator seed, one host, and
   agents that know their assigned arm. The control lacks the private procedure,
   exact scoring rejects contract-incompatible alternatives, and shared-start
   timing includes dispatch skew despite alternating spawn order.
8. Iteration 006's observable lexical-token proxy is not complete prompt usage
   or billed model telemetry. Its `+17.78%` mean result cannot establish H7's
   production token-overhead bound.

## Precise next experiment

Run a preregistered automatic-activation shadow trial through the real session
hook before changing the installed runtime:

- freeze at least 100 chronological tasks across several natural task families,
  at least 5 repositories, and at least 5 independent randomization seeds;
- remove the explicit `memory_enabled` flag from consumer prompts and let the
  hook detect whether recall is appropriate;
- compare memory-blind control, explicit Python recall, and automatic shadow
  recall without allowing shadow advice to mutate actions;
- reserve the last 20% of tasks and one entire repository as untouched
  holdouts;
- score top-1/top-3 tool and skill choice, workflow edges, invalid acceptance,
  abstention calibration, recall-trigger precision/recall, latency, and
  host-reported model tokens;
- advance to an installed-runtime migration only if automatic recall matches
  explicit recall on usefulness and passes every authority and contamination
  gate.
