# Convergence: Template

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

## Convergence Contract Template

Create the full record for L3/L4 and for any lower-profile loop whose noisy,
subjective, or repeated comparable cycles need it. Keep it beside the DoD in
the selected Loop state. For ordinary L1, retain only criterion status,
residual uncertainty, a useful-next-cycle rule, and the hard budget; for L2,
add only the progress or repeated-failure rule that can alter the next action.

```markdown
## Convergence Contract — [Loop ID and name]

- **DoD version:** [Immutable reference]
- **Admission / budget:** [Admission hash; cumulative budget hash/revision]
- **State:** [Artifact and environment dimensions allowed to change]
- **Target set:** [Mandatory DoD criteria defining acceptable states]
- **Observable dimensions:** [Verifiers, probes, and human gates]
- **Unobservable / unknown dimensions:** [Anything that prevents a confident claim]

### Residuals and Success

| Criterion | Status / gap representation | Scale | Verifier | Confidence or approval rule |
| --- | --- | --- | --- | --- |
| DOD-1 | PASS / FAIL / UNKNOWN / ERROR or numeric gap | [Unit] | [Evidence] | [Rule] |

- **Success:** [All hard gates, freshness, integration, confirmation, and approval]
- **Best-state rule:** [How the best valid checkpoint is selected and restored]

### Progress and Dynamics

- **Minimum meaningful improvement:** [Absolute and relative values]
- **Grace period:** [Iterations or observations]
- **Patience window:** [Window and aggregation]
- **Artifact / semantic delta:** [Method and tolerance, if useful]
- **Plateau:** [Exact rule]
- **Stuck / repetition:** [Normalized fingerprint, threshold, and strategy-change rule]
- **Oscillation:** [Similarity, periods, and recurrence threshold]
- **Divergence:** [Trend, regression, or growth rule]
- **Noise / inconclusive:** [Variance, confidence, flakiness, and rerun policy]

### Responses and Limits

- **On progress / learning:** [Continue rule and required distinct intervention]
- **On settling:** [Confirmation without unnecessary mutation]
- **On plateau:** [Reframe, alternate strategy, human judgment, or stop]
- **On stuck / oscillation / divergence:** [Rollback and escalation]
- **Hard limits:** [Time, cost, tokens, iterations, calls, and external effects]
- **Decision priority:** [Safety/cancellation, measurement validity, success, hard non-success limits, dynamics]
- **Authority for changes:** [Who may change target, thresholds, or limits]

### Per-Iteration Trace

| Iteration | Criterion vector / residual | Evidence and uncertainty | Artifact / strategy signature | Best state | Cost | Classification | Next decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
```
