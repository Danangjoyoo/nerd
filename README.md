# Nerd

![Nerd mascot banner](assets/nerd-banner.png)

[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml) [![skills.sh](https://skills.sh/b/danangjoyoo/nerd)](https://skills.sh/danangjoyoo/nerd)

**Nerd is a skill ecosystem for coding agents with a quietly revolutionary idea: make focus, context discipline, and memory part of how work gets done.**

Nerd's strength is making each token count. Focused workflows narrow what the agent reads, concise output preserves room for useful context, and memory reuses verified lessons from earlier work. Together, they reduce repeated explanation and rediscovery while keeping the current request in charge. The payoff: less overhead, more attention on the task, and verification matched to the work.

Works with **Codex, Claude Code, and Cursor**. [Browse the skills](skills/).

## Three core powers

### Gentle Intelligence

Good work starts with understanding what you actually need. [nerd-smart](skills/nerd-smart/SKILL.md) turns a broad request into a clear goal, a defined scope, and the right workflow, giving the agent a steady direction before it begins. It keeps exploration, planning, and execution tied to your intended outcome, and challenges assumptions when they would send the task off course. The result is collaboration that is easier to follow, with a shared understanding of what matters, what belongs in the task, and when the work is complete.

### Golden Brain

Useful memory should make the next task easier. [nerd-memory](skills/nerd-memory/SKILL.md) carries verified lessons from earlier work into later requests, helping the agent reuse approaches that worked and learn from corrections. Alongside it, [nerd-context](skills/nerd-context/SKILL.md) preserves a task's goals, boundaries, decisions, evidence, checkpoints, and open questions in a local SQLite store, addressed only by an opaque `context_id` you supply on resume — omitting it always creates a fresh Context, and unknown IDs never search or substitute. Records are bounded, source-linked, and treated as untrusted advisory evidence (not authority). Nerd Context and Nerd Memory are separate stores and separate workflows; MCP registration is preferred and CLI fallback is guarded. Production release is not yet declared — the measured lexical POC ([evidence](docs/specs/nerd-context-handover.md)) still has token-savings, quality-delta, adversarial, latency, break-even, and generated-capture gates unmet, and its Codex-only measurements may drift with hosted model versions. Together, the vision is continuity: less time rebuilding shared understanding, less repeated explanation, and more useful context for the work ahead, with your current instructions always taking priority.

### Eye's Blink in Fast Mode

Speed comes from spending effort where it matters. [nerd-fast](skills/nerd-fast/SKILL.md) reduces waiting by reusing trustworthy evidence, batching independent operations, and narrowing reads and checks to the task while keeping required verification intact. [nerd-xfast](skills/nerd-xfast/SKILL.md) pushes further toward immediate output with a smaller action path and limited exploration and verification. That extra speed accepts trade-offs in accuracy and completeness, making it an explicit choice for concrete requests where those limits are acceptable. The two modes let you match the pace of the agent to the demands of the work.

## Nerd performance

**49.2% faster. 38.6% fewer output tokens. Higher measured accuracy.**

Recorded benchmark results across eight models:

| Metric | Nerd |
| --- | ---: |
| Speed | **49.2% faster** |
| Token saving (output) | **38.6% less token** |
| Accuracy | **100%** |

Speed compares the averages of each model's median time: (baseline ÷ Nerd − 1) × 100%. Token savings average each model's median reduction. Accuracy is the mean rubric score across 16 case pairs. These results describe this benchmark sample. [Benchmark details](docs/benchmark/nerd-cost-accuracy.html).

### Smart + Memory + Context pilot — Claude 5 family (2026-09-18)

Three deterministic Nerd cases that each require `/nerd-smart`, `/nerd-memory`, and `/nerd-context` in that order, three repetitions per case, three models = 27 real `claude -p` sessions. Runner: [benchmarks/nerd_pilot/](benchmarks/nerd_pilot/). Duration and tokens are read from the `claude` CLI `--output-format json` payload (not self-reported); accuracy is a six-point rubric ([benchmarks/nerd_pilot/rubric.py](benchmarks/nerd_pilot/rubric.py)) covering visible Focus Record, endpoint choice, memory-blind pass, unknown-ID `not_found` without substitution, fresh `Nerd-context created:` receipt from a real runtime-generated ID, and naming one smallest-choice-changing unknown. Sub-sessions ran with `--allowedTools` restricted to Skill/Read plus the six Nerd MCP tools; no repo mutation.

Baseline (100%) is a non-Nerd Opus 5 run of the same three cases (1 rep each, no `/nerd-smart`, `/nerd-memory`, `/nerd-context`). Each Nerd row shows the median across 3 cases × 3 reps as a percentage of that baseline. Accuracy above 100% is better; duration and tokens below 100% are better.

| Model | Accuracy | Duration | Output tokens |
| --- | ---: | ---: | ---: |
| `claude-opus-5` | **300.0%** | 94.8% | 153.4% |
| `claude-sonnet-5` | **250.0%** | **34.1%** | **78.0%** |
| `claude-haiku-4-5` | 100.0% | **38.3%** | 94.4% |

Overall: 27/27 Nerd sessions completed successfully; the six-point rubric ([benchmarks/nerd_pilot/rubric.py](benchmarks/nerd_pilot/rubric.py)) covers visible Focus Record, endpoint choice, memory-blind pass, unknown-ID `not_found` without substitution, fresh `Nerd-context created:` receipt from a real runtime-generated ID, and naming one smallest-choice-changing unknown. Sub-sessions ran with `--allowedTools` restricted to Skill/Read plus the six Nerd MCP tools; no repo mutation. Reasoning tier was each sub-agent's harness-configured default (no explicit `low`/`medium`/`high` knob exposed). Rubric fails on smaller models cluster on Focus Record surfacing and receipt phrasing rather than on Context correctness. This pilot is a single sample on three cases; it does not replace the held live empirical protocol for Nerd Context's own gates and does not unlock Task 7 of [the plan](docs/plans/2026-08-27-nerd-context.md). Raw run artifacts live under the ignored `benchmarks/results/nerd-pilot/` root; runner and cases in [benchmarks/nerd_pilot/](benchmarks/nerd_pilot/).

## Install

Install the skills and automatic Smart hook together:

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

MIT licensed. See [LICENSE](LICENSE). Includes condensed knowledge derived from Superpowers; see [third-party notices](THIRD_PARTY_NOTICES.md). No separate Superpowers installation is required.
