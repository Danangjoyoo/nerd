# Convergence: Dynamics

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

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
