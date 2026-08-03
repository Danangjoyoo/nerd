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
| `nerd-xfast` | Super high speed through batched native text/patch calls, one immutable action chain, and V0 or one bounded V1 end-proof wave; deliberately lossy. |
| `nerd-ufast` | Generic tool-backed ultra-fast work through batched registry operations, deterministic safety guards, and a V0/V1 auto-or-ask proof ladder. |

Smart routes one primary specialty; Fast, UFast, and Silent are explicit global modifiers. XFast is a self-contained, explicitly lossy execution path. The Agent Skills layout supports Codex, Claude Code, and Cursor; UFast's bundled MCP runtime is currently verified only with Codex.

Nerd includes shortened internal knowledge derived from MIT-licensed Superpowers; see [third-party notices](THIRD_PARTY_NOTICES.md). Users do not need a separate Superpowers installation.

## Choose a speed mode

Smart aligns intention, endpoint, scope, and working role. The speed modes then optimize different parts of execution:

| Need | Choose | Contract |
| --- | --- | --- |
| High speed work without deliberate accuracy loss | Fast | Reuse, batch, parallelize, navigate narrowly, and run proportionate proof. |
| Super high speed for rapid output | XFast | Batch native text/patch calls and accept reduced exploration, completeness, accuracy, and verification breadth. |
| Tool-backed ultra-fast work on a supported deterministic operation | UFast | Batch project index/search/edit/test operations and preserve the active workflow's accuracy contract. |

XFast remains at the agent's native text/patch layer: it batches independent calls, stops exploration early, and chooses V0 or one end-only V1 proof wave. UFast moves the mechanical “how” into deterministic tools: search accepts batched queries, safe edit batches files atomically, and the test runner executes independent checks concurrently. Its V0 reuses fresh structured evidence; V1 runs safe local proof automatically or asks first when proof is broad, stateful, external, destructive, or needs more authority.

UFast is generic: its operation registry can route any intent for which a deterministic backend is installed. Phase 1 bundles a reusable project index, bounded fast search, hash-guarded safe edit, and repository-aware test runner. The safe-edit backend handles UTF-8 workspace changes with atomic replacement and rollback; Python is only the adapter exercised by the verification benchmark. Language Server and AST/codemod backends remain later phases. UFast and XFast do not compose. Installing UFast does not promise that every task is faster, and benchmark wording follows the measured result.

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
## UFast: routed deterministic project tools

Nerd UFast is a generic tool-backed modifier with an operation registry. Phase 1 batches indexed queries, atomic multi-file edits, and concurrent allowlisted checks. V0 reuses fresh structured evidence; V1 runs safe local proof automatically or asks before broader proof. Language-specific LSP and AST backends can register later without changing the public routing contract.

Across this directional pilot, UFast was 47.33% slower than XFast. UFast used 44.73% more output tokens.

| Model | XFast accuracy | UFast accuracy | Accuracy delta | XFast latency | UFast latency | Speed | XFast tokens | UFast tokens | Token change | Tool hit | Fallbacks |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |
| Luna | 90.00% | 90.00% | +0.00 points | 45.45s | 73.77s | 62.30% slower | 1722 | 2826 | 64.11% more | 100.00% | 0 |
| Terra | 100.00% | 90.00% | -10.00 points | 46.84s | 61.99s | 32.35% slower | 1736 | 2176 | 25.35% more | 100.00% | 0 |
| Combined | 95.00% | 90.00% | -5.00 points | 46.15s | 67.88s | 47.33% slower | 1729 | 2501 | 44.73% more | 100.00% | 0 |

The UFast route had a 100.00% tool hit rate, 0 fallback runs, 2 project-index runs, 2 fast-search runs, 0 standalone test-runner runs, 38.50 ms median cold start, and 69.00 ms median total tool-operation time per run.

Method: one Python discovery/edit verification case, one repetition, and Luna plus Terra at `high` reasoning effort produced 4 fresh Codex processes and 2 matched pairs. The case exercises one adapter, not UFast's generic scope. The exact prompt and proof commands are shared by both arms. This tiny verification does not establish a universal speedup. Codex is the only verified UFast tool host in this release; other hosts install the skill but fall back until their tool integration is verified.

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
