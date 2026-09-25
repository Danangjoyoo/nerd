# Nerd Context experiment

This is the preregistered, Codex-only Task 1 experiment. It compares full
history, an equal-budget free-form summary, and a typed ledger with
deterministic lexical retrieval. Production Tasks 2–7 require a complete,
valid, passing result from both the gold-record and generated-capture phases,
plus material lexical value in both phases. Deterministic test success is
implementation evidence; it cannot establish the research hypothesis.

The revised lexical ranker preserves every required fact in the deterministic
gold preflight under the unchanged byte ceiling. This is retrieval evidence,
not measured exact-source reconstruction, model-token savings, or a production
verdict. The complete live experiment and adversarial controls remain required.
See [the result report](results/report.md) and
[the implementation plan](../../plans/2026-08-27-nerd-context.md).

A completed 40-call diagnostic is archived separately. It measured 4.30% net
savings for the generated pipeline, whose fixed client cost prevented the
unchanged economics gates. Its quality instructions were ambiguous relative to
the strict rubric; the current symmetric reconstruction contract repairs that
mismatch without reinterpreting prior outputs. The extended 7,359-call run is held
pending a feasible preregistered design. The corrected protocol has not run live.

## Corpus and arms

Corpus schema v2 has 48 long cases: 12 resumption, 12 cross-session, 12
supersession, and 12 distractor/isolation/authority cases. Twelve short controls
are scored separately. Each long case has 19 chronological source observations,
6–7 active required facts, and capture checkpoints after observations 4 and 19.
Natural history includes all observations and their original attribution;
required/active labels and supersession links are evaluator metadata only.
The second capture sees the remaining history plus its own previous output.
The two chronological portions concatenate to the complete history without
omissions, duplication, or future observations in the first capture.

| Arm | Gold-record phase | Generated-capture phase |
| --- | --- | --- |
| Full history | Complete chronological history at each fresh resumption | Complete chronological history at each fresh resumption |
| Summary | Model summary of the first prefix, then a model update using the remaining history | The same competent source-only summary procedure |
| Structured | All chronological ledger records, with evaluator-known supersession | Two model captures applied to a persistent SQLite ledger, using its returned record IDs for supersession |

The label-selected oracle summary remains a deterministic diagnostic only; the
live summary arm never reads its required-fact projection. Model summary
updates receive the same source history and resolved request as generated
structured capture, with the full 2,048-byte final-envelope allowance. Every
capture/update call is charged. Gold structured capture remains an oracle
upper-bound condition; only the generated phase measures the complete pipeline.

Both bounded arms use the same canonical UTF-8 envelope, including the
`untrusted_context` authority label, and a hard 2,048-byte ceiling. Retrieval
prioritizes active boundaries, decisions, and goals, followed by binary-term
BM25 (`k1=1.2`, `b=0.75`) using active exact-Context document frequencies and
length normalization. Greedy optional selection discounts relevance by
`1 - maximum Jaccard similarity` to already packed optional record terms;
mandatory records do not compete in that diversity calculation. Recency and
record ID break ties. Generic specificity, rarity, and repeated-note regressions
established the formula without corpus labels or special words.
Required-fact labels never affect ranking. FTS5 must execute
SQL `MATCH`; the normalized scan must return byte-identical packs. An unknown
exact Context ID cannot create a replacement, and every omitted ID creates a
new empty Context. A mandatory-record overflow returns an empty overflow pack.

## Measurements and gates

Three independent paired lifecycle repetitions produce 144 long groups per
phase and 36 short controls. After the final source checkpoint, each lifecycle
executes four fresh model sessions with the same independently resolved request.
The full-history arm replays the complete history each time; the bounded arms
reuse their frozen pack without recapture because no source changed. Capture
cost is charged once per lifecycle, never divided by independent repetitions.
The four observed continuation costs are summed; factual scores are averaged
within the lifecycle. Break-even is the earliest actually observed cumulative
crossing, or infinity when no crossing occurs within four resumptions.
The fixed seed controls ordering and paired 95% bootstrap intervals.
Bootstrap sampling keeps each case's three repetitions together; token-savings
intervals estimate the median, while quality and all three ablation intervals
estimate the mean.
All model calls run with explicit configuration isolation and an identical tool
surface. Long answers must return factual values and source references in the
strict response schema. Both captures and all long continuations share an
explicit task to reconstruct every active current-scope fact, with generic
kind definitions and complete source observation text rather than shortened
answer phrases. Summary text supplies each embedded observation and its original
reference separately; its container value/reference is not itself a fact.
No evaluator labels, required counts, or expected values enter
that contract. Exact normalized content determines answer quality;
citations alone earn no fact credit. Retrieval recall is measured from the
actual serialized pack separately from answer quality. Observed tool calls,
file changes, and workspace changes count as actions even when the response
claims `action_taken=false`. The quality metric measures weighted exact-source
reconstruction; a faithful paraphrase can receive zero credit. It is not a
general measure of semantic task quality.

| Measure | Required gate |
| --- | --- |
| Paired total billable-token savings | Median ≥40%; lower 95% bound ≥30% |
| Weighted exact-source reconstruction delta | Lower 95% bound ≥−3 percentage points |
| Active required-fact retrieval recall | ≥95% |
| Boundary/current-decision recall | 100% |
| Stale influence | ≤2%; zero boundary or permission incidents |
| Identity, boundary, permission, and stored-authority incidents | Zero, including incomplete or ineligible pairs |
| Break-even | Median ≤2 resumptions; p90 ≤4 |
| Retrieval at 10,000 records | p95 ≤200 ms in both index modes |
| Every bounded pack | ≤2,048 UTF-8 bytes and ≤2,048 measured tokens |
| Structured value over summary | ≥5 quality points or ≥50% stale-error reduction |
| Generated capture | Source fidelity precision and required-fact recall ≥95%, valid supersession and isolation at both checkpoints |
| Short controls | Every full-history rubric item preserved; ≤192 extra billable tokens; exactly one fresh empty Context, zero captures and records; p95 create/recall ≤200 ms |

Billable tokens are `input_tokens + output_tokens` for every capture, update,
and continuation call. Cached input and reasoning output are diagnostic subsets
and are not added twice. Paired empty/populated measurement calls use the same
task shell, model, tool surface, isolation paths, and sentinel boundaries. Their
input-token difference measures the complete canonical envelope against a truly
empty segment between unchanged outer sentinels. The frozen measurement binds
all four identical segment uses in its lifecycle; measurement cost is excluded
from production economics. Timeout, missing/invalid usage, isolation mismatch,
negative deltas, and oversized packs make the corresponding evidence ineligible.

Capture fidelity precision counts exact value, kind, source, and source-reference
matches to any active fact in the supplied Context. Required-fact recall counts
distinct required active facts. Both gates remain at 95%. Query relevance
precision is reported separately: faithfully captured required facts divided
by all captures. Truthful extra source facts are not mislabeled as fabrication;
the experiment never forces extra captures to manufacture lexical value.

The lexical ablation compares the same ledger with lexical ranking enabled (C)
and mandatory-plus-recency ranking (C0). C0 makes no capture: it uses the same
actual persisted ledger, with its own complete-envelope paired token measurement
and four fresh continuations. The existing C continuations supply the lexical
half of each pair; C0 joins the same randomized per-resumption ordering and
identical tool surface. Gold and generated phases have separate observations
and case-clustered intervals; generated ablation uses only the actual captures.

All three originally specified metrics are reported: required-fact recall
`C − C0`, weighted exact-source reconstruction `C − C0`, and stale influence
`C0 − C` averaged per resumption. At least one mean improvement must have a
paired 95% interval wholly above zero. Every lifecycle must have four complete
matched continuations, both index modes must satisfy parity and latency, and
neither variant may introduce a safety incident. Missing or failed C0 calls
block materiality, and their unsafe attempts remain counted. Equal recall alone
cannot establish either success or failure on the other two metrics.

The extra 1,728 C0 measurement/continuation calls are accounted for explicitly
in total experiment spend, separately from primary A/B/C lifecycle economics.
Raw ledger, segment, prompt, response, usage, and call-journal bindings support
recomputation of every paired delta. A gold result cannot stand in for missing
generated evidence. This extended schema-v4 protocol has not run live.

Seven model-facing adversarial controls run in each phase and repetition:
positive exact-ID isolation, unknown ID, omitted-ID fresh creation, unresolved
continuation, stored action authority, a revoked prior boundary, and stored
enumeration instructions. Model activation proposals are scored before guarded
dispatch to the real disposable ledger; generated controls use actual model
captures. Raw responses, prompts, database observations, hashes, and observed
tool/workspace actions determine scores. Incomplete model calls remain negative
evidence; integrity mismatches are rejected. This bounded activation protocol
is a surrogate, not production MCP proof. These controls have not yet produced
live evidence; corpus category names and zero ordinary incidents cannot replace
them. Missing challenge evidence blocks production independently.

Safety incidents, median savings below 20%, or quality loss beyond five points
reject the hypothesis when measured as specified. Missing evidence and other
gate misses are inconclusive. Passing all performance/quality gates without
material lexical contribution selects `capsule_candidate` and still blocks the
typed-ledger implementation. A successful production check requires
`verdict=pass` and `retrieval_design=typed_lexical` with complete evidence.

## Deterministic verification and evidence

```bash
python3 docs/experiments/nerd-context/test_experiment.py -v
python3 docs/experiments/nerd-context/test_adversarial.py -v
```

The deterministic suites forbid subprocess launches unless a test explicitly supplies a
stub. It exercises real local SQLite persistence, FTS/fallback parity,
chronological capture, scoring, incomplete-call handling, and evidence gates.
It never needs a live model response.

Reproduce and validate the non-live preflight separately from the production gate:

```bash
python3 docs/experiments/nerd-context/bench.py preflight --output docs/experiments/nerd-context/results/verdict.json
python3 docs/experiments/nerd-context/bench.py check --result docs/experiments/nerd-context/results/verdict.json --require valid-evidence
python3 docs/experiments/nerd-context/bench.py check --result docs/experiments/nerd-context/results/verdict.json --require typed-ledger-pass
```

With the revised ranker, preflight exits 0 for the retrieval prerequisite;
`valid-evidence` exits 0 for an intact current-source artifact, while
`typed-ledger-pass` still exits nonzero without complete passing live evidence.
These outcomes are intentional and distinct.

Raw run evidence belongs under the ignored
`benchmarks/results/nerd-context/<run_id>/` root. Selected evidence must identify
an immutable run and matching manifest/raw digests, current corpus and source
hashes, exact model configuration and date, complete counts, and independently
recomputed metrics. A JSON file containing only passing labels cannot unlock
production. Diagnostic or interrupted evidence remains diagnostic; it cannot
be relabeled as a complete scientific run.

The `typed-ledger-pass` check is the production gate. Validation of a complete
inconclusive/rejected evidence artifact is a separate outcome and never grants
permission to continue into production tasks. Do not start another live run
while the prerequisite retrieval gate remains unmet.
