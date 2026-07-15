# Claude Model Benchmark Operator Prompt

Paste everything below into Claude Code from the Nerd repository root.

---

You are the benchmark operator for the Nerd repository at `/Users/danangjoyo.agus/work/playground/mensa`.

Run the repository's four Claude benchmark shards and return validated artifacts for later aggregation with GPT results. Use parallel subagents: one worker per target. Wait for every worker, then produce one index and a concise report.

## Exact targets

| Display | Config | Required model | Effort |
| --- | --- | --- | --- |
| Claude Fable 5 · xhigh | `benchmarks/configs/claude-fable-5-xhigh.json` | `claude-fable-5` | `xhigh` |
| Claude Opus 4.8 · xhigh | `benchmarks/configs/claude-opus-4-8-xhigh.json` | `claude-opus-4-8` | `xhigh` |
| Claude Sonnet 5 · xhigh | `benchmarks/configs/claude-sonnet-5-xhigh.json` | `claude-sonnet-5` | `xhigh` |
| Claude Haiku 4.5 | `benchmarks/configs/claude-haiku-4-5.json` | `claude-haiku-4-5` | configured default; do not add `xhigh` |

Do not silently substitute a model, alias, fallback, or effort. If an exact target is unavailable, record it as blocked and continue with the other targets.

## Metrics

Measure exactly these paired comparisons:

1. `nerd-smart` vs `superpowers-brainstorming`: mean accuracy score, accuracy pass rate, p50/p95 latency, paired score delta, and paired latency delta.
2. `nerd-surgery` vs `superpowers-systematic-debugging`: the same accuracy and latency metrics.
3. `nerd-execute` vs `superpowers-executing-plans`: the same accuracy and latency metrics.
4. `nerd-silent` vs `regular`: accuracy score/pass rate, p50/p95 latency, paired latency delta, eligible median output tokens, tokens saved, valid-pair counts, and every exclusion reason.

Each target config contains five cases, three repetitions, and 120 candidate agent runs. A complete target has 60 blinded judge tasks and 120 scored runs.

## Hard rules

- Read `AGENTS.md`, `docs/plans/2026-07-15-nerd-model-matrix.md`, and `docs/plans/2026-07-15-nerd-benchmarks.md` first.
- Use the committed configs and harness without changing them.
- Do not modify `README.md`, any skill, test, fixture, case, config, harness, or plan.
- Do not commit, push, tag, or publish anything.
- Do not fabricate, estimate, interpolate, or hand-repair evidence.
- Use synthetic fixtures only. Never expose hidden criteria to candidate agents.
- Keep the two arms of each pair sequential. The four target workers may run concurrently.
- Use the pinned Codex judge from each config. A tested Claude model must not judge itself.
- Treat `raw.jsonl` and `judges.jsonl` as append-only evidence.
- Preserve failures and timeouts. Report blockers and exclusions instead of naming an unsupported winner.
- During parallel execution, never use `--latest`; always pass the explicit result directory printed by `run`.
- Do not change Git state, remotes, tags, README, or published packages.

## Preflight

From the repository root, record:

```bash
git rev-parse HEAD
git status --short
claude --version
claude auth status
codex --version
codex login status
python3 --version
```

Then run:

```bash
python3 -m compileall -q scripts benchmarks tests
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
```

Stop before paid calls if these fail. Do not reset or discard user changes. Require no uncommitted changes under `skills/`, `benchmarks/nerdbench/`, `benchmarks/cases/`, `benchmarks/fixtures/`, or `benchmarks/configs/`.

For each config, require:

```bash
python3 benchmarks/run.py plan --config <CONFIG>
```

The last line must be `120 planned agent runs`.

## Per-target worker procedure

Use the worker's exact config path for every command.

First run a smoke gate:

```bash
SMOKE_RESULT="$(python3 benchmarks/run.py run --config <CONFIG> --smoke)"
python3 benchmarks/run.py judge --config <CONFIG> --results "$SMOKE_RESULT"
python3 benchmarks/run.py score --config <CONFIG> --results "$SMOKE_RESULT"
python3 benchmarks/run.py report --results "$SMOKE_RESULT"
python3 benchmarks/run.py report --results "$SMOKE_RESULT" --check
```

Require 8/8 raw runs, four blinded judge tasks, eight scores, exit code `0` for every candidate run, no harness errors, and provider-reported output tokens for both Silent arms. Smoke summaries must remain non-publishable.

Only after that target's smoke passes, run its release shard:

```bash
RESULT_DIR="$(python3 benchmarks/run.py run --config <CONFIG> --release)"
python3 benchmarks/run.py judge --config <CONFIG> --results "$RESULT_DIR"
python3 benchmarks/run.py score --config <CONFIG> --results "$RESULT_DIR"
python3 benchmarks/run.py report --results "$RESULT_DIR"
python3 benchmarks/run.py report --results "$RESULT_DIR" --check
```

If interrupted, resume only the exact native run ID—the final path component of `RESULT_DIR`:

```bash
python3 benchmarks/run.py run --config <CONFIG> --resume <RUN_ID>
```

Continue judging/scoring/reporting with the explicit `RESULT_DIR`; never use `LATEST`.

## Validate every release shard

For each target, verify:

- `manifest.json`, `raw.jsonl`, `judges.jsonl`, `scores.jsonl`, `summary.json`, and `summary.md` exist.
- `raw.jsonl` contains exactly 120 unique run IDs and `scores.jsonl` contains the same 120 IDs.
- `judges.jsonl` contains exactly 60 unique judge task IDs.
- Every record has the config's exact `target_id`, requested model, and reasoning effort.
- Claude `system/init` events report only the requested model; any resolved-model mismatch blocks the shard.
- Every case/target/repetition identity has both expected arms.
- The manifest records the exact Nerd commit, Superpowers commit/tag object, config, seed, agent version, model, and effort.
- `report --check` succeeds without changing the derived files.
- Silent token claims use provider-reported output tokens and the repository eligibility rule.
- Any insufficient comparison remains `insufficient-data`.

Audit shareable JSON/JSONL for credentials, authorization headers, secret-like values, and unrelated absolute paths. Never print a suspected secret. Quarantine the affected shard and report only its file and JSON field path; do not hand-edit raw evidence.

## Create the Claude index

Create `benchmarks/results/claude-model-matrix-<UTC>-index.json` containing only relative paths. Include:

```json
{
  "schema_version": 1,
  "suite": "nerd-claude-model-matrix",
  "nerd_commit": "<full SHA>",
  "upstream_commit": "<full SHA>",
  "runs": [
    {
      "target_id": "claude-fable-5-xhigh",
      "display_name": "Claude Fable 5 · xhigh",
      "agent": "claude",
      "model": "claude-fable-5",
      "reasoning_effort": "xhigh",
      "result_dir": "benchmarks/results/<run-id>",
      "summary": "benchmarks/results/<run-id>/summary.json",
      "publication_state": "<actual state>",
      "sha256": {
        "manifest.json": "<hash>",
        "raw.jsonl": "<hash>",
        "judges.jsonl": "<hash>",
        "scores.jsonl": "<hash>",
        "summary.json": "<hash>",
        "summary.md": "<hash>"
      }
    }
  ],
  "blocked": [
    {
      "target_id": "<blocked target>",
      "reason": "<concise evidence-backed blocker>"
    }
  ]
}
```

Add one `runs` entry per validated release shard and one `blocked` entry per unavailable target. Do not add hashes for blocked or quarantined evidence. Compute the index SHA-256 after writing it.

Do not create README charts. The Nerd operator will validate this index, combine it with GPT evidence, and render charts later.

## Final response

Return only:

- Nerd and Superpowers commits;
- Claude and Codex CLI versions;
- exact status for all four requested targets;
- explicit result and summary paths;
- raw/judge/score counts, publication states, timeouts, invalid pairs, token exclusions, and sanitization exclusions;
- Claude index path and SHA-256;
- confirmation that no number was fabricated;
- confirmation that tracked files, README, Git history, remotes, tags, and published packages were unchanged.
