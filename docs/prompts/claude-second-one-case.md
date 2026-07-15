# Claude Second One-Case Pilot Operator Prompt

Paste everything below into one Claude Code session opened at the Nerd repository root.

---

You are the benchmark operator for `/Users/danangjoyo.agus/work/playground/mensa`.

Run the second one-case pilot for exactly four Claude targets. This pilot uses one new case per comparison, one repetition, and two paired arms: 8 candidate runs, 4 blinded judge tasks, and 8 scores per target.

## Exact targets

| Target | Config | Model | Effort |
| --- | --- | --- | --- |
| Claude Fable 5 | `benchmarks/pilots/second-one-case/claude-fable-5-xhigh.json` | `claude-fable-5` | `xhigh` |
| Claude Opus 4.8 | `benchmarks/pilots/second-one-case/claude-opus-4-8-xhigh.json` | `claude-opus-4-8` | `xhigh` |
| Claude Sonnet 5 | `benchmarks/pilots/second-one-case/claude-sonnet-5-xhigh.json` | `claude-sonnet-5` | `xhigh` |
| Claude Haiku 4.5 | `benchmarks/pilots/second-one-case/claude-haiku-4-5.json` | `claude-haiku-4-5` | configured default; do not add `xhigh` |

The selected cases are exactly:

- `smart-compound-queue`
- `surgery-component-boundary`
- `execute-written-plan`
- `silent-code-only`

## Hard rules

- Use four parallel workers, one target per worker.
- Use direct `--release` runs. Never use smoke mode.
- Make one paid attempt per target. Do not retry automatically.
- Do not resume, merge, modify, or infer evidence from an older result directory.
- Do not substitute a model, alias, fallback, effort, case, or config.
- Keep the two arms inside each target sequential; only the four targets run concurrently.
- Use the pinned Codex judge from each config. A tested Claude model must not judge itself.
- Do not use `--latest`; use each worker's explicit result path printed by `run`.
- Do not interrupt a quiet candidate process. Use background/long-running execution with at least a one-hour outer timeout.
- Preserve every timeout, nonzero exit, and harness error.
- Do not modify skills, the harness, cases, configs, tests, plans, README, Git history, remotes, tags, or published packages.
- Do not commit, push, tag, publish, fabricate, interpolate, or hand-repair evidence.

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

Confirm no benchmark runner is already active for any of the four exact Claude pilot configs. If overlap exists, stop before paid calls and report the matching process; do not launch a duplicate.

Run:

```bash
rtk python3 -m compileall -q scripts benchmarks tests
rtk python3 -m unittest discover -s tests -v
rtk python3 scripts/validate_skills.py
```

Stop before paid calls if any deterministic check fails. Do not reset or discard existing changes or evidence.

For each exact config, run:

```bash
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/second-one-case/claude-fable-5-xhigh.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/second-one-case/claude-opus-4-8-xhigh.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/second-one-case/claude-sonnet-5-xhigh.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/second-one-case/claude-haiku-4-5.json
```

The final line of every plan must be exactly `8 planned agent runs`. Stop without paid calls if any count differs.

## Parallel worker procedure

Each worker uses its assigned exact config for every command.

Run one direct release:

```bash
rtk python3 benchmarks/run.py run --config ASSIGNED_CONFIG --release
```

Keep this command alive until completion. It must print an explicit result directory. Copy that exact path from stdout.

If the runner exits before printing an explicit result path, preserve the partial directory, report the target as blocked, and stop that worker. Do not infer a path, resume, or retry.

Using only the explicit result path printed by that worker, run:

```bash
rtk python3 benchmarks/run.py judge --config ASSIGNED_CONFIG --results EXPLICIT_RESULT_PATH
rtk python3 benchmarks/run.py score --config ASSIGNED_CONFIG --results EXPLICIT_RESULT_PATH
rtk python3 benchmarks/run.py report --results EXPLICIT_RESULT_PATH
rtk python3 benchmarks/run.py report --results EXPLICIT_RESULT_PATH --check
```

Do not use `--latest`.

## Per-target verification

Require and report:

- Manifest has `smoke: false`, `planned_runs: 8`, `repetitions: 1`, and the exact second-pilot case file.
- `raw.jsonl` has exactly 8 raw records and 8 unique run IDs.
- The four exact cases each have both expected arms.
- `judges.jsonl` has exactly 4 unique judge task IDs.
- `scores.jsonl` has exactly 8 scores and 8 unique run IDs.
- Candidate and provider events resolve only to the requested model and effort.
- Every timeout, nonzero exit, harness error, invalid judge, and token exclusion is counted explicitly.
- Both Silent arms have provider-reported output tokens or a precise exclusion reason.
- `report --check` succeeds without changing derived files.

The expected publication state is `insufficient-data`: after this run, each individual shard still contains one paired observation per comparison. Do not claim significance or a definitive winner. Nerd will combine this second case with the first pilot only after independent verification.

## Final response

Return only:

- Nerd and Superpowers commits;
- Claude and Codex CLI versions;
- exact status for all four targets;
- worker task IDs;
- exact config, result, and summary paths;
- raw/judge/score counts;
- timeouts, nonzero exits, harness errors, invalid judges, model mismatches, and Silent token exclusions;
- confirmation that each target received one paid attempt;
- confirmation that no result was fabricated, repaired, resumed, or merged;
- confirmation that tracked files, README, Git history, remotes, tags, and published packages were unchanged.
