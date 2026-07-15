# Nerd

[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml)

Focused operating skills for coding agents: think clearly, diagnose before fixing, audit with evidence, build against repository reality, and stay silent when narration adds no value.

## Install

```bash
npx skills add danangjoyoo/nerd
```

## Skills

| Skill | Description |
| --- | --- |
| `nerd-smart` | Aligns intention, endpoint, scope, and one working specialty before substantive work. |
| `nerd-surgery` | Diagnoses broken behavior from evidence and repairs only at an authorized execute endpoint. |
| `nerd-patrol` | Examines a confirmed security scope and reports only reachable, evidence-backed findings. |
| `nerd-execute` | Implements approved plans or confirmed small changes using repository patterns and fresh proof. |
| `nerd-silent` | Suppresses optional narration and effort while preserving correctness and the complete result. |

Smart routes one primary specialty; Silent composes with any active workflow. The Agent Skills layout supports Codex, Claude Code, and Cursor.

Nerd includes shortened internal knowledge derived from MIT-licensed Superpowers; see [third-party notices](THIRD_PARTY_NOTICES.md). Users do not need a separate Superpowers installation.

## Benchmarks

<!-- BENCHMARK_RUN:pending -->
<!-- BENCHMARK_RESULTS:START -->
Benchmark results pending a complete release run.
<!-- BENCHMARK_RESULTS:END -->

Method: paired same-agent/model runs, five cases per workflow, three repetitions, weighted accuracy rubrics with hard gates, latency excluding setup, and provider-reported output tokens. See the [benchmark plan](docs/plans/2026-07-15-nerd-benchmarks.md).

## Verify locally

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
python3 benchmarks/run.py plan --config benchmarks/config.json
```

Live release benchmarks invoke configured coding-agent CLIs and are not run in CI:

```bash
python3 benchmarks/run.py run --config benchmarks/config.json --release
```

MIT licensed. See [LICENSE](LICENSE).
