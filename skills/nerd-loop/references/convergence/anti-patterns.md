# Convergence: Anti Patterns

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

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
