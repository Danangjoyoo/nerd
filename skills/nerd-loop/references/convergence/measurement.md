# Convergence: Measurement

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

## Contents

- [Operational Model](#operational-model)
- [Preserve the criterion vector](#preserve-the-criterion-vector)
- [Track best-so-far separately](#track-best-so-far-separately)
- [Measure progress over a window](#measure-progress-over-a-window)
- [What to Measure](#what-to-measure)

## Operational Model

For iteration `t`, record:

- `x_t`: current artifact and relevant environment state.
- `h`: immutable common admission hash for this loop contract.
- `a_t`: action and strategy used.
- `e_t`: verifier evidence, exact DoD/artifact binding, authenticated observed
  verdict, and freshness.
- `c_t`: DoD criterion status vector using `PASS | FAIL | UNKNOWN | ERROR`,
  derived from those authenticated verdicts.
- `g_i(t)`: nonnegative gap for criterion `i`, where zero means the criterion passes.
- `u_t`: uncertainty or variability of noisy evidence.
- `k_t`: cumulative time, cost, tokens, tool calls, and risk exposure.
- `b_t`: authenticated cumulative active-budget revision; remaining iterations
  are derived from its committed consumption records.

### Preserve the criterion vector

Never allow a high score on one mandatory criterion to compensate for failure on another. Completion is a conjunction:

```text
done_t = every mandatory c_i(t) is PASS
         and all evidence is fresh
         and parent integration passes
         and every required exact-hash owner decision is APPROVED
```

Use a scalar residual only as a navigation and diagnosis aid. When meaningful normalization exists, define:

```text
R_t = max_i g_i(t)
```

The maximum keeps the worst mandatory gap visible. If criteria cannot be honestly normalized, retain the vector and compare it by priority or Pareto improvement instead of inventing weights.

Typical gap encodings are:

- Binary requirement: `0` for pass and `1` for fail.
- Upper limit `y <= threshold`: scale `max(0, y - threshold)` by a declared meaningful unit.
- Lower limit `y >= threshold`: scale `max(0, threshold - y)` similarly.
- Rubric: measure distance below the accepted anchored score.
- Human judgment: keep `UNKNOWN` until the named acceptance owner decides; do not manufacture a number.
- Verifier failure: keep `ERROR` until the measurement path is repaired; do not reinterpret it as a task failure or pass.

### Track best-so-far separately

The latest state is not necessarily the best state. Preserve:

```text
B_t = best verified residual or criterion vector seen through iteration t
```

Checkpoint the corresponding artifact and evidence. Compare progress against `B_t`, and roll back to it after a regression when authorized.

### Measure progress over a window

For a normalized scalar residual and window `W`, a simple best-so-far improvement is:

```text
progress_W(t) = B_(t-W) - B_t
```

Optionally scale it relative to `max(abs(B_(t-W)), scale_floor)`. Declare both absolute and relative tolerances so behavior near zero remains meaningful.

An empirical contraction ratio can diagnose a regular numerical loop:

```text
q_hat = median(R_j / R_(j-1)) over a recent valid window
```

- Persistent `0 < q_hat < 1` suggests geometric reduction.
- `q_hat` near `1` suggests a plateau.
- `q_hat > 1` suggests divergence.

Do not treat this as proof for an agent loop. Its strategy, prompt, tools, and environment can change between iterations, so it is rarely one fixed contraction mapping.
## What to Measure

Select the smallest credible portfolio. No single signal works for every task.

| Signal | What it reveals | Main limitation |
| --- | --- | --- |
| DoD pass vector | Direct target attainment | Only as complete and trustworthy as the DoD and verifiers |
| Criterion residuals | Which mandatory gaps remain and their magnitude | Some qualitative criteria have no honest numeric scale |
| Best-so-far improvement | Whether the loop has produced a materially better valid state | Can hide recent regression if current state is not also shown |
| Trend or slope | Direction and rate of change over a window | Sensitive to window choice, nonlinearity, and outliers |
| EWMA or CUSUM | Small drift or sustained changes in noisy measurements | Requires a baseline and noise assumptions |
| Artifact delta | Whether files, output, or state are still changing | Small change does not imply correctness; large change does not imply progress |
| Semantic delta | Whether meaning is still changing despite textual edits | Embeddings can miss task-critical details and domain constraints |
| Action/strategy novelty | Whether the loop is exploring materially different approaches | Novel activity can still be unproductive |
| Failure fingerprint | Whether the same causal failure is recurring | Fingerprints require normalization to ignore incidental differences |
| Cycle signature | Repeated states, A/B alternation, or criterion pass/fail cycling | Approximate cycles need task-specific similarity rules |
| Regression count and severity | Whether new work damages previously passing criteria | Depends on rerunning affected evidence |
| Verifier variance or flakiness | Whether apparent progress is distinguishable from noise | More samples cost time and may still share bias |
| Cross-run or reviewer agreement | Whether independent paths reach compatible conclusions | Agreement can reflect shared blind spots |
| Held-out or parent validation | Whether visible-loop optimization generalizes | Expensive; repeated exposure destroys independence |
| Marginal gain per cost | Whether another iteration is economically justified | Expected gain is uncertain and cannot waive mandatory DoD criteria |
| Evidence coverage and freshness | Whether observed dimensions represent current state | Uninstrumented requirements remain unknown |

Convergence is observable only on instrumented dimensions. If a required property has no verifier, probe, or named human gate, record it as `UNKNOWN`; the loop cannot honestly determine convergence on that property.

Bind every label other than `NOT_ASSESSED` to the exact comparable evidence
window and threshold revision that produced it. Bind the “another cycle has
positive value” decision to its own evidence as well; the label and value
judgment are different claims. A caller-provided adjective or Boolean with no
trace reference is not a convergence observation.
