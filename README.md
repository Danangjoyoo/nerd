# Nerd

![Nerd mascot banner](assets/nerd-banner.png)

[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml) [![skills.sh](https://skills.sh/b/danangjoyoo/nerd)](https://skills.sh/danangjoyoo/nerd)

Focused operating skills for coding agents: think clearly, diagnose before fixing, audit with evidence, build against repository reality, and stay silent when narration adds no value.

## Install

```bash
npx skills add danangjoyoo/nerd --global --agent claude-code --skill '*' --yes  # Claude Code
npx skills add danangjoyoo/nerd --global --agent codex --skill '*' --yes        # Codex
npx skills add danangjoyoo/nerd --global --agent cursor --skill '*' --yes       # Cursor
```

Or use the helper after cloning: `./scripts/install.sh {claude|codex|cursor|all}`.

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

Model preview from the current valid paired evidence:

### Accuracy

Representative rubric score per model. Higher is better; each block is 5 percentage points.

```text
================= Sol     =================
Nerd        [████████████████████] 100.0%
Superpowers [████████████████████] 100.0%

================= Terra   =================
Nerd        [████████████████████] 100.0%
Superpowers [██████░░░░░░░░░░░░░░]  30.0%

================= Luna    =================
Nerd        [████████████████████] 100.0%
Superpowers [█████████████░░░░░░░]  65.0%

================= GPT 5.5 =================
Nerd        [████████████████████] 100.0%
Superpowers [████████████████████] 100.0%

================= Opus    =================
Nerd        [████████████████████] 100.0%
Superpowers [█████████████░░░░░░░]  65.0%

================= Fable   =================
Nerd        [████████████████████] 100.0%
Superpowers [█████████████░░░░░░░]  65.0%

================= Sonnet  =================
Nerd        [████████████████████] 100.0%
Superpowers [█████████████░░░░░░░]  65.0%

================= Haiku   =================
Nerd        [████████████████████] 100.0%
Superpowers [██████░░░░░░░░░░░░░░]  30.0%
```

### Latency

Nerd Smart versus Superpowers Brainstorming per model, with no aggregation. GPT values use one new complex-case repetition; lower is better and all bars share a 0–180s scale.

```text
================= Sol     =================
Nerd        [█████████░░░░░░░░░░░]  82.9s
Superpowers [██████████░░░░░░░░░░]  89.9s

================= Terra   =================
Nerd        [█████████░░░░░░░░░░░]  78.8s
Superpowers [██████████░░░░░░░░░░]  88.7s

================= Luna    =================
Nerd        [███████░░░░░░░░░░░░░]  65.3s
Superpowers [█████████░░░░░░░░░░░]  84.4s

================= GPT 5.5 =================
Nerd        [█████░░░░░░░░░░░░░░░]  46.9s
Superpowers [████████░░░░░░░░░░░░]  72.1s

================= Opus    =================
Nerd        [████░░░░░░░░░░░░░░░░]  35.6s
Superpowers [█████████████░░░░░░░] 114.4s

================= Fable   =================
Nerd        [████████████░░░░░░░░] 109.9s
Superpowers [███████████░░░░░░░░░] 103.1s

================= Sonnet  =================
Nerd        [████░░░░░░░░░░░░░░░░]  32.5s
Superpowers [███████████████████░] 169.6s

================= Haiku   =================
Nerd        [███░░░░░░░░░░░░░░░░░]  30.6s
Superpowers [███░░░░░░░░░░░░░░░░░]  28.4s

```

### Token savings
All bars share a 0–60% scale.

```text
Sol      Nerd [███████████████████░] 55.9%
Terra    Nerd [██░░░░░░░░░░░░░░░░░░]  6.9%
Luna     Nerd [███████████░░░░░░░░░] 33.3%
GPT 5.5  Nerd [████████████████████] 59.9%
Opus     Nerd [██████████████░░░░░░] 43.4%
Fable    Nerd [███████████████░░░░░] 44.5%
Sonnet   Nerd [███████████████████░] 58.4%
Haiku    Nerd [██░░░░░░░░░░░░░░░░░░]  6.5%
```

### Method

Accuracy and latency use Nerd Smart versus Superpowers Brainstorming as the representative comparison for every model. Token savings is the median per-case percentage for the no-narration comparison, labeled Nerd. See the [full cost and accuracy view](docs/benchmark/nerd-cost-accuracy.html) and [benchmark plan](docs/plans/2026-07-15-nerd-benchmarks.md).

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
