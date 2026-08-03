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
| `nerd-smart` | Cleverly quick thinking that aligns intention, endpoint, scope, and one working role before substantive work. |
| `nerd-surgery` | Diagnoses broken behavior from evidence and repairs only at an authorized execute endpoint. |
| `nerd-patrol` | Examines a confirmed security scope and reports only reachable, evidence-backed findings. |
| `nerd-execute` | Implements approved plans or confirmed small changes using repository patterns and fresh proof. |
| `nerd-silent` | Suppresses optional narration and effort while preserving correctness and the complete result. |
| `nerd-fast` | High speed work that cuts critical-path latency through reuse, batching, narrow exploration, and proportionate proof without reducing accuracy. |
| `nerd-xfast` | Super high speed through batched native text/patch calls, one immutable action chain, and V0 or one bounded V1 end-proof wave; deliberately lossy. |
| `nerd-ufast` | Prompt-only ultra-fast work through one batched context wave, one action wave, and one V0/V1 proof decision. |

Smart routes one primary specialty; Fast, UFast, and Silent are explicit global modifiers. XFast is a self-contained, explicitly lossy execution path. The Agent Skills layout supports Codex, Claude Code, and Cursor.

Nerd includes shortened internal knowledge derived from MIT-licensed Superpowers; see [third-party notices](THIRD_PARTY_NOTICES.md). Users do not need a separate Superpowers installation.

## Choose a speed mode

Smart aligns intention, endpoint, scope, and working role. The speed modes then optimize different parts of execution:

| Need | Choose | Contract |
| --- | --- | --- |
| High speed work without deliberate accuracy loss | Fast | Reuse, batch, parallelize, navigate narrowly, and run proportionate proof. |
| Super high speed for rapid output | XFast | Batch native text/patch calls and accept reduced exploration, completeness, accuracy, and verification breadth. |
| Strict prompt-only execution without deliberate accuracy loss | UFast | Use one batched context wave, one action wave, and one V0/V1 proof decision. |

XFast batches native text/patch calls, stops exploration early, and deliberately accepts reduced completeness, accuracy, and proof. UFast preserves the active workflow's accuracy contract but forces a stricter three-wave shape: batch known context, batch known mutations, then make one proof decision. Its V0 reuses fresh evidence; V1 runs safe local proof automatically or asks first when proof is broad, stateful, external, destructive, or needs more authority.

UFast currently ships only `SKILL.md` instructions and metadata. It has no bundled scripts, MCP server, registry, language server, or AST engine. Those capabilities can be added and benchmarked individually later. UFast and XFast do not compose, and benchmark wording follows the measured result.

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

<!-- UFAST_BENCHMARK:START -->
## UFast: prompt-only three-wave execution

Nerd UFast currently contains prompt instructions and metadata only. It batches known context, known mutations, and proportionate proof into three waves while preserving the active workflow's accuracy contract. It has no bundled scripts, MCP server, registry, language server, or AST engine.

Across this directional pilot, UFast was 47.00% slower than XFast. UFast used 52.54% more output tokens.

| Model | XFast accuracy | UFast accuracy | Accuracy delta | XFast latency | UFast latency | Speed | XFast tokens | UFast tokens | Token change |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Luna | 100.00% | 100.00% | +0.00 points | 53.85s | 63.20s | 17.37% slower | 2264 | 2721 | 20.19% more |
| Terra | 100.00% | 100.00% | +0.00 points | 48.31s | 85.33s | 76.64% slower | 1960 | 3624 | 84.90% more |
| Combined | 100.00% | 100.00% | +0.00 points | 51.08s | 74.27s | 47.00% slower | 2112.0 | 3172.5 | 52.54% more |

Method: one unchanged Python discovery/edit verification case, one repetition, and Luna plus Terra at `high` reasoning effort produced 4 fresh isolated Codex processes and 2 matched pairs. Both conditions ignored user configuration and used only their materialized skills plus platform-native tools. This tiny pilot measures prompt discipline, not future specialized-tool performance, and does not establish a universal speedup.

[Cases](benchmarks/cases/ufast-phase1-verification.json) · [Pilot configs](benchmarks/pilots/ufast-vs-xfast/) · [Result summary](benchmarks/pilots/ufast-vs-xfast/result.json)
<!-- UFAST_BENCHMARK:END -->

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
