# Nerd XFast Implementation and Benchmark Plan

## Goal

Publish `nerd-xfast` as a self-contained, explicitly lossy execution skill,
verify its repository contracts, compare it with regular `nerd-fast`, and
publish measured results in the README.

For this plan, "new agents" means every benchmark run launches a fresh,
isolated Codex process, workspace, and `CODEX_HOME`. It does not mean adding a
new agent platform.

## Confirmed Design

`nerd-xfast` is an execution-only skill built around one persistent Edit
Ledger and three waves:

1. Minimal `READ` work.
2. One single-agent, batched multi-file `WRITE` patch.
3. One final validation batch after all code edits are complete.

The skill intentionally trades accuracy, completeness, and verification
breadth for lower wall-clock latency. It must preserve authorization, safety,
honest reporting, and repository constraints.

## KISS Breakdown

- **Required outcome:** Add the XFast skill, deterministic verification, a
  two-case paired benchmark across three high-effort models, and an
  evidence-backed README section.
- **Smallest change:** Add one two-file skill package, extend existing public
  skill contracts, and add a dedicated XFast pilot on top of the current
  benchmark runner.
- **Proof:** Deterministic repository tests plus 24 fresh workload runs and 12
  blinded paired judging tasks.
- **Not needed:** Changes to `nerd-fast`, a bundled XFast helper script, new
  runtime dependencies, a new agent platform, or weaker main-release
  publication thresholds.

## Worktree Constraint

The repository already contains uncommitted README, installer, validator,
test, and documentation-move changes. Implementation must patch the current
versions in place. It must not reset, revert, overwrite, or commit unrelated
user work.

## Task 1: Create the Self-Contained Skill

Create:

```text
skills/nerd-xfast/
├── SKILL.md
└── agents/
    └── openai.yaml
```

`SKILL.md` must define:

- Explicit activation only.
- A self-contained execution workflow with no automatic Nerd skill
  composition.
- No subagents or reviewers.
- The temporary Edit Ledger as the only planning mechanism.
- Required columns: `#`, `Task`, `Files`, `Action`, and `Status`.
- Actions: `READ` and `WRITE`.
- Statuses: `N`, `O`, `D`, and `S`.
- One ledger update per wave rather than per file.
- The edit-first question: "What is the smallest complete set of files I can
  edit now?"
- Minimal reads, one batched multi-file patch, and deferred validation.
- Compile, lint, and focused tests only after all `WRITE` rows are `D` or
  `S`.
- One conditional repair batch only when final output identifies an exact
  local correction.
- Honest unresolved state: a failed row remains `O` with one short failure
  note.
- The required family Superpowers boundary.
- A compactness ceiling of approximately 650 words.

`agents/openai.yaml` must expose `$nerd-xfast` and describe the intentional
speed-versus-accuracy trade-off.

## Task 2: Register XFast as the Seventh Public Skill

Update the current versions of:

- `scripts/validate_skills.py`
- `tests/test_skill_structure.py`
- `tests/test_workflows.py`
- `.github/workflows/release.yml`
- `tests/test_readme.py`

Required changes:

- Add `nerd-xfast` to the exact public skill set.
- Declare no required references or scripts for XFast.
- Change the release skill count from six to seven.
- Ensure release packaging checks include XFast.
- Preserve wildcard installation. `scripts/install.sh` should not require an
  XFast-specific branch.

## Task 3: Add Deterministic XFast Contract Tests

Add `XFastContractTests` to `tests/test_skill_contracts.py`.

The tests must enforce:

- Self-contained and explicit-only behavior.
- No runtime dependency on `nerd-smart`, `nerd-execute`, or `nerd-fast`.
- Exact ledger columns and status definitions.
- Runtime temporary-file lifecycle.
- The ledger as the sole plan source of truth.
- Smallest-complete-edit-set language.
- One single-agent, multi-file patch.
- No intermediate compile, lint, test, or review.
- Final validation after all write tasks finish.
- One bounded repair rule.
- No subagents or reviewers.
- The word-count ceiling.
- Metadata that explicitly names `$nerd-xfast`.

## Task 4: Create Two Representative Benchmark Cases

Create:

```text
benchmarks/cases/xfast.json
benchmarks/fixtures/xfast-batched-edit/
benchmarks/fixtures/xfast-discovery-edit/
```

### Case A: Known Multi-File Batched Edit

- Require changes across two implementation files and focused tests.
- Measure whether the write set is handled together.
- Validate compilation, repository-local lint, and behavior only after all
  edits.

### Case B: Narrow-Discovery Multi-File Edit

- Do not explicitly name the final implementation target.
- Require one focused discovery pass followed by implementation and test
  edits.
- Use the same deferred validation structure.

Use Python standard-library tooling so dependency installation and network
variance cannot affect latency. Supply deterministic repository-local lint
checks instead of adding a linter dependency.

Hard gates must measure produced files and behavior. Judge criteria may
measure batching and narrow discovery. Ledger compliance remains a
deterministic skill-contract concern rather than relying on judge inference.

## Task 5: Add Isolated Benchmark Conditions

Extend:

- `benchmarks/nerdbench/runner.py`
- `benchmarks/nerdbench/materialize.py`
- `benchmarks/nerdbench/adapters.py`
- `benchmarks/nerdbench/scorer.py`

Add two conditions:

- `xfast-baseline`: install and invoke regular `nerd-smart` + `nerd-execute`
  + `nerd-fast`.
- `nerd-xfast`: install and invoke only `nerd-xfast`.

Both arms must:

- Use fresh workspaces.
- Use fresh temporary `CODEX_HOME` and `HOME` directories.
- Reuse only the authentication symlink.
- Ignore user configuration, global rules, and globally installed skills.
- Launch a new ephemeral Codex process for every run.
- Receive the same case, model, effort, repetition, timeout, and proof
  commands.

## Task 6: Add Three High-Effort Pilot Configurations

Create:

```text
benchmarks/pilots/xfast-vs-fast/gpt-5.6-luna-high.json
benchmarks/pilots/xfast-vs-fast/gpt-5.6-terra-high.json
benchmarks/pilots/xfast-vs-fast/gpt-5.6-sol-high.json
```

Each configuration must specify:

- Agent: `codex`.
- Model: the corresponding Luna, Terra, or Sol model.
- Reasoning effort: `high`.
- Exactly two XFast cases.
- Exactly two repetitions.
- Regular Fast versus XFast conditions.
- Parallelism of one to prevent resource contention.
- The same pinned blinded-judge configuration.

Expected workload count:

```text
2 cases × 2 repetitions × 2 arms × 3 models = 24 workload runs
```

The workload results produce 12 blinded paired judging tasks.

## Task 7: Add a Dedicated XFast Result Aggregator

Create:

```text
benchmarks/nerdbench/xfast_report.py
tests/test_xfast_benchmark.py
```

Extend `benchmarks/run.py` with dedicated XFast report and publish commands.

The reporter must:

- Accept the Luna, Terra, and Sol result directories.
- Reject missing, duplicated, mismatched, or non-`high` runs.
- Require four valid pairs per model and twelve combined pairs.
- Produce per-model directional metrics.
- Produce one twelve-pair aggregate headline.
- Calculate mean accuracy, pass rate, accuracy delta, latency, paired median
  speed improvement, paired median output-token change, and hard-gate
  failures.
- Report unavailable token usage honestly rather than estimating it.
- Render negative token savings as "more tokens" instead of describing them
  as savings.

Two cases and two repetitions provide only four pairs per model, below the
repository's normal five-pair publication threshold. Per-model metrics must be
labelled directional. The combined twelve-pair metric may support the README
headline while still stating that only two coding cases were measured.

Do not weaken or replace the main release benchmark's publication rules.

## Task 8: Run Deterministic Verification Before Live Benchmarks

Run after all implementation and test files are complete:

```bash
rtk python3 -m compileall -q scripts benchmarks tests
rtk git diff --check
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest discover -s tests -v
```

Validate every pilot schedule:

```bash
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/xfast-vs-fast/gpt-5.6-luna-high.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/xfast-vs-fast/gpt-5.6-terra-high.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/xfast-vs-fast/gpt-5.6-sol-high.json
```

Each configuration must plan exactly eight workload runs.

## Task 9: Execute the Benchmark With Fresh Agents

Run the three configurations sequentially. Do not modify source files between
runs.

For each configuration:

1. Execute the eight workload agents.
2. Run blinded judging.
3. Derive deterministic scores.
4. Record the immutable result directory.

After all three configurations complete:

- Aggregate the result directories.
- Write `benchmarks/pilots/xfast-vs-fast/result.json`.
- Record run IDs, model versions, the repository commit, and limitations.
- Confirm aggregate generation is deterministic.

## Task 10: Publish the Measured README Section

Update `README.md` only after benchmark results exist.

Add `nerd-xfast` to the Skills table and add the exact heading:

```markdown
## Now available xfast!
```

The generated section must compare regular Fast and XFast for Luna, Terra,
Sol, and the combined result. It must show:

- Accuracy.
- Accuracy delta.
- Latency.
- Speed improvement.
- Output-token savings or increase.

Required notes:

- XFast intentionally trades accuracy, completeness, and verification breadth
  for speed.
- Each model result covers two cases and two repetitions.
- Every arm used a fresh isolated agent.
- Both arms used the same model at `high` reasoning effort.
- Results apply only to the measured coding cases.
- XFast must not be presented as safer or more accurate than regular Fast.

Use generated README markers and a check mode so published values cannot drift
from `result.json` or be entered before evidence exists.

## Task 11: Final Verification

After publishing the README section, run:

```bash
rtk python3 -m compileall -q scripts benchmarks tests
rtk git diff --check
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest discover -s tests -v
rtk python3 benchmarks/run.py xfast-publish --check ...
```

## Acceptance Criteria

- Seven public skills validate and install.
- All deterministic tests pass.
- Each model has exactly four valid benchmark pairs.
- The aggregate has exactly twelve valid pairs.
- README values match `result.json`.
- Accuracy loss is displayed and never hidden.
- Existing uncommitted work remains preserved.

## Decision Record

- **Active goal:** Plan `nerd-xfast`.
- **Decision:** Use a dedicated isolated XFast pilot without changing the main
  release benchmark matrix.
- **Reason:** This satisfies the requested experiment while preserving the
  repository's existing statistical rules.
- **Queued next:** User review, then explicitly authorized implementation.
- **Accepted trade-off:** Per-model results are directional because each model
  has only four pairs.
