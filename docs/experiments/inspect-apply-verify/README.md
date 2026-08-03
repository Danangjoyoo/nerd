# Inspect and Apply/Verify Latency Experiment

This experiment compares local tool routes without an LLM, agent, prompt, or
Nerd skill.

## Comparisons

- `inspect`: persistent exact-symbol index versus one batched `rg` plus bounded
  file reads.
- `apply_verify`: one request that applies a unified patch and runs focused
  checks versus two requests using the same patch and check engine.

Both routes use the same persistent JSONL request/response transport. Fixture
setup and reset are outside timed regions. The primary result therefore
measures warm dispatch-to-decoded-response latency, not Codex's private built-in
tool transport.

## Run

```bash
rtk python3 docs/experiments/inspect-apply-verify/test_experiment.py -v
rtk python3 docs/experiments/inspect-apply-verify/bench.py
rtk python3 docs/experiments/inspect-apply-verify/bench.py --check
```

Raw paired samples are written to `results/raw.json`; the derived report is
written to `results/report.md`.

