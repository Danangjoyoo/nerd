# Hypotheses

These statements preserve the brainstorm handoff exactly. Classification says
what this synthetic POC can establish; it does not weaken the hypothesis.

## POC-testable

### H1 — Capture

Event reconstruction is 100% correct and seeded secrets have 0 persisted
leakage.

Measure: exact canonical episode round-trip rate and exact/regex secret scan of
every serialized captured episode. Pass threshold: `1.00` reconstruction and
`0` leaked seeded secrets.

### H2 — Tool/skill selection

Contextual hybrid improves macro set-F1 by at least 0.08 over the best
non-oracle baseline.

Measure: average of per-episode tool set-F1 and skill set-F1 on chronological
test data, then on untouched holdout seeds. B3 is excluded from the comparison.

### H3 — Workflow

Learned DAG violates fewer than 5% of mandatory ordering edges and improves
edge-F1 by at least 0.10.

Measure: workflow edge-F1 and violated mandatory edges divided by all mandatory
edges. Improvement is against the best non-oracle baseline.

### H4 — Rejection

Invalid-output recall is at least 90% at no more than 2% false rejection, with
zero false acceptance on high-severity fixtures.

Measure: recall on invalid outputs, false-rejection rate on valid outputs, and
count of accepted invalid outputs whose severity is `high`.

### H5 — Global transfer

Context-aware global memory improves unseen-repository accuracy by at least
0.10 over hard repository partitioning while keeping cross-context
contamination below 2%.

Measure: exact action accuracy on an unseen repository and the fraction of
prediction provenance drawn from an incompatible language/surface/project
context.

### H6 — Drift

An obsolete recommendation falls below 10% usage within three new independently
verified contradictory episodes.

Measure: the obsolete recommendation's normalized support share after each
contradictory episode. Pass threshold after the third episode: `<0.10`.

## Future live-agent hypothesis

### H7 — Agent value

Memory-informed subagents improve verified task success by at least 10
percentage points without increasing invalid acceptance or adding more than
10% median runtime/token overhead.

Status in this POC: `UNTESTED`. Synthetic labels, local prediction latency, and
simulated cost cannot establish live task success, model token usage, or
end-to-end subagent overhead.

## Cross-agent Python POC hypothesis

### H8 — Shared availability and bounded usefulness

After one teacher agent records at least six independently verified opaque
behavior patterns, three fresh consumer agents operating under distinct
repository labels can retrieve the same shared Python POC memory without a
storage partition selector and improve exact task-pattern success by at least
50 percentage points over counterbalanced memory-off trials.

Mandatory supporting gates are shared recall accuracy `>=0.90`,
cross-repository recall `>=0.90` with all three consumers represented, unknown
pattern abstention `>=0.90`, exactly one memory query for every memory-on trial,
zero memory queries for memory-off trials, and no `namespace` table or column
in the experimental SQLite schema.

Classification: this can establish cross-agent availability and bounded
usefulness for the Python POC. It cannot establish that the installed Nerd
Memory runtime already has this architecture, nor can it complete H7's token
and end-to-end overhead gate.

Result: `PASS` in iteration 005. All predeclared E1–E8 gates passed; result
digest:
`sha256:1e317c5e3dc4001bf2be322ea0c26b02ff27b30acb2904af8df2ab18b0c5357d`.

### H9 — Five-round paired task advantage

After one fresh teacher completes and records a verified task procedure, five
fresh memory-enabled agents executing new instances of that task pattern will
achieve mean exact-output accuracy `>=0.80` and improve by at least `0.40` over
five matched memory-blind agents given the same inputs.

Every pair must use an identical input digest. Every memory agent must make
exactly one audited recall and every control agent must make zero recalls.
Accuracy is exact canonical JSON equality, supplemented by leaf-level accuracy.

Iteration 006 also measures arithmetic mean, median, and paired difference for
end-to-end wall time and an observable lexical-token proxy. The proxy counts
the stored task protocol, task card, retrieved advice, and submitted answer;
it excludes system/developer prompts, hidden reasoning, tool traffic, and
billed model tokens. No directional pass threshold is declared for time or the
token proxy—the experiment reports their observed cost rather than assuming
memory must reduce either.

Classification: H9 can establish a bounded paired advantage for the Python
POC. It cannot complete H7 because actual model token telemetry and the
installed automatic Nerd Memory path remain outside the experiment.

Result: `PASS` in iteration 006. Memory exact accuracy was `1.00`, control
exact accuracy was `0.00`, and paired exact gain was `+1.00` across five
rounds. Result digest:
`sha256:03fdc50d5eba5dd7b1b057517bfbb9d137e1b62d930bdf2892e04bc0f074de62`.
