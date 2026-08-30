# Behavioral Nerd Memory Rearchitecture POC

This directory is the single source of truth for an offline, deterministic
proof of concept for behavioral Nerd Memory. The POC asks whether a local
learner can turn verified chronological work episodes into useful advisory
predictions without treating memory as authority.

The experiment models this episode:

```text
context + sanitized command cues
  -> action
  -> skills and tools
  -> ordered steps
  -> output signals
  -> verification and user feedback
  -> eligible behavioral evidence
```

Current instructions, permissions, endpoint choice, and action authority are
deliberately outside the learner. Predictions are advisory and carry source
episode provenance.

## Scope

- Python standard library only.
- Synthetic, deterministic episodes; no raw transcripts or secrets persist.
- Chronological train/calibration/test partitions for development seeds.
- A separately invoked final gate over untouched holdout seeds.
- Three learner iterations plus one separately admitted verifier-contract
  correction iteration, one fresh-agent shared-memory integration trial, and
  one five-round paired memory/control replication.
- No changes to the existing `skills/nerd-memory` implementation.

H1 through H6 are testable by this POC. H7 requires production-faithful live
agent success, token, and end-to-end latency evidence and remains `UNTESTED`.
H8 tests bounded shared availability and usefulness through a Python-only
SQLite store and passed in iteration 005. H9 tests paired task advantage over
five matched memory/control rounds and passed in iteration 006. H9 reports a
declared lexical-token proxy; it does not turn H7 into a tested claim.

## Artifacts

- `architecture.md`: trust boundary, data contract, learner variants, and
  baselines.
- `hypotheses.md`: exact H1-H9 statements and operational measures.
- `experiment-plan.md`: splits, interventions, thresholds, and convergence.
- `poc/`: deterministic learner, fixtures, metrics, and runner.
- `tests/`: focused standard-library tests.
- `results/`: machine-readable iteration and final-gate evidence.
- `reports/`: one report for each bounded iteration.
- `final-report.md`: final criterion vector, best checkpoint, and next test.

## Reproduction

From this directory:

```bash
python3 -m unittest discover -s tests -v
python3 -m poc.runner --iteration 1 --output results/iteration-001.json
python3 -m poc.runner --iteration 2 --output results/iteration-002.json
python3 -m poc.runner --iteration 3 --output results/iteration-003.json
python3 -m poc.runner --final --output results/final-holdout.json
python3 -m poc.verify --output results/verification.json
python3 -m poc.verify --output results/verification-run-b.json
python3 -m poc.verify --compare results/verification.json results/verification-run-b.json --output results/iteration-004.json
python3 -m poc.loop_receipt --output results/loop-terminal.json
python3 -m poc.agent_experiment --db results/iteration-005/shared-memory.sqlite evaluate --experiment-dir results/iteration-005 --output results/iteration-005.json
python3 -m poc.paired_agent_experiment evaluate --db results/iteration-006/shared-memory.sqlite --experiment-dir results/iteration-006 --output results/iteration-006.json
```

Each verification run checks exact deterministic experiment evidence, runs
safety probes, and records a real 500-sample runtime measurement. The compare
command requires the deterministic projections to match exactly while checking
runtime under fixed 5/10 ms bounds and a repeat tolerance of
`max(0.05 ms, 25% of the slower measurement)`. The two raw verification JSON
files are expected to differ in their timing values. The receipt command
applies the admitted Nerd Loop completion expression. None of these commands
measures live model tokens or end-to-end agent latency.

Iteration 005 additionally contains the frozen teacher export, public cards,
hidden gold mapping, three consumer submissions, audited shared SQLite file,
and aggregate result. Re-evaluation is deterministic, but recreating the
submissions requires spawning fresh agents under the protocol in
`reports/iteration-005.md`.

Iteration 006 contains one verified teacher trace and five matched pairs of
fresh consumer submissions: one memory-enabled and one memory-blind agent per
round. Accuracy and recall isolation are exact evidence; speed is observed
wall time; token cost is the preregistered observable lexical proxy described
in `reports/iteration-006.md`, not actual model usage.
