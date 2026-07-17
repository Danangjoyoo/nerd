# Nerd Fast Raw-Agent Smoke Benchmark Implementation Plan

**Goal:** Compare raw Codex with Codex using only Nerd Fast on one complex repository-summary case, publish accuracy, latency, and provider-reported output tokens, and make skill isolation plus indexer use observable.

**Architecture:** Materialize the current repository into two isolated workspaces. Give the raw arm no Nerd skills and the treatment arm only `nerd-fast`. Run both with GPT-5.6 Sol at `xhigh`, score deterministic factual-coverage and clean-worktree gates, reject contaminated evidence, and publish one sanitized paired summary.

**Constraints:** Work in the current repository without a worktree. Use one case, one repetition, and no judge call. Preserve failed or unfavorable evidence. Reuse authentication without copying credentials into a workspace. Do not install Universal Ctags automatically.

## Task 1: Isolate the benchmark arms

**Files:**

- `benchmarks/nerdbench/materialize.py`
- `benchmarks/nerdbench/runner.py`
- `benchmarks/nerdbench/adapters.py`
- `tests/test_fast_raw_benchmark.py`

- [x] Add `raw-agent` with an empty skill set and unchanged prompt.
- [x] Add `nerd-fast-only` with exactly `nerd-fast` and the prefix `Use $nerd-fast.`
- [x] Ignore user config and rules for both isolated arms.
- [x] Give both arms temporary `CODEX_HOME` and `HOME` values while symlinking only `auth.json`.
- [x] Prove the raw workspace has an empty `.agents/skills` directory and the treatment has exactly one skill.

Focused proof:

```sh
rtk python3 -m unittest tests.test_fast_raw_benchmark.FastRawConditionTests -v
```

## Task 2: Add the complex one-case pilot

**Files:**

- `benchmarks/pilots/fast-raw-one-case/cases.json`
- `benchmarks/pilots/fast-raw-one-case/gpt-5.6-sol-xhigh.json`
- `benchmarks/nerdbench/cases.py`
- `benchmarks/nerdbench/materialize.py`
- `benchmarks/nerdbench/scorer.py`

- [x] Add the `__repository__` fixture, copying tracked and non-ignored untracked contents into an isolated workspace.
- [x] Ask for a path-grounded maintainer summary covering purpose, all public skills, composition, benchmark architecture, installation, validation, and major directories.
- [x] Add deterministic regex gates for skill, architecture, agent, and operations coverage.
- [x] Add a `clean` evaluator that requires no changed files.
- [x] Pin Codex, `gpt-5.6-sol`, `xhigh`, one repetition, sequential execution, and the ordered arms `raw-agent` then `nerd-fast-only`.

Focused proof:

```sh
rtk python3 -m unittest tests.test_fast_raw_benchmark.FastRawPilotTests -v
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/fast-raw-one-case/gpt-5.6-sol-xhigh.json
```

## Task 3: Make isolation and indexer use reportable invariants

**Files:**

- `benchmarks/nerdbench/pair_report.py`
- `benchmarks/run.py`
- `skills/nerd-fast/SKILL.md`
- `tests/test_fast_raw_benchmark.py`
- `tests/test_skill_contracts.py`

- [x] Require exactly one `raw-agent` record and one `nerd-fast-only` record with matching run identity.
- [x] Reject any raw executed command that accesses `/.agents/skills/nerd-*`.
- [x] Reject a treatment run unless an executed command invokes `symbol_index.py ensure`.
- [x] Accept ordinary shell punctuation after `ensure` without treating a read of the script as execution.
- [x] Require Nerd Fast to attempt one index refresh at discovery start for complex repository analysis, architecture summaries, or cross-file work expected to need at least three exact-symbol lookups.
- [x] Preserve the single-known-target skip and one-attempt fallback when Universal Ctags is unavailable.
- [x] Record the two evidence controls in the sanitized summary.

Focused proof:

```sh
rtk python3 -m unittest tests.test_fast_raw_benchmark.FastRawReportTests -v
rtk python3 -m unittest tests.test_skill_contracts.FastContractTests -v
rtk python3 scripts/validate_skills.py
```

## Task 4: Run, score, and publish the exact evidence

**Files:**

- `benchmarks/pilots/fast-raw-one-case/result.json`
- `README.md`
- `tests/test_readme.py`

- [x] Run the exact two-arm configuration once.
- [x] Audit raw commands for Nerd-skill access and treatment commands for the indexer invocation.
- [x] Score the exact printed result directory.
- [x] Generate the sanitized paired summary with explicit overwrite only after the audit passes.
- [x] Publish the generated README region and label the result as one-case, one-repetition directional evidence.

Commands:

```sh
rtk python3 benchmarks/run.py run --config benchmarks/pilots/fast-raw-one-case/gpt-5.6-sol-xhigh.json
rtk python3 benchmarks/run.py score --config benchmarks/pilots/fast-raw-one-case/gpt-5.6-sol-xhigh.json --results <exact-result-directory>
rtk python3 benchmarks/run.py pair-report --results <exact-result-directory> --output benchmarks/pilots/fast-raw-one-case/result.json --overwrite
rtk python3 benchmarks/run.py pair-publish --summary benchmarks/pilots/fast-raw-one-case/result.json --readme README.md
```

## Task 5: Verify and open the pull request

- [ ] Run the complete repository suite, skill validator, README contracts, and `git diff --check`.
- [ ] Review the final diff for unrelated or generated raw evidence.
- [ ] Commit the approved changes on the current branch.
- [ ] Push the branch and create the PR with `gh`.

Final proof:

```sh
rtk python3 -m unittest discover -s tests -v
rtk python3 scripts/validate_skills.py
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/fast-raw-one-case/gpt-5.6-sol-xhigh.json
rtk git diff --check
```
