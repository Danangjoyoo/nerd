# Nerd Second One-Case Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and execute a second direct benchmark pilot with one new case per comparison, one repetition, and two arms across four GPT and four Claude targets.

**Architecture:** A dedicated immutable case bundle selects four existing cases that do not overlap the first pilot. Eight derived configs retain every model, judge, effort, seed, condition, and upstream pin while setting `repetitions` to `1` and pointing at the new bundle. GPT shards execute locally; a self-contained Claude prompt runs the same direct release workflow for the four Claude targets.

**Tech Stack:** Python 3 standard library, JSON benchmark configs, `unittest`, Codex CLI, Claude Code CLI.

## Global Constraints

- Selected cases are exactly `smart-compound-queue`, `surgery-component-boundary`, `execute-written-plan`, and `silent-code-only`.
- Each target plans exactly 8 candidate runs: 4 cases × 1 repetition × 2 arms.
- Use direct `--release` runs; never use smoke mode.
- Do not modify the original case files or eight 120-run configs.
- Use one paid attempt per target and explicit result paths for judge, score, and report commands.
- Preserve timeouts and failures; never rewrite raw or judge evidence.
- Do not update README or publish pilot metrics as statistically sufficient.

---

### Task 1: Lock the second-pilot contract

**Files:**
- Create: `tests/test_second_pilot.py`

**Interfaces:**
- Consumes: `benchmarks.nerdbench.runner.load_config` and `schedule_runs`.
- Produces: A contract requiring four exact non-overlapping cases, eight exact target configs, 8 unique runs per config, and a bounded Claude prompt.

- [ ] **Step 1: Write the failing test**

Create tests that require:

```python
SECOND_CASES = {
    "smart-compound-queue",
    "surgery-component-boundary",
    "execute-written-plan",
    "silent-code-only",
}
```

For every target, assert `repetitions == 1`, the case file is the second-pilot bundle, scheduling returns 8 unique runs, repetitions equal `{1}`, and case IDs equal `SECOND_CASES`. Assert the Claude prompt names all four Claude configs, requires direct `--release`, expects `8`, `4`, and `8`, and forbids `--latest`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
rtk python3 -m unittest tests.test_second_pilot -v
```

Expected: FAIL because `benchmarks/pilots/second-one-case/cases.json`, its eight configs, and `docs/prompts/claude-second-one-case.md` do not exist.

### Task 2: Add immutable second-pilot inputs

**Files:**
- Create: `benchmarks/pilots/second-one-case/cases.json`
- Create: `benchmarks/pilots/second-one-case/gpt-5.6-sol-xhigh.json`
- Create: `benchmarks/pilots/second-one-case/gpt-5.6-terra-xhigh.json`
- Create: `benchmarks/pilots/second-one-case/gpt-5.6-luna-xhigh.json`
- Create: `benchmarks/pilots/second-one-case/gpt-5.5-xhigh.json`
- Create: `benchmarks/pilots/second-one-case/claude-fable-5-xhigh.json`
- Create: `benchmarks/pilots/second-one-case/claude-opus-4-8-xhigh.json`
- Create: `benchmarks/pilots/second-one-case/claude-sonnet-5-xhigh.json`
- Create: `benchmarks/pilots/second-one-case/claude-haiku-4-5.json`

**Interfaces:**
- Consumes: Existing case objects and base target configs.
- Produces: Eight direct-run configs that each schedule exactly 8 runs over the same four cases.

- [ ] **Step 1: Copy exact case objects**

Create one `{"cases": [...]}` document containing byte-for-byte JSON object copies of the four selected cases from their source files.

- [ ] **Step 2: Derive target configs**

For each base config, keep all fields unchanged except:

```json
{
  "case_files": ["benchmarks/pilots/second-one-case/cases.json"],
  "repetitions": 1
}
```

- [ ] **Step 3: Run the contract test**

Run:

```bash
rtk python3 -m unittest tests.test_second_pilot -v
```

Expected: the config and case tests PASS while the Claude-prompt test still FAILS.

### Task 3: Add the Claude execution handoff

**Files:**
- Create: `docs/prompts/claude-second-one-case.md`

**Interfaces:**
- Consumes: The four Claude configs from Task 2.
- Produces: One operator prompt that runs four independent direct pilot shards in parallel.

- [ ] **Step 1: Write the prompt**

Require preflight checks, exactly 8 planned candidates per config, direct `--release`, one paid attempt per target, long-running/background execution, explicit printed result paths, and exact-path judge → score → report → report-check commands. Require 8 raw, 4 unique judges, and 8 scores for each completed target.

- [ ] **Step 2: Run the focused tests**

Run:

```bash
rtk python3 -m unittest tests.test_second_pilot -v
```

Expected: PASS.

### Task 4: Verify and execute

**Files:**
- Verify: `benchmarks/pilots/second-one-case/*.json`
- Execute into: `benchmarks/results/`

**Interfaces:**
- Consumes: The four GPT configs and Claude handoff.
- Produces: Four local GPT result shards plus four externally executed Claude result shards.

- [ ] **Step 1: Run deterministic verification**

Run:

```bash
rtk python3 -m unittest discover -s tests -v
rtk python3 -m compileall -q scripts benchmarks tests
rtk python3 scripts/validate_skills.py
```

Expected: all tests and validations PASS.

- [ ] **Step 2: Verify every dry plan**

Run `rtk python3 benchmarks/run.py plan --config` for all eight configs. Each final line must equal `8 planned agent runs`.

- [ ] **Step 3: Execute four GPT shards in parallel**

Run each GPT config once with direct `--release`. For each explicit result path, run judge, score, report, and report `--check`. Validate 8 raw, 4 judge tasks, 8 scores, exact model/effort pins, and Silent token usage.

- [ ] **Step 4: Hand off Claude execution**

Provide `docs/prompts/claude-second-one-case.md` to the user. Claude executes only the four Claude configs and returns exact paths for independent verification.

