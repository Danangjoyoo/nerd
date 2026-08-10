# Convergence: Foundation

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

## Core Answer

Convergence is meaningful only relative to six declared things:

1. **State:** What changes from one iteration to the next.
2. **Target:** The Definition of Done (DoD) acceptance set.
3. **Gap or distance:** How unresolved criteria are represented.
4. **Observation:** Which verifiers expose the relevant state.
5. **Tolerance and confidence:** How close and how certain is sufficient.
6. **Window:** How much history is needed to distinguish a trend from noise.

Without these declarations, “the loop converged” is subjective. With them, convergence can be observed and operationally classified, although it may still be impossible to prove mathematically.

Use this governing rule:

> Convergence describes loop dynamics. The DoD determines success. Small changes, repeated answers, flat scores, agreement among agents, or an exhausted budget never establish completion by themselves.
## Working Definition

In mathematics, a sequence `x_0, x_1, ...` converges to `x*` under distance `d` when, for every positive tolerance, all sufficiently late states remain within that tolerance of `x*`.

A task rarely has one unique correct artifact. Define the acceptable target set instead:

```text
S_DoD = { x | every mandatory DoD criterion is satisfied by x }
```

The idealized task-loop statement is:

```text
distance(x_t, S_DoD) -> 0 as t -> infinity
```

Real task loops are finite, partially observed, and often stochastic. A finite trace usually cannot prove this asymptotic statement. It can support three narrower claims:

- **Successful completion:** Current, fresh evidence shows `x_t` is inside `S_DoD`.
- **Operational convergence:** Declared measurements show sustained movement toward `S_DoD` or settling within an authorized tolerance region.
- **Dynamic diagnosis:** The trace instead shows plateau, oscillation, divergence, noise, or repeated ineffective behavior.

Prefer the first claim whenever the DoD is directly decidable. A loop does not need to approach success asymptotically if it can reach and verify success in a finite iteration.
## Convergence, Completion, and Termination

Keep these terms separate:

| Term | Question answered | Can imply `done`? |
| --- | --- | --- |
| Completion | Does the current result satisfy every mandatory DoD criterion with fresh evidence? | Yes; this is the only success authority |
| Convergence | How is the result or its measured gap changing across iterations? | Only when the convergence target is the full DoD and the success rule passes |
| Stability | Has the measured state or score stopped changing materially? | No; a stable state can be wrong |
| Stationarity | Is there little detectable local improvement or gradient? | No; it may be a local optimum, constraint, or broken action space |
| Termination | Did execution stop for any reason? | No; termination includes success, limits, cancellation, failure, and blockers |
| Budget exhaustion | Was the allowed time, cost, token, tool, or iteration budget consumed? | Never by itself |

The two most important axes are **target attainment** and **dynamics**:

| Target status | Dynamic signal | Classification |
| --- | --- | --- |
| DoD passed | Any safe dynamic | `DONE`; further stability is required only when the DoD calls for confirmation or dwell time |
| DoD unmet | Gap decreasing materially | `PROGRESSING` |
| DoD unmet | Gap unchanged but material uncertainty shrinks | `LEARNING`; continue only toward a distinct evidence-backed intervention |
| DoD unmet | Little meaningful change | `PLATEAUED` or `PREMATURELY_CONVERGED` |
| DoD unmet | Prior states recur | `OSCILLATING` or `STUCK` |
| DoD unmet | Gap or regressions grow | `DIVERGING` |
| DoD unknown | Verifier results conflict or vary excessively | `INCONCLUSIVE` |

This is analogous to the statistical-process distinction between being stable and being capable: predictable output may still be outside its specification.
