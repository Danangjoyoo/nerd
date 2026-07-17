# Claude Fable + Sonnet One-Case Pilot Prompt

Paste everything below into one Claude Code session opened at the Nerd repository root.

---

You are the benchmark operator for `/Users/danangjoyo.agus/work/playground/mensa`.

Complete only the missing Claude Fable 5 xhigh and Claude Sonnet 5 xhigh pilots. Each target must run exactly one case from each of the four comparisons, one repetition, and two paired arms: 8 candidate runs followed by 4 blinded judge tasks and 8 scores.

This is a direct release run. Do not use the smoke mode or the existing 156-run configs directly.

## Hard scope

- Fable base config: `benchmarks/configs/claude-fable-5-xhigh.json`
- Sonnet base config: `benchmarks/configs/claude-sonnet-5-xhigh.json`
- Exact models: `claude-fable-5` and `claude-sonnet-5`
- Exact effort: `xhigh` for both
- Exact selected cases:
  - `smart-ambiguous-focus`
  - `surgery-trace-source`
  - `execute-blocker`
  - `silent-final-only`
- Run Fable and Sonnet in two parallel workers only.
- Make one paid attempt per target. Never retry automatically.
- Do not resume or merge any older partial result directory.
- Do not run Opus, Haiku, or any GPT target.
- Do not modify skills, the harness, original cases, original configs, README, Git history, remotes, tags, or published packages.
- Do not commit, push, tag, publish, or use `--latest`.

## Preflight

Read `AGENTS.md` and obey its repository command rules. Record:

```bash
rtk git rev-parse HEAD
rtk git status --short
rtk claude --version
rtk claude auth status
rtk codex --version
rtk codex login status
rtk python3 --version
```

Confirm no Fable or Sonnet benchmark process is active. If one exists, stop and report it; do not start overlapping work.

Run the deterministic checks before paid calls:

```bash
rtk python3 -m compileall -q scripts benchmarks tests
rtk python3 -m unittest discover -s tests -v
rtk python3 scripts/validate_skills.py
```

Stop before paid calls if any check fails. Do not reset or discard existing changes or evidence.

## Create isolated direct-run inputs

Create only these three untracked files:

```text
benchmarks/pilots/fable-sonnet-one-case/cases.json
benchmarks/pilots/fable-sonnet-one-case/claude-fable-5-xhigh.json
benchmarks/pilots/fable-sonnet-one-case/claude-sonnet-5-xhigh.json
```

`cases.json` must have the repository's existing `{ "cases": [...] }` schema and contain byte-for-byte copies of only the four selected case objects from:

- `benchmarks/cases/smart.json`
- `benchmarks/cases/surgery.json`
- `benchmarks/cases/execute.json`
- `benchmarks/cases/silent.json`

Create each pilot config by copying its base config and changing only:

```json
{
  "case_files": [
    "benchmarks/pilots/fable-sonnet-one-case/cases.json"
  ],
  "repetitions": 1
}
```

Keep the original target ID, model, xhigh effort, judge, conditions, seed, upstream pins, timeouts, and every other field unchanged. Do not modify the two base configs.

Validate both derived configs:

```bash
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/fable-sonnet-one-case/claude-fable-5-xhigh.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/fable-sonnet-one-case/claude-sonnet-5-xhigh.json
```

The final line of each command must be exactly `8 planned agent runs`. Stop without paid calls if either count differs.

## Parallel worker procedure

Each worker owns one config and must keep its candidate command alive until it finishes. Use the Claude Code background/long-running execution facility with at least a one-hour outer timeout; do not interrupt the command because it is quiet. The benchmark's own per-case timeouts remain authoritative.

Run the direct release once:

```bash
rtk python3 benchmarks/run.py run --config <PILOT_CONFIG> --release
```

The command must print its explicit result directory. Copy that exact path from stdout. If the runner exits before printing a path, report the target as blocked and stop that worker—do not infer a directory, resume, repair raw evidence, or retry.

Using only the explicit path printed by that worker, run:

```bash
rtk python3 benchmarks/run.py judge --config <PILOT_CONFIG> --results <EXACT_RESULT_PATH>
rtk python3 benchmarks/run.py score --config <PILOT_CONFIG> --results <EXACT_RESULT_PATH>
rtk python3 benchmarks/run.py report --results <EXACT_RESULT_PATH>
rtk python3 benchmarks/run.py report --results <EXACT_RESULT_PATH> --check
```

Never use `LATEST` or another worker's path.

## Acceptance checks

For each target require:

- `manifest.json`, `raw.jsonl`, `judges.jsonl`, `scores.jsonl`, `summary.json`, and `summary.md` exist.
- Manifest has `smoke: false` and `planned_runs: 8`.
- Raw has exactly 8 unique run IDs: four selected cases, one repetition, and both expected arms.
- Judges has exactly 4 unique task IDs.
- Scores has exactly 8 unique run IDs and all eight have valid judge evidence.
- Every candidate record has the exact target ID, requested Claude model, and xhigh effort.
- Every candidate exit is `0`; there are no timeouts, harness errors, or model substitutions.
- Both Silent arms have provider-reported output tokens.
- `report --check` succeeds without modifying derived evidence.

The expected publication state is `insufficient-data` because one paired sample per comparison is below Nerd's five-pair threshold. This is a minimal directional pilot; do not claim significance, a definitive winner, or publishable accuracy.

## Final response

Return only:

- Nerd commit and Claude/Codex CLI versions;
- exact status for Fable and Sonnet;
- exact config, result, and summary paths;
- raw/judge/score counts;
- model and effort verification;
- timeouts, nonzero exits, harness errors, invalid judges, and Silent token exclusions;
- confirmation that each target had at most one paid attempt;
- confirmation that no result was fabricated or merged from partial shards;
- confirmation that README, tracked source files, Git history, remotes, tags, and published packages were unchanged.
