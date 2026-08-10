# Convergence in Task-Completion Loops

Use [the Nerd Loop Runtime Contract](runtime-contract.md) as the normative
source for closed criterion, dynamics, work-node, loop-phase, and terminal
vocabularies and for transition priority. This reference is a measurement and
diagnosis library. D0/L1 do not instantiate its full history model; L2 uses a
compact subset only when comparable cycles can change a decision; L3/L4 use a
full Convergence Contract when noise, subjectivity, or repeated dynamics make
it necessary.

## Contents

- [Core answer](#core-answer)
- [Working definition](#working-definition)
- [Convergence, completion, and termination](#convergence-completion-and-termination)
- [Operational model](#operational-model)
- [What to measure](#what-to-measure)
- [Observable convergence states](#observable-convergence-states)
- [Decision protocol](#decision-protocol)
- [Calibrating thresholds](#calibrating-thresholds)
- [Qualitative and subjective tasks](#qualitative-and-subjective-tasks)
- [Failure modes and anti-patterns](#failure-modes-and-anti-patterns)
- [Convergence Contract template](#convergence-contract-template)
- [Task patterns](#task-patterns)
- [Research basis](#research-basis)

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

## Observable Convergence States

Classify from declared rules, not intuition:

| State | Observable signs | Required response |
| --- | --- | --- |
| `NOT_ASSESSED` | Too few comparable observations exist, or a dynamics label cannot change the next decision | Use the DoD, distinct causal evidence, and hard budget without manufacturing a trend |
| `PROGRESSING` | At least one unresolved mandatory gap improves by the minimum meaningful amount over the window, with no unacceptable regression | Continue the current strategy while value exceeds cost and risk |
| `LEARNING` | A new counterexample, causal distinction, or measurement materially reduces uncertainty without yet reducing the target gap | Record the information and attempt a distinct intervention; do not count repeated rediscovery as progress |
| `SETTLING` | Result entered the allowed region but evidence is noisy, transient, or requires dwell time | Recheck for the declared confirmation window; do not mutate gratuitously |
| `PLATEAUED` | Best-so-far improvement stays below the meaningful threshold for the patience window while the DoD remains unmet | Reframe the representation, plan, action, or verifier; when no authorized proportionate cycle remains, return terminal `STOPPED` with reason `PLATEAU` |
| `PREMATURELY_CONVERGED` | Artifact and score changes are small, but mandatory gaps remain; strategy diversity has collapsed or held-out checks still fail | Restore the best checkpoint, diversify strategy, or seek missing judgment |
| `STUCK` | The same normalized action-error, action-observation, or failure fingerprint returns after a materially different strategy was attempted | Stop repeating; diagnose, escalate, or change the action space |
| `OSCILLATING` | A prior state or failure vector recurs periodically, adjacent updates remain material, or criteria alternate pass/fail | Diagnose conflicting constraints or coupled fixes; use joint integration or rollback |
| `DIVERGING` | Robust residual trend worsens beyond noise, regressions accumulate, or state/resource magnitude grows without compensating evidence | Stop or roll back; revisit assumptions, scale, and strategy |
| `INCONCLUSIVE` | Repeated verifier results conflict, confidence interval crosses the threshold, a verifier errors, or measurement integrity is suspect | Repair or repeat measurement; never convert uncertainty or infrastructure failure into pass |
| `FALSE_CONVERGENCE` | Visible metrics pass or stabilize while held-out, integration, or user validation fails | Repair the DoD or verifier model before further optimization |

`DONE`, `BLOCKED`, `EXHAUSTED`, and `STOPPED` are terminal outcomes, not
convergence states. Apply all terminal meanings and their priority from the
runtime contract after using this table to diagnose the trace. An inconclusive
trace returns `STOPPED/INCONCLUSIVE_TRACE` only after no credible repair or
measurement cycle remains; the diagnosis alone does not force termination.

Exact hashes are useful for exact repetition. For approximate behavior, normalize away timestamps, IDs, formatting, and other incidental differences, then compare:

- Artifact structure or semantic content.
- Active criterion and residual vector.
- Tool name, arguments, result, and error class.
- Strategy label and causal hypothesis.
- Environment and dependency state.

## Decision Protocol

Apply the runtime contract's one transition function after every verification
cycle so live execution, reporting, and replay cannot disagree. This
convergence-specific view preserves the same order:

1. **Honor hard interrupts.** Stop unsafe, unauthorized, or explicitly
   cancelled activity immediately.
2. **Reconcile first.** Resolve ambiguous effects, ownership, schema, and stale
   external state before interpreting measurements.
3. **Apply contract revisions.** Version current user or higher-authority
   changes and invalidate affected evidence.
4. **Validate and update measurement.** Confirm verifier scope, freshness,
   environment, skipped checks, and noise; then store the criterion vector,
   residuals, uncertainty, signatures, cost, and best checkpoint.
5. **Test the DoD.** Return `DONE` only when the canonical completion
   expression passes.
6. **Apply hard non-success conditions.** Return only the supported canonical
   terminal outcome. A limit cannot satisfy the DoD.
7. **Honor viable waiting.** If no work is ready and a registered condition and
   deadline can deliver the next evidence, pause without claiming that an
   active action has positive value.
8. **Diagnose dynamics.** Interpret inconsistency, divergence, cycles,
   repetition, regressions, and progress only with a valid declared window;
   otherwise remain `NOT_ASSESSED`.
9. **Choose the next edge.** From sorted unique ready IDs, select one stable
   focus, or retry measurement, roll back, change strategy, reframe, request
   judgment, or return the evidence-bound stop.
10. **Record why.** Bind the rule, evidence window, threshold version, and
   authority to the decision.

Keep a finite kill switch even when adaptive stopping is used. A maximum
iteration, cost, time, token, tool-call, or external-effect limit guarantees
bounded execution; it does not guarantee convergence or success. Carry it in
the common admission's authenticated cumulative budget state so a new decision
or reducer command cannot reset the count.

Before one more iteration, ask:

```text
Is there an authorized next action that has a credible chance of reducing a
mandatory gap or resolving material uncertainty, and is its expected value
proportionate to its cost and risk?
```

If no, do not repeat the same loop. Reframe, escalate, or stop.

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

## Failure Modes and Anti-Patterns

| Weak signal or rule | Why it fails | Stronger replacement |
| --- | --- | --- |
| “The output stopped changing” | Stable wrong answers exist | Check full DoD residuals and held-out or human validation |
| “The score stopped improving” | May be a plateau, noisy verifier, local optimum, or saturated proxy | Use a window, uncertainty, multiple signals, and a non-success plateau state |
| “The model says DONE” | Self-report is gameable and may not inspect current evidence | Use external, deterministic, independent, or named human verification |
| “All agents agree” | Shared prompts, models, context, and blind spots create correlated agreement | Diversify evidence and preserve a direct acceptance gate |
| “All visible tests pass” | The loop can overfit or omit integration behavior | Use traceability, affected integration, and held-out final checks |
| “No new bug was found” | Search saturation is not absence of defects | Report search budget, coverage, corpus growth, and residual risk |
| “The same result appeared three times” | Repetition can be a fixed wrong point | Compare repeated result with the target and failure vector |
| “Every iteration changed something” | Activity and novelty do not imply progress | Require meaningful criterion-gap reduction or verified information gain |
| “Average quality is high” | One mandatory failure can be hidden | Keep hard gates and the criterion vector |
| “The step size is tiny” | Action space may be constrained or the loop may be stuck | Pair artifact delta with residual, gradient/progress, and feasibility checks |
| “The maximum iteration count was reached” | This proves only bounded termination | Return `EXHAUSTED` with unmet criteria and best checkpoint |
| “Relax the tolerance until it passes” | Manufactures convergence by moving the target | Version the change and obtain acceptance authority |
| “One favorable noisy run passed” | Repeated peeking creates false confidence | Use confirmation, independent repetitions, or sequentially valid inference |
| “The child loops converged” | Local results may not compose | Run the parent's integration and acceptance rules |

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

## Research Basis

- [Fundamentals of Numerical Computation: fixed-point iteration](https://fncbook.com/fixed-point/): target-relative convergence, convergence rates, contraction conditions, and the warning that a finite sample does not by itself prove an infinite sequence's limit.
- [SciPy nonlinear least squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html): distinct objective-change, step-change, and gradient tolerances; typed termination reasons; and a separate success field.
- [PETSc KSP manual](https://petsc.org/main/manual/ksp/) and [convergence reasons](https://petsc.org/release/manualpages/KSP/KSPConvergedReason/): absolute/relative residual tests and explicit positive convergence versus negative divergence reasons.
- [NIST on stable but unacceptable processes](https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc15.htm): stability is predictability, not specification satisfaction.
- [NIST EWMA](https://itl.nist.gov/div898/handbook/mpc/section2/mpc2211.htm) and [CUSUM](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm): windowed monitoring for small shifts and drift in noisy processes.
- [Stan R-hat and effective sample size](https://mc-stan.org/rstan/reference/Rhat.html): compare within- and between-run behavior and measure effective evidence rather than trusting one trace.
- [Time-uniform confidence sequences](https://arxiv.org/abs/1810.08240): inference that remains valid under continuous monitoring and data-dependent stopping.
- [Z3 solver API](https://z3prover.github.io/api/html/ml/Z3.Solver.html): preserve a solver's explicit `unknown` result and reason instead of coercing uncertainty into success or failure.
- [Dafny termination metrics](https://dafny.org/dafny/DafnyRef/DafnyRef): a bounded, well-founded decreasing measure can prove termination, while termination still remains distinct from postcondition satisfaction.
- [TensorFlow EarlyStopping](https://www.tensorflow.org/api_docs/python/tf/keras/callbacks/EarlyStopping) and [scikit-learn early stopping](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html): baseline, tolerance, warm-up, patience, validation data, and best-state restoration patterns.
- [Microsoft Research on syntax-guided synthesis](https://www.microsoft.com/en-us/research/publication/syntax-guided-synthesis-2/): counterexample-guided candidate-verifier loops where new counterexamples constrain the next search rather than merely trigger an unchanged retry.
- [AutoGen termination conditions](https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/termination.html): stateful, composable success, handoff, external, time, token, and message stop conditions.
- [OpenHands Stuck Detector](https://docs.openhands.dev/sdk/guides/agent-stuck-detector): concrete repeated action-observation, repeated error, monologue, and alternating-pattern symptoms.
- [Self-Refine](https://selfrefine.info/): feedback-refine iteration with an explicitly task-dependent sufficiency function rather than one universal stopping rule.
- [SWE-agent trajectories](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/trajectories.md): preserve action-observation traces and exit statuses while keeping task evaluation as a separate step.
- [LLVM libFuzzer](https://llvm.org/docs/LibFuzzer.html): track corpus and coverage novelty, but distinguish finding a failure from ending because a time or run budget was reached.
- [Reflexion](https://arxiv.org/abs/2303.11366): evaluator feedback and bounded episodic lessons can improve later trials, but memory is not itself completion evidence.
- [Operational rationality and anytime algorithms](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1993/6276.html): model the tradeoff between result quality and computation cost.
- [Semantic early stopping for iterative LLM loops](https://arxiv.org/abs/2606.27009): emerging evidence for combining semantic-change patience with quality signals, while explicitly treating contraction as an empirical conjecture rather than an unsupported theorem.
- [When Agents Do Not Stop](https://arxiv.org/abs/2607.01641): recent static-analysis evidence that effective bounds must cover the actual feedback path, not merely appear near a loop.

Treat these sources as transferable patterns, not universal constants. Calibrate every convergence contract to the task's DoD, observability, noise, risk, and authorized cost.
