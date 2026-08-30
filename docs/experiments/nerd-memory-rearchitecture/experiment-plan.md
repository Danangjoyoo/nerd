# Experiment Plan

## Focus and causal question

Can verified behavioral episodes provide useful, context-sensitive workflow
advice while remaining non-authoritative, rejecting invalid outputs, adapting
to corrections, and abstaining outside evidence?

The learner experiment has three active iterations. Each changes one named
causal variable from the previous checkpoint. The third variable is a
predeclared composite evidence-admission policy; this design cannot attribute
effects to its internal guard, correction, drift, and abstention components.
Parent integration then exposed a verifier-contract defect and authorized one
separately admitted correction iteration, iteration 4.

## Data and partitions

- Development seeds: `11`, `17`, `23`.
- Untouched holdout seeds: `101`, `103`, `107`.
- Within each seed, episodes are ordered by sequence and split chronologically:
  first 60% train, next 20% calibration, final 20% test.
- Unseen-repository transfer fixtures use repository labels absent from train
  while preserving known non-repository contexts.
- Drift fixtures append exactly three independent, verified corrections after
  an established recommendation.
- Secret fixtures seed API keys, bearer tokens, passwords, and private-key
  material into raw capture inputs and scan the stored representation.

Holdout seeds are not used to choose features, thresholds, or reports for
iterations 1–3. They are evaluated once by `--final` after M3 and its thresholds
are frozen.

## Iterations

### Iteration 1 — Simple counts

- Control: B0–B3.
- Intervention: M1 enables simple count memory.
- Primary question: can capture and basic frequency learning run
  deterministically, and where do global counts fail?
- Expected disconfirmation: context-colliding actions produce tool/skill and
  workflow errors; invalid outputs are not yet rejected.

### Iteration 2 — Context-aware hybrid

- Control: frozen iteration-1 fixture generator and B0–B3.
- Intervention: only the prediction key/ranker changes from global action to
  action plus compatible context, with global cue transfer across repositories.
- Primary question: do H2, H3, and H5 cross their thresholds without context
  contamination?
- Expected disconfirmation: failure feedback, drift, unknown cues, and invalid
  outputs remain untreated.

### Iteration 3 — Refinement policy

- Control: frozen M2 representation and ranker.
- Intervention: evidence admission changes to the predeclared verified,
  correction-aware, guarded, abstaining policy.
- Primary question: do H4 and H6 pass while H2, H3, and H5 do not regress below
  threshold?
- Expected disconfirmation: the composite intervention cannot reveal which
  internal component caused a change.

### Iteration 4 — Reproducibility semantics

- Control: verification v1, whose raw JSON changed across correct runs because
  it mixed deterministic evidence with wall-clock timing.
- Intervention: only the verifier evidence contract changes. Functional and
  deterministic metric evidence receives an exact canonical projection;
  timing remains raw and must pass fixed bounds plus a declared two-run
  tolerance.
- Runtime bounds: 500 samples per run, median `<5 ms`, p95 `<10 ms`.
- Repeat tolerance: for each statistic, absolute delta must be no more than
  `max(0.05 ms, 25% of the slower measurement)`.
- Expected disconfirmation: complete verification JSON remains byte-different;
  claiming whole-document determinism is invalid.

### Iteration 5 — Fresh-agent shared-memory trial

- Control: counterbalanced task cards completed without querying behavioral
  memory.
- Intervention: the same opaque behavior families completed after advisory
  recall from one Python SQLite corpus populated by a separate teacher agent.
- Agents: one teacher followed by three fresh consumers with no inherited
  conversation turns. Consumers use distinct repository labels and never
  receive the teacher's behavior mappings in their task prompts.
- Fixtures: at least six arbitrary two-word markers whose actions, tools,
  ordered steps, skills, and invalid-output signals cannot be inferred from
  ordinary task semantics. Each behavior appears in memory-on and memory-off
  conditions across consumers; public cards omit gold answers.
- Randomization: fixed seed `505`, shuffled card order, and alternating
  counterbalanced condition assignment.
- Isolation: the Python POC uses a dedicated SQLite file. The store has no
  namespace selector, table, or column; repository labels exist only as
  source/consumer provenance. Every recall is audited by trial ID.
- Expected disconfirmation: successful retrieval without improvement over the
  memory-off condition proves sharing but not usefulness; repository-specific
  failures disprove global availability; memory-off queries invalidate the
  causal comparison.

Predeclared iteration-5 gates:

| Gate | Pass rule |
| --- | --- |
| E1 Teacher evidence | At least six verified teacher behaviors persisted |
| E2 Independent consumers | Exactly three fresh consumer submissions |
| E3 Shared availability | Correct behavior recall `>=0.90` on memory-on known trials |
| E4 Cross-repository reuse | Correct cross-repository recall `>=0.90` and represented in all three consumers |
| E5 Bounded usefulness | Exact success gain over memory-off `>=0.50` |
| E6 Abstention | Unknown-pattern abstention `>=0.90` |
| E7 Condition isolation | Every memory-on card queried exactly once; memory-off cards never queried |
| E8 Storage shape | No `namespace` table or column exists |

All E1–E8 must pass for H8. The trial remains a Python POC test even though
real subagents perform it; H7 stays open because installed-runtime behavior,
token overhead, and end-to-end latency are outside this intervention.

### Iteration 6 — Five paired task replications

- Teacher: one fresh agent receives a private deterministic procedure and one
  training fixture. Its output and behavior trace must pass a hidden verifier
  before the trace enters a new dedicated Python SQLite store.
- Consumers: five independent rounds. Every round spawns one memory-enabled
  agent and one memory-blind agent with no inherited conversation turns.
- Matching: both arms receive the same round input and base task card. Round
  inputs differ, but all are generated from seed `606` under the same procedure.
- Isolation: the memory arm must make exactly one audited recall. The control
  arm may not inspect the store, teacher trace, recall output, source, hidden
  gold, or another submission.
- Timing: a common wall-clock start is persisted immediately before each pair
  is spawned. Finalization stamps completion after the answer artifact exists.
  Spawn order alternates by round to reduce first-dispatch bias.
- Accuracy: canonical exact-output equality plus leaf-level path/value
  accuracy against hidden gold.
- Token proxy: lexical tokens from the stored arm protocol, public task card,
  retrieved advice for the memory arm, and submitted answer. This is explicitly
  not billed or full model-context usage.
- Aggregation: arithmetic mean, median, population standard deviation, and
  memory-minus-control paired differences across exactly five rounds.
- Expected disconfirmation: a recall audit failure invalidates the pair;
  memory exact accuracy below `0.80` or paired improvement below `0.40`
  disproves H9. Slower or larger memory trials remain valid measurements and
  must not be hidden by the accuracy result.

Predeclared iteration-6 gates:

| Gate | Pass rule |
| --- | --- |
| F1 Teacher verification | Teacher output is exact and one verified trace is recorded |
| F2 Replication completeness | Five rounds contain both finalized arms |
| F3 Matched inputs | Both arms use the same input digest in every round |
| F4 Recall isolation | Memory arms query once; controls query zero times |
| F5 Memory accuracy | Mean exact-output accuracy `>=0.80` |
| F6 Paired advantage | Mean memory-minus-control exact accuracy `>=0.40` |
| F7 Cost reporting | Mean, median, and paired differences exist for wall time and observable-token proxy |

All F1–F7 must pass for H9. Cost reporting is mandatory; lower cost is not.

## Metrics and thresholds

| Criterion | Mandatory POC pass rule | Verifier |
| --- | --- | --- |
| C1 Capture | Reconstruction `=1.00`; leaked seeded secrets `=0` | Capture round trip and persisted scan |
| C2 Selection | M2/M3 macro set-F1 gain over best B0–B2 `>=0.08` | Chronological test and final holdout |
| C3 Workflow | Mandatory-edge violation `<0.05`; edge-F1 gain `>=0.10` | DAG edge comparison |
| C4 Rejection | Recall `>=0.90`; false rejection `<=0.02`; severe false acceptance `=0` | Labeled output fixtures |
| C5 Transfer | Unseen-repository action gain over B2 `>=0.10`; contamination `<0.02` | Transfer fixtures and provenance audit |
| C6 Drift | Obsolete usage share after three corrections `<0.10` | Sequential correction probe |
| C7 Abstention | Unknown/ambiguous fixture abstention `>=0.90`; known-case abstention `<=0.05` | Calibration-selected threshold, test-only verdict |
| C8 Determinism | Two fresh runs have exactly equal deterministic projections and valid stored projection digests | v4 two-run comparison |
| C9 Isolation | Current explicit choices override advice; no authority field persists | Unit and schema tests |
| C10 Runtime | Both 500-sample runs satisfy median `<5 ms` and p95 `<10 ms`; each statistic's cross-run delta is `<= max(0.05 ms, 25% slower)` | `perf_counter_ns` plus v2 two-run comparison |
| C11 Reports | Six iteration reports and all machine-readable outputs exist | Manifest verification |
| C12 H7 honesty | H7 remains exactly `UNTESTED` | Final report inspection |
| C13 Cross-agent H8 | Iteration-5 result passes all predeclared E1–E8 gates | `results/iteration-005.json` inspection |
| C14 Paired-agent H9 | Iteration-6 result passes all predeclared F1–F7 gates | `results/iteration-006.json` inspection |

All C1–C14 are mandatory for POC `DONE`. C12 requires an honest non-result for
H7; it does not require H7 to pass.

## Convergence and stopping

The original fixed active budget was three learner iterations. Iteration 4 has
its own one-iteration correction admission, and iteration 5 is a separately
authorized cross-agent integration experiment. Scores do not compensate for a
failed mandatory criterion. M3 remains the best behavioral checkpoint;
verification v4 extends the corrected evidence checkpoint with frozen H8 and
H9 evidence.

Dynamics are classified over the learner result vectors and verifier evidence:

- `PROGRESSING`: at least one mandatory gap closes without reopening another.
- `LEARNING`: disconfirming evidence changes the next intervention.
- `SETTLING`: all POC gates pass and the remaining unknown is explicitly H7.
- `FALSE_CONVERGENCE`: aggregate scores look stable while any mandatory gate
  fails or H7 is presented as tested.

The v1 `DONE` was invalidated as `FALSE_CONVERGENCE` when two passing verifier
documents differed without a declared comparison contract. Iteration 4
returned the trace to `SETTLING` after exact comparison and the runtime policy
passed. Iteration 5 keeps that classification only if H8 and the new C13 gate
pass without presenting H7 as complete. Iteration 6 keeps it only if all five
pairs are complete, H9 passes, and the real-token limitation remains explicit.

Terminal `DONE` requires fresh unit tests, deterministic reruns, the untouched
holdout gate, report/manifest checks, and all C1–C14 passing. Otherwise the
terminal is a truthful non-success (`FAILED`, `EXHAUSTED`, or `STOPPED`) with
the failed criterion retained.

## Evidence and reproducibility

`results/iteration-001.json` through `iteration-003.json` record model, data,
metrics, hypotheses, and canonical digests. `results/iteration-004.json`
records the two-run verifier comparison and its stable contract digest. Each
matching report records hypothesis, artifact/data revision, seeds, control,
intervention, metrics, result, disconfirming evidence, decision, and next focus.

`results/final-holdout.json` is the only H1–H6 release verdict.
`results/verification.json` and `results/verification-run-b.json` retain real
timing measurements. Their v4 deterministic projections must compare exactly;
their timing values are compared only through the declared bounds/tolerance.
`results/iteration-005.json` is the H8 verdict and binds the teacher, public
cards, hidden gold, submissions, recall audit, and storage-shape evidence.
`results/iteration-006.json` is the H9 verdict and binds the verified teacher,
five matched input pairs, ten consumer submissions, recall isolation, timing,
and observable-token proxy evidence.
