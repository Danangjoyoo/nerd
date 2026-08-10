# Convergence: Thresholds

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

## Calibrating Thresholds

There are no universal convergence thresholds. Derive them in this order:

1. User or specification acceptance thresholds.
2. Mandatory standards and parent-loop constraints.
3. Measurement resolution, natural variability, and verifier error.
4. Consequences of false acceptance and false rejection.
5. Expected improvement rate and delayed effects.
6. Cost, time, risk, and reversibility of another iteration.

Define these parameters before execution:

- **Scale:** Unit used to normalize each numeric gap.
- **Minimum meaningful improvement:** Smallest change worth distinguishing from noise or trivial edits.
- **Grace period:** Minimum evidence history before plateau detection is allowed.
- **Patience window:** Consecutive or rolling history required before a low-progress diagnosis.
- **Confirmation window:** Repetitions or dwell time required after entering the target region.
- **Cycle similarity and period:** What counts as the same state and which periods are checked.
- **Divergence tolerance:** Worsening that triggers rollback or reframe.
- **Confidence rule:** Sample count, confidence sequence, repeated run, independent reviewer, or human approval.
- **Budget:** Hard limits that bound execution even if no detector fires.

A practical plateau rule is:

```text
after the grace period,
if best improvement over W valid observations
<= absolute_tolerance + relative_tolerance * reference_scale,
then classify PLATEAUED
```

If a trustworthy lower or upper bound on the best possible remaining result exists, an authorized optimality-gap tolerance can justify a stronger stop. Without such a bound, `minimum improvement + patience` establishes only an empirical plateau: it does not prove correctness, global optimality, or proximity to the DoD.

A bounded, strictly decreasing ranking measure can prove that a deterministic loop terminates. It does not prove that the loop's terminal state satisfies its postconditions; keep the DoD check separate.

Use a robust statistic or control chart when evidence is noisy. Ordinary fixed-sample confidence intervals are unsafe when repeatedly inspected until one happens to pass; use a predeclared sampling plan or an anytime-valid sequential method.

Version every threshold. Do not relax it because the current result failed. Obtain the same authority required for changing the associated DoD criterion.
