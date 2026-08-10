# Convergence: Research

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Convergence router](index.md) and load it only for its named trigger.

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
