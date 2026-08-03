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

# Opt into the verified Codex UFast tool runtime:
./scripts/install.sh codex --ufast

# Configure all three supported agents in one run:
./scripts/install.sh all
```

The helper preserves existing hook and Codex configuration and is safe to run again. `--ufast` is explicit because it registers a local, namespaced MCP server; Codex is the only verified UFast tool host in this release. Codex asks you to review and trust newly installed command hooks once through `/hooks` before they execute.

## Skills

| Skill | Description |
| --- | --- |
| `nerd-smart` | Cleverly quick thinking that aligns intention, endpoint, scope, and one working role before substantive work. |
| `nerd-surgery` | Diagnoses broken behavior from evidence and repairs only at an authorized execute endpoint. |
| `nerd-patrol` | Examines a confirmed security scope and reports only reachable, evidence-backed findings. |
| `nerd-execute` | Implements approved plans or confirmed small changes using repository patterns and fresh proof. |
| `nerd-silent` | Suppresses optional narration and effort while preserving correctness and the complete result. |
| `nerd-fast` | High speed work that cuts critical-path latency through reuse, batching, narrow exploration, and proportionate proof without reducing accuracy. |
| `nerd-xfast` | Super high speed for rapid output through one immutable action chain, immediate results, and bounded end proof. |
| `nerd-ufast` | Generic tool-backed ultra-fast work for supported operations, with bounded inputs, structured results, safety guards, and immediate fallback. |

Smart routes one primary specialty; Fast, UFast, and Silent are explicit global modifiers. XFast is a self-contained, explicitly lossy execution path. The Agent Skills layout supports Codex, Claude Code, and Cursor; UFast's bundled MCP runtime is currently verified only with Codex.

Nerd includes shortened internal knowledge derived from MIT-licensed Superpowers; see [third-party notices](THIRD_PARTY_NOTICES.md). Users do not need a separate Superpowers installation.

## Choose a speed mode

Smart aligns intention, endpoint, scope, and working role. The speed modes then optimize different parts of execution:

| Need | Choose | Contract |
| --- | --- | --- |
| High speed work without deliberate accuracy loss | Fast | Reuse, batch, parallelize, navigate narrowly, and run proportionate proof. |
| Super high speed for rapid output | XFast | Accept reduced exploration, completeness, accuracy, and verification breadth. |
| Tool-backed ultra-fast work on a supported deterministic operation | UFast | Route work into a matching namespaced tool; fall back when no installed tool supports it. |

UFast is generic: the modifier can route any operation for which a matching UFast tool is installed. Its first bundled route handles bounded UTF-8 workspace changes with hash guards, atomic replacement, verification adapters, and rollback; Python is only the adapter exercised by this benchmark. UFast and XFast do not compose. Installing UFast does not promise that every task is faster, and the benchmark reports the measured result even when it is slower.

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
## UFast: deterministic tools for supported changes

Nerd UFast is a generic tool-backed modifier that keeps the active workflow's scope and correctness contract. Its first bundled route moves a supported UTF-8 workspace change into one hash-guarded, atomic transaction with verification adapters and rollback; unsupported operations fall back to the active workflow.

Across this directional pilot, UFast was 15.27% slower than XFast and used 2.75% more output tokens.

| Model | XFast accuracy | UFast accuracy | Accuracy delta | XFast latency | UFast latency | Speed | XFast tokens | UFast tokens | Token change | Tool hit | Fallbacks |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |
| Luna | 94.00% | 96.00% | +2.00 points | 44.54s | 78.72s | 88.18% slower | 1927 | 3559 | 92.48% more | 100.00% | 1 |
| Terra | 100.00% | 94.00% | -6.00 points | 40.73s | 37.79s | 9.52% faster | 1423 | 1346 | 5.41% fewer | 100.00% | 0 |
| Sol | 96.00% | 96.00% | +0.00 points | 45.54s | 47.59s | 15.27% slower | 1712 | 1712 | 2.75% more | 100.00% | 0 |
| Combined | 96.67% | 95.33% | -1.33 points | 41.83s | 46.40s | 15.27% slower | 1712 | 1712 | 2.75% more | 100.00% | 1 |

The UFast tool path had a 100.00% hit rate, 1 fallback runs, 25.00 ms median cold start, and 637.00 ms median tool-operation time per run.

Method: five Python coding cases, one repetition, and three models at `high` reasoning effort produced 30 fresh Codex processes and 15 matched pairs. The cases exercise one adapter, not UFast's generic scope. The exact prompts and proof commands are shared by both arms. One repetition is directional evidence; it does not establish a universal speedup. Codex is the only verified UFast tool host in this release; other hosts install the skill but fall back until their tool integration is verified.

[Cases](benchmarks/pilots/xfast-v3-five-cases/cases.json) · [Pilot configs](benchmarks/pilots/ufast-vs-xfast/) · [Result summary](benchmarks/pilots/ufast-vs-xfast/result.json)
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
