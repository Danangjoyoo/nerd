# Nerd

![Nerd mascot banner](assets/nerd-banner.png)

[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml) [![skills.sh](https://skills.sh/b/danangjoyoo/nerd)](https://skills.sh/danangjoyoo/nerd)

Focused operating skills for coding agents: think clearly, diagnose before fixing, audit with evidence, build against repository reality, minimize critical-path latency, and stay silent when narration adds no value.

## Install

Clone once, then use the helper so skill installation and the automatic Smart hook are configured together:

```bash
git clone --depth 1 https://github.com/Danangjoyoo/nerd.git
cd nerd

./scripts/install.sh codex
./scripts/install.sh claude
./scripts/install.sh cursor

# Configure all three supported agents in one run:
./scripts/install.sh all
```

The helper preserves existing hook configuration and is safe to run again. Codex asks you to review and trust newly installed command hooks once through `/hooks` before they execute.

## Skills

| Skill | Description |
| --- | --- |
| `nerd-smart` | Aligns the complete outcome and authorization boundary, then routes and works proactively without overengineering. |
| `nerd-surgery` | Diagnoses broken behavior from evidence and repairs only at an authorized execute endpoint. |
| `nerd-patrol` | Examines a confirmed security scope and reports only reachable, evidence-backed findings. |
| `nerd-execute` | Implements approved plans or confirmed outcomes using simple repository-native designs and proportionate proof. |
| `nerd-silent` | Suppresses optional narration and effort while preserving correctness and the complete result. |
| `nerd-fast` | Minimizes critical-path latency through reuse, batching, narrow exploration, and proportionate proof. |
| `nerd-xfast` | Produces the smallest sufficient answer or authorized edit through one immutable action chain, immediate output, and bounded end proof. |

Smart may route one primary specialty when it strengthens the workflow; Fast and Silent compose as global modifiers. XFast is a self-contained, explicitly lossy execution path. The Agent Skills layout supports Codex, Claude Code, and Cursor.

Nerd includes shortened internal knowledge derived from MIT-licensed Superpowers; see [third-party notices](THIRD_PARTY_NOTICES.md). Users do not need a separate Superpowers installation.

## Benchmarks

Representative rubric score per model. Higher is better; each block is 5 percentage points.

```text
================= Sol     =================
Nerd        | Acc [████████████████████] 100.0% | Lty [█████████░░░░░░░░░░░]  82.9s | Tokens Saved [███████████████████░] 55.9%
Superpowers | Acc [████████████████████] 100.0% | Lty [██████████░░░░░░░░░░]  89.9s | N/A

================= Terra   =================
Nerd        | Acc [████████████████████] 100.0% | Lty [█████████░░░░░░░░░░░]  78.8s | Tokens Saved [██░░░░░░░░░░░░░░░░░░]  6.9%
Superpowers | Acc [██████░░░░░░░░░░░░░░]  30.0% | Lty [██████████░░░░░░░░░░]  88.7s | N/A

================= Luna    =================
Nerd        | Acc [████████████████████] 100.0% | Lty [███████░░░░░░░░░░░░░]  65.3s | Tokens Saved [███████████░░░░░░░░░] 33.3%
Superpowers | Acc [█████████████░░░░░░░]  65.0% | Lty [█████████░░░░░░░░░░░]  84.4s | N/A

================= GPT 5.5 =================
Nerd        | Acc [████████████████████] 100.0% | Lty [█████░░░░░░░░░░░░░░░]  46.9s | GPT 5.Tokens Saved [████████████████████] 59.9%
Superpowers | Acc [████████████████████] 100.0% | Lty [████████░░░░░░░░░░░░]  72.1s | N/A

================= Opus    =================
Nerd        | Acc [████████████████████] 100.0% | Lty [████░░░░░░░░░░░░░░░░]  35.6s | Tokens Saved [██████████████░░░░░░] 43.4%
Superpowers | Acc [█████████████░░░░░░░]  65.0% | Lty [█████████████░░░░░░░] 114.4s | N/A

================= Fable   =================
Nerd        | Acc [████████████████████] 100.0% | Lty [████████████░░░░░░░░] 109.9s | Tokens Saved [███████████████░░░░░] 44.5%
Superpowers | Acc [█████████████░░░░░░░]  65.0% | Lty [███████████░░░░░░░░░] 103.1s | N/A

================= Sonnet  =================
Nerd        | Acc [████████████████████] 100.0% | Lty [████░░░░░░░░░░░░░░░░]  32.5s | Tokens Saved [███████████████████░] 58.4%
Superpowers | Acc [█████████████░░░░░░░]  65.0% | Lty [███████████████████░] 169.6s | N/A

================= Haiku   =================
Nerd        | Acc [████████████████████] 100.0% | Lty [███░░░░░░░░░░░░░░░░░]  30.6s | Tokens Saved [██░░░░░░░░░░░░░░░░░░]  6.5%
Superpowers | Acc [██████░░░░░░░░░░░░░░]  30.0% | Lty [███░░░░░░░░░░░░░░░░░]  28.4s | N/A
```


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

<!-- XFAST_BENCHMARK:START -->
## Now available xfast!

Nerd XFast is the self-contained, KISS-first throughput path. It intentionally trades exploration, accuracy, completeness, and verification breadth in pursuit of lower latency through one immutable action chain, immediate output, and at most one model-selected end-proof wave.

In this pilot, XFast was 55.39% faster and used 58.50% fewer output tokens.

| Model | Fast accuracy | XFast accuracy | Accuracy delta | Fast latency | XFast latency | Speed | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | 98.00% | 100.00% | +2.00 points | 95.60s | 28.93s | +69.12% | 69.07% saved |
| Terra | 100.00% | 100.00% | +0.00 points | 41.71s | 30.28s | +36.40% | 39.14% saved |
| Sol | 96.00% | 100.00% | +4.00 points | 81.45s | 39.35s | +52.15% | 55.83% saved |
| Combined | 98.00% | 100.00% | +2.00 points | 75.13s | 30.28s | +55.39% | 58.50% saved |

[Cases](benchmarks/pilots/xfast-v3-five-cases/cases.json) · [Pilot configs](benchmarks/pilots/xfast-v3-five-cases/) · [Result summary](benchmarks/pilots/xfast-v3-five-cases/result.json)
<!-- XFAST_BENCHMARK:END -->

<!-- UFAST_BENCHMARK:START -->
## UFast directional pilot

UFast is archived under [docs/experiments/nerd-ufast](docs/experiments/nerd-ufast/) and is not included in Nerd installs.

Across 2 cases, 1 repetition, and 1 model at Luna-high, both XFast and UFast scored 100.00%. The paired result put UFast 27.71% slower with 44.70% more output tokens.

| Mode | Accuracy | Median latency | Median output tokens |
| --- | ---: | ---: | ---: |
| XFast | 100.00% | 43.77s | 1,769.5 |
| UFast | 100.00% | 54.93s | 2,324.0 |

This is directional evidence only. The isolated run exercised UFast's skill-only fallback path, not its registered `inspect` and `apply_verify` MCP tools.

[Cases](benchmarks/pilots/ufast-v1-two-cases/cases.json) · [Config](benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json) · [Fresh result](benchmarks/pilots/ufast-v1-two-cases/runs/20260803T164208Z-24e573e-gpt-5.6-luna-high/result.json)
<!-- UFAST_BENCHMARK:END -->
