# Convergence: Qualitative Patterns

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

## Qualitative and Subjective Tasks

Subjective does not mean unobservable. It means the acceptance function includes human judgment or a calibrated rubric.

Use one or more of:

- Anchored rubric levels with examples of pass, borderline, and fail.
- Pairwise comparison against a baseline or reference artifact.
- A named acceptance owner with explicit accept/reject authority.
- Representative user task completion, preference, or comprehension checks.
- Independent reviewers and an agreement rule when one reviewer is insufficient.
- Held-out examples to test whether repeated self-critique overfit visible feedback.

For qualitative work, track dimensions separately. A writing loop might measure factual accuracy, required coverage, clarity, audience fit, and stakeholder acceptance. Do not average away a factual failure with a high style score.

Semantic or textual stability can suggest saturation, but it may represent convergence toward the model's preferred wording rather than the user's target. Require the rubric or human gate to pass.

Convergence is “obvious” only when the target is direct, every material dimension is observable, the verifier is reliable, and the result lies clearly inside the acceptance boundary. Otherwise expose uncertainty instead of claiming obviousness.
## Task Patterns

### Deterministic code repair

- Target: regression test, affected suite, and integration DoD all pass.
- Progress: failing assertions or static errors decrease without new regressions.
- Stuck: the same normalized failure returns after a materially different repair.
- Done: fresh required checks pass; repeated identical patches or a submission marker are irrelevant.

### Performance or reliability

- Target: declared percentile or reliability threshold under a pinned workload and environment.
- Progress: confidence-aware movement of the target metric and no guardrail regression.
- Settling: threshold holds for the specified repetitions or duration.
- Plateau: best improvement is below measurement noise for the patience window.

### Design, writing, or policy

- Target: mandatory content and factual gates plus an anchored rubric and named acceptance owner.
- Progress: unresolved rubric dimensions close or reviewer objections are resolved.
- Premature convergence: wording stops changing while a mandatory objection remains.
- Done: acceptance is recorded; self-critique or semantic stability alone is insufficient.

### Research or exploration

- Target: agreed questions answered with required source quality, contradictions, uncertainty, and delivery format.
- Progress: material unknowns close or evidence changes the conclusion.
- Plateau: repeated searches yield no decision-relevant evidence after query/source diversification.
- Done: the research DoD passes, not merely because novelty has saturated.

### Open-ended search, testing, or fuzzing

- Target: a bounded coverage, risk, or evidence objective defined by the DoD.
- Progress: new relevant states, failures, coverage features, or counterexamples.
- Plateau: novelty rate falls below the declared threshold.
- Stop: budget or plateau reports residual risk; it does not prove defect absence.
