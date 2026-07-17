# Nerd

![Nerd mascot banner](assets/nerd-banner.png)

[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml) [![skills.sh](https://skills.sh/b/danangjoyoo/nerd)](https://skills.sh/danangjoyoo/nerd)

Focused operating skills for coding agents: think clearly, diagnose before fixing, audit with evidence, build against repository reality, minimize critical-path latency, and stay silent when narration adds no value.

## Install

```bash
# Codex
npx skills add danangjoyoo/nerd \
  --global \
  --agent codex \
  --skill '*' \
  --yes

# Claude Code
npx skills add danangjoyoo/nerd \
  --global \
  --agent claude-code \
  --skill '*' \
  --yes

# Cursor
npx skills add danangjoyoo/nerd \
  --global \
  --agent cursor \
  --skill '*' \
  --yes
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
| `nerd-fast` | Minimizes critical-path latency through reuse, batching, narrow exploration, and proportionate proof. |

Smart routes one primary specialty; Fast and Silent compose as global modifiers with any active workflow. The Agent Skills layout supports Codex, Claude Code, and Cursor.

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
