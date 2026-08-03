# Nerd UFast Research, Implementation, Benchmark, and Release Plan

## Outcome

Research and build Nerd UFast as a tool-backed execution modifier, prove that
its tools are available only to the UFast benchmark condition, compare it
directly with Nerd XFast on the existing five-case XFast v3 corpus, publish
honest evidence and clearer speed-mode wording in the README, then commit,
push, open a pull request, and continue until its required checks pass.

## Confirmed Inputs

- The approved design is
  docs/specs/2026-08-03-nerd-ufast-design.md.
- UFast remains an explicitly invoked tool-backed modifier. The active
  workflow owns scope, authorization, reasoning, fallback, and proof.
- Research must resolve prompt tuning, the concrete UFast tool surface, and
  UFast-only tool integration before implementation is frozen.
- The published comparison is Nerd UFast versus Nerd XFast.
- Reuse exactly the five cases in
  benchmarks/pilots/xfast-v3-five-cases/cases.json; do not copy or rewrite
  their prompts or scoring criteria.
- Use one repetition and the existing Luna, Terra, and Sol models at high
  reasoning effort.
- Run each model with both conditions:
  5 cases × 1 repetition × 2 conditions = 10 workload runs per model.
- The complete matrix is 30 workload runs and 15 paired comparisons.
- Execution is not complete at a local implementation. Its terminal condition
  is an open pull request with committed benchmark evidence, synchronized
  README content, and passing required checks.

## KISS Breakdown

- **Required outcome:** Deliver one benchmark-relevant UFast fast path, an
  isolated UFast tool runtime, a valid 30-run UFast-versus-XFast comparison,
  evidence-generated README wording, and a green pull request.
- **Smallest change:** Add one thin public skill, one minimal namespaced tool
  runtime selected by research, one isolated benchmark condition, and one
  dedicated result/README reporter on top of the existing XFast harness.
- **Proof:** Deterministic skill and tool tests, exact condition-isolation
  tests, 30 fresh workload runs forming 15 valid pairs, generated README check
  mode, full repository validation, and green pull-request checks.
- **Not needed:** A universal agent platform, multiple language adapters,
  generic AST infrastructure, new published benchmark cases, more than one
  repetition, changes to XFast behavior, or a claim that UFast is faster when
  the evidence does not show it.

## Constraints and Non-goals

- This plan is the endpoint for the current task. It does not begin research,
  implementation, benchmarking, commits, pushes, or pull-request creation.
- Use current official primary documentation during research because MCP,
  agent tool configuration, and language-server integration can change.
- Record documentation URLs, access dates, versions, and relevant constraints
  in the research artifact.
- Do not tune the UFast prompt or tools against final benchmark outcomes and
  then publish only a favorable rerun.
- Freeze the skill, runtime, and benchmark harness before the final matrix.
- A slower but valid UFast result is still a completed experiment and must be
  reported honestly.
- Correctness, authorization, workspace containment, preservation of user
  changes, and honest verification claims remain mandatory.
- XFast must receive no UFast skill, executable, MCP configuration, tool
  metadata, or tool-call events.
- UFast tools must use an explicit UFast namespace and no other Nerd skill may
  instruct the agent to call them.
- Preserve the five existing case prompts and proof commands exactly so the
  comparison stays tied to the published XFast v3 corpus.
- One repetition makes the results directional. Do not report p95, statistical
  significance, or stable universal performance.
- Do not merge the pull request unless the user separately authorizes merging.

## Worktree and Baseline

At plan creation, the repository is on master with origin pointing to
https://github.com/Danangjoyoo/nerd.git. The worktree already contains
user-owned modifications to:

- README.md
- skills/nerd-fast/SKILL.md
- skills/nerd-fast/agents/openai.yaml
- skills/nerd-smart/SKILL.md
- skills/nerd-smart/agents/openai.yaml
- skills/nerd-xfast/SKILL.md
- skills/nerd-xfast/agents/openai.yaml
- tests/test_readme.py
- tests/test_skill_contracts.py

The UFast design specification is also untracked. Execution must reread status
and diffs before every branch, staging, commit, and push boundary. It must patch
the current files in place, preserve user changes, and stage only UFast-owned
files or hunks. It must not reset, revert, overwrite, or silently commit
unrelated work.

## Ordered Work

### Task 1: Establish the Branch and Immutable Baseline

**Files:**

- Inspect: all current modified and untracked paths
- Create branch: feat/nerd-ufast, or a non-conflicting equivalent

**Change:**

- Capture the starting commit, branch, status, and full diff before changing
  source files.
- Create the feature branch before implementation. Carry the existing dirty
  worktree without rewriting it.
- Record which existing hunks are user-owned and which later UFast changes
  overlap those files.
- Record the current XFast v3 case-file digest and checked-in result summary so
  later work can prove the case corpus did not drift.

**Proof:**

~~~bash
rtk git branch --show-current
rtk git status --short
rtk git diff --check
rtk git diff -- README.md skills tests
~~~

Expected: the feature branch is active, existing edits remain present, and the
five-case source digest is recorded before UFast changes.

### Task 2: Research and Resolve the UFast Contract

**Files:**

- Create: docs/research/2026-08-03-nerd-ufast.md
- Modify: docs/specs/2026-08-03-nerd-ufast-design.md

**Change:**

Research three connected decisions and record the evidence, alternatives,
selected direction, rejected directions, and consequences.

#### Prompt research

- Inspect the current Fast and XFast prompts, their contract tests, and
  available event evidence from prior XFast pilots.
- Define at most two UFast prompt hypotheses. The recommended hypothesis is a
  thin modifier that inherits the active workflow, selects one tool-backed fast
  path, and immediately falls back when unsupported.
- Test activation, one capability decision, tool invocation, fallback,
  verification ownership, result reporting, and incompatibility with XFast.
- Use development scenarios that are structurally similar to the final cases
  but do not reuse their functions, expected outputs, or proof commands.
- Select the smallest prompt that reliably invokes the intended tool without
  weakening scope, correctness, or proof.

#### Tool research

- Map every final XFast v3 case to its discovery, read, edit, and verification
  operations.
- Quantify which sequential model/tool rounds dominate those cases using
  existing traces when available and an explicitly non-published calibration
  run when traces are insufficient.
- Compare the existing symbol index, native search, native patching, a
  composite context operation, atomic structured editing, focused verification
  orchestration, LSP operations, and AST/codemod options.
- Reject wrappers that merely rename existing shell operations without
  reducing a measured round, improving determinism, or enforcing a safety
  property.
- Reconcile the design’s original reference/rename slice with the selected
  five feature-implementation cases. If that slice cannot serve the five
  cases, update the design to defer it and select one narrower
  benchmark-relevant vertical slice.
- Require the selected tool surface to have a legitimate fast-path role in
  every one of the five published cases. The benchmark must not measure only
  UFast fallback behavior.

#### UFast-only integration research

- Consult current official MCP and supported-agent tool configuration
  documentation.
- Compare a persistent MCP server with a transport-independent core plus a
  CLI/stdio adapter. Prefer the smallest option that can be installed
  reproducibly in fresh isolated benchmark homes.
- Determine the exact production-install and benchmark-materialization
  boundaries.
- Define UFast-only isolation at three levels:
  namespaced tool names, condition-specific installation/configuration, and
  event-level proof that XFast cannot see or call UFast tools.
- Determine whether the first release is portable across Codex, Claude, and
  Cursor or explicitly limited to the agents with verified tool integration.
  README wording must match the evidence.

**Decision gates:**

- One prompt contract is selected.
- One minimal tool contract is selected and mapped to all five cases.
- One transport and configuration path is selected.
- Exact failure, fallback, path-containment, atomicity, and telemetry behavior
  is specified.
- UFast-only isolation is enforceable in the benchmark harness.
- No critical implementation decision remains Unknown.

**Proof:**

- The research artifact includes sources, a five-case operation map, prompt
  comparison, tool comparison, integration comparison, and final decisions.
- The design specification incorporates the selected vertical slice and no
  longer contradicts the benchmark corpus.

### Task 3: Create and Tune the UFast Skill Contract

**Files:**

- Create: skills/nerd-ufast/SKILL.md
- Create: skills/nerd-ufast/agents/openai.yaml
- Modify: tests/test_skill_contracts.py

**Change:**

- Implement the frozen prompt as an explicit-only global modifier.
- Require a resolved endpoint, scope, authorization, and active workflow.
- Name only the selected UFast tool surface and its exact invocation policy.
- Allow one capability decision and one evidence-driven tool retry only when
  the first failure identifies an exact recoverable invocation problem.
- Fall back immediately for unsupported, ambiguous, unavailable, or unsafe
  operations.
- Preserve active-workflow verification instead of inventing a second proof
  ladder.
- State that UFast and XFast do not compose.
- Require the final response to disclose whether the UFast fast path ran,
  fell back, or failed.
- Keep the prompt compact and enforce its final word ceiling in contract tests.
- Tune only with the development scenarios defined in Task 2. Freeze the
  prompt before running the final five-case matrix.

**Proof:**

~~~bash
rtk python3 -m unittest tests.test_skill_contracts -v
rtk python3 scripts/validate_skills.py
~~~

Expected: activation, composition, tool-use, fallback, proof ownership,
reporting, and compactness contracts pass.

### Task 4: Build the Minimal UFast Tool Runtime

**Files:**

- Create: tools/nerd_tools/__init__.py
- Create: tools/nerd_tools/core.py
- Create: tools/nerd_tools/server.py
- Create: tests/test_ufast_tools.py

**Change:**

- Implement only the tool operations selected by Task 2.
- Keep the core transport-independent; keep server/configuration logic at the
  edge.
- Validate workspace roots, normalized paths, symlink escapes, requested file
  scope, and expected file hashes before mutation.
- Make multi-file changes atomic or fully recoverable.
- Return structured statuses for applied, unsupported, ambiguous, stale,
  rejected, and failed operations.
- Bound output size and reject arbitrary out-of-contract command execution.
- Emit operation name, tool/runtime version, cold-start duration, operation
  duration, changed paths, fallback reason, and verification handoff data.
- Avoid network access and automatic dependency or language-server
  installation during task execution.
- If research selects a persistent process, make lifecycle and clean shutdown
  deterministic in isolated homes.

**Proof:**

- Unit tests cover successful fast-path behavior, stale hashes, ambiguity,
  out-of-root paths, symlink escape, partial-write rollback, malformed
  requests, bounded output, and deterministic result envelopes.
- A local protocol smoke test starts the runtime, performs one read-only and
  one mutating operation, and shuts it down without leaving workspace state.

### Task 5: Register UFast and Isolate Its Tools

**Files:**

- Modify: scripts/validate_skills.py
- Modify: scripts/install.sh
- Modify: scripts/install_hooks.py, only if selected integration requires it
- Modify: tests/test_skill_structure.py
- Modify: tests/test_install.py
- Modify: tests/test_workflows.py
- Modify: tests/test_skill_contracts.py
- Modify: .github/workflows/release.yml
- Create: tests/test_ufast_integration.py

**Change:**

- Register nerd-ufast as the eighth public skill.
- Package the selected runtime and its metadata without changing other skill
  behavior.
- Keep UFast tool names under the selected UFast namespace.
- Ensure no Smart, Execute, Fast, XFast, Surgery, Patrol, or Silent prompt
  references those names.
- Configure the runtime only for an explicit UFast install/profile when the
  host supports condition-specific configuration.
- Where a host exposes installed tools globally, enforce namespace and prompt
  ownership and disclose that host limitation instead of claiming stronger
  isolation.
- Preserve repeatable installation and existing user configuration.
- Extend release packaging checks to include the skill and required runtime
  assets.

**Proof:**

- Installation tests prove an explicit UFast profile receives the runtime and
  configuration.
- Non-UFast profiles preserve their previous files and configuration.
- Reinstallation is idempotent.
- Public skill, metadata, runtime assets, and release counts validate.

### Task 6: Calibrate Prompt and Tool Integration Before Evaluation

**Files:**

- Create: benchmarks/cases/ufast-calibration.json
- Create: the smallest fixture set under benchmarks/fixtures/ufast-calibration/
- Modify: tests/test_ufast_integration.py
- Modify: docs/research/2026-08-03-nerd-ufast.md

**Change:**

- Add development-only cases covering each selected tool route without copying
  the five final benchmark behaviors.
- Use one model for calibration and keep all calibration outputs out of the
  published result directory and README.
- Iterate prompt wording, tool schemas, and runtime configuration until:
  the intended tool is visible only in UFast, each calibration task invokes
  it, deterministic proof passes, and unsupported work falls back correctly.
- Record every material prompt/tool change and the reason. Do not choose a
  variant solely because it produced a favorable latency sample.
- Freeze and record hashes for SKILL.md, runtime files, benchmark harness, and
  final case corpus after calibration passes.

**Proof:**

- Calibration completes with no UFast tool available in the control
  workspace.
- The frozen hashes are recorded before any final benchmark run.

### Task 7: Add the UFast-versus-XFast Benchmark Conditions

**Files:**

- Modify: benchmarks/nerdbench/materialize.py
- Modify: benchmarks/nerdbench/runner.py
- Modify: benchmarks/nerdbench/adapters.py, if tool events need normalization
- Modify: benchmarks/nerdbench/models.py, if structured tool telemetry is new
- Modify: benchmarks/nerdbench/scorer.py
- Create: benchmarks/pilots/ufast-vs-xfast/gpt-5.6-luna-high.json
- Create: benchmarks/pilots/ufast-vs-xfast/gpt-5.6-terra-high.json
- Create: benchmarks/pilots/ufast-vs-xfast/gpt-5.6-sol-high.json
- Create: tests/test_ufast_benchmark.py

**Change:**

- Point all three configurations directly at
  benchmarks/pilots/xfast-v3-five-cases/cases.json.
- Define exactly two isolated conditions:
  - nerd-xfast: install and invoke only nerd-xfast.
  - nerd-ufast: install and invoke nerd-smart, nerd-execute, and nerd-ufast,
    plus the selected UFast runtime/configuration.
- Do not add nerd-fast to the UFast arm; the comparison must isolate UFast
  rather than Fast-plus-UFast.
- Give every workload a fresh fixture workspace, temporary home, temporary
  Codex home, and agent process.
- Reuse only the existing authentication handoff required by the harness.
- Keep model, high effort, prompt, timeout, proof commands, and repetition
  identical within each pair.
- Use parallelism one so tool-server and model contention cannot distort
  paired latency.
- Capture normalized UFast tool-call identity and timing without recording
  credentials or unrelated user data.
- Reject a UFast treatment run that cannot prove at least one selected UFast
  tool was invoked.
- Reject any XFast run containing a UFast runtime file, configuration entry,
  advertised tool, or tool-call event.

**Expected matrix:**

~~~text
5 cases × 1 repetition × 2 conditions × 3 models = 30 workload runs
15 UFast-versus-XFast pairs
~~~

**Proof:**

- Each model configuration plans exactly ten workload runs.
- Materialization tests prove exact skill sets and tool isolation.
- Case-file digest matches the Task 1 baseline.

### Task 8: Add Strict UFast Result and README Generation

**Files:**

- Create: benchmarks/nerdbench/ufast_report.py
- Modify: benchmarks/run.py
- Modify: tests/test_ufast_benchmark.py
- Modify: tests/test_readme.py

**Change:**

- Add dedicated ufast-report and ufast-publish commands.
- Require exactly three result directories: Luna, Terra, and Sol at high
  effort.
- Require exactly five cases, one repetition, two conditions, five pairs per
  model, and fifteen aggregate pairs.
- Reject missing, duplicate, mismatched, resumed-from-different-source, or
  non-isolated evidence.
- Report per-model and aggregate:
  mean accuracy, pass rate, hard-gate failures, accuracy delta, median latency,
  paired median speed delta, output-token change, UFast tool-hit rate, fallback
  count, cold-start time, and tool-operation time.
- State that one repetition and five coding cases are directional evidence.
- Render negative speed or token results as slower or more tokens rather than
  hiding them behind a positive label.
- Generate README content from result.json and support check mode so prose,
  tables, and values cannot drift.

**Proof:**

- Reporter tests cover valid evidence, every rejection path, unavailable
  tokens, negative deltas, tool-isolation failures, and deterministic output.

### Task 9: Run Deterministic Validation Before Live Benchmarks

**Files:**

- Validate all completed source, skill, test, benchmark, and documentation
  files.

**Change:**

- Run focused tool, integration, skill, installation, benchmark, and README
  tests first.
- Run the complete repository suite only after focused checks pass.
- Validate the three schedules and frozen hashes.
- Do not begin paid/live agent runs while deterministic validation is failing.

**Proof:**

~~~bash
rtk python3 -m compileall -q scripts benchmarks tools tests
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest tests.test_ufast_tools tests.test_ufast_integration tests.test_ufast_benchmark -v
rtk python3 -m unittest discover -s tests -v
rtk git diff --check
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/ufast-vs-xfast/gpt-5.6-luna-high.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/ufast-vs-xfast/gpt-5.6-terra-high.json
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/ufast-vs-xfast/gpt-5.6-sol-high.json
~~~

Expected: all checks pass and every plan reports exactly ten agent runs.

### Task 10: Execute and Complete the 30-Run Matrix

**Files:**

- Create: benchmarks/pilots/ufast-vs-xfast/result.json
- Retain immutable live evidence under the existing ignored results directory

**Change:**

- Run Luna, Terra, and Sol configurations sequentially without modifying the
  frozen skill, runtime, harness, or case corpus between runs.
- For each model, complete all ten workload agents, blinded judging, and
  deterministic scoring.
- Resume interrupted infrastructure work through the existing immutable resume
  mechanism instead of silently replacing completed evidence.
- Continue through transient failures until every expected run and judge task
  is present.
- If a correctness or tool-isolation defect requires source changes, preserve
  the failed run, fix the defect, rerun deterministic validation, assign a new
  benchmark run ID, and rerun the complete three-model matrix.
- If a valid frozen matrix shows UFast is slower, do not retune on those final
  outputs. Complete the report and publish the unfavorable result honestly.
- Aggregate only three result directories with identical frozen provenance.
- Re-run report generation in check mode to prove determinism.

**Execution pattern for each model:**

~~~bash
rtk python3 benchmarks/run.py run --config <model-config>
rtk python3 benchmarks/run.py judge --config <model-config> --results <result-directory>
rtk python3 benchmarks/run.py score --config <model-config> --results <result-directory>
~~~

**Aggregation:**

~~~bash
rtk python3 benchmarks/run.py ufast-report --results <luna-results> <terra-results> <sol-results> --output benchmarks/pilots/ufast-vs-xfast/result.json
~~~

Expected: 30 workload runs, 15 complete pairs, three model summaries, one
aggregate summary, full provenance, and explicit limitations.

### Task 11: Rewrite README Positioning and Publish UFast Evidence

**Files:**

- Modify: README.md
- Modify: benchmarks/nerdbench/ufast_report.py
- Modify: tests/test_readme.py
- Modify: tests/test_ufast_benchmark.py

**Change:**

- Preserve and improve the current user-owned Smart, Fast, and XFast wording.
- Add UFast to the skill table as a tool-backed fast path for supported
  operations, with explicit fallback and no universal speed promise.
- Replace the isolated promotional XFast framing with one cohesive speed-mode
  explanation:
  - Smart aligns the work.
  - Fast reduces critical-path latency without deliberate accuracy loss.
  - XFast pursues rapid output with explicitly reduced exploration and proof.
  - UFast moves supported mechanical work into deterministic tools.
- Add a short selection table explaining when to choose Fast, XFast, or UFast
  and the trade-off each accepts.
- Publish a generated UFast-versus-XFast section only after result.json exists.
- Show Luna, Terra, Sol, and aggregate accuracy, latency, speed delta, output
  tokens, and UFast tool-hit/fallback data.
- State the exact five-case, one-repetition, three-model, fresh-agent controls.
- State which agent/tool hosts were actually verified.
- Use the measured wording:
  faster, slower, equal within displayed precision, fewer tokens, or more
  tokens. Never imply a win that result.json does not support.
- Do not say ten times faster unless the frozen aggregate evidence measures
  that result.

**Proof:**

~~~bash
rtk python3 benchmarks/run.py ufast-publish --summary benchmarks/pilots/ufast-vs-xfast/result.json --readme README.md
rtk python3 benchmarks/run.py ufast-publish --summary benchmarks/pilots/ufast-vs-xfast/result.json --readme README.md --check
rtk python3 -m unittest tests.test_readme tests.test_ufast_benchmark -v
~~~

Expected: README guidance is coherent, benchmark prose matches result.json,
and check mode detects any drift.

### Task 12: Run Final Repository and Release Validation

**Files:**

- Validate the complete intended UFast change set.

**Change:**

- Repeat all deterministic checks after README generation.
- Verify public skill discovery and installation.
- Inspect the final diff for accidental case changes, secrets, generated
  runtime state, benchmark workspaces, credentials, or unrelated user hunks.
- Confirm the XFast v3 case digest remains unchanged.

**Proof:**

~~~bash
rtk python3 -m compileall -q scripts benchmarks tools tests
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest discover -s tests -v
rtk npx skills add . --list
rtk python3 benchmarks/run.py ufast-publish --summary benchmarks/pilots/ufast-vs-xfast/result.json --readme README.md --check
rtk git diff --check
rtk git status --short
~~~

Expected: all relevant validation passes, no unintended artifacts are tracked,
and only the intended UFast change set is ready to stage.

### Task 13: Commit, Push, Open the Pull Request, and Reach Green CI

**Files:**

- Stage only reviewed UFast-owned files and hunks
- Create no permanent PR-body artifact unless repository convention requires it

**Change:**

- Respect the hard dependency order: commit first, push second, create the pull
  request third.
- Review staged content separately from unstaged user-owned changes.
- Commit the complete intended change with a focused message such as:
  [FEAT] add Nerd UFast tool-backed execution path.
- Push the feature branch to origin without force.
- Open a pull request against master containing:
  summary, research decisions, tool/isolation design, deterministic tests,
  exact 30-run matrix, result table, limitations, README-generation proof, and
  disclosure of any unsupported agent hosts.
- Retrieve the PR URL and verify its base, head, state, and commit.
- Watch required checks. For any related failure, diagnose it, make the
  smallest correction, rerun relevant local proof, commit, push, and continue
  watching.
- Stop only when the PR is open and all required checks are green, or when an
  external authority/credential/service blocker makes completion impossible
  and has been exhausted without destructive workarounds.
- Do not merge the PR.

**Proof:**

~~~bash
rtk git diff --cached --check
rtk git status --short
rtk git commit -m "[FEAT] add Nerd UFast tool-backed execution path"
rtk git push -u origin feat/nerd-ufast
rtk gh pr create --base master --head feat/nerd-ufast --title "Add Nerd UFast tool-backed execution path" --body-file <prepared-pr-body>
rtk gh pr view --json url,state,headRefName,baseRefName,commits,statusCheckRollup
rtk gh pr checks --watch
~~~

Expected: one open PR against master, the intended commit history is pushed,
required checks are green, and the PR URL is reported.

## Final Validation

The final execution report must include:

- Selected prompt, tool, and integration decisions.
- Exact public skill and runtime files.
- Deterministic test and validation commands with results.
- Three immutable benchmark run IDs and source hashes.
- 30 workload runs and 15 valid pairs.
- Per-model and aggregate UFast-versus-XFast results.
- UFast tool-hit and XFast isolation evidence.
- Generated README check result.
- Commit SHA, pushed branch, PR URL, and required-check status.

No favorable benchmark result is required for honesty, but no missing run,
hidden failure, stale README, unpushed commit, absent PR, or unresolved required
check counts as completion.

## Acceptance Criteria

- Prompt, tool, and UFast-only integration research is recorded and resolves
  every critical design question.
- The design specification matches the selected benchmark-relevant vertical
  slice.
- UFast is an explicit tool-backed modifier with deterministic fallback.
- Eight public skills validate and install.
- UFast tools are namespaced, workspace-contained, recoverable, and tested.
- Every UFast benchmark run proves a selected UFast tool was invoked.
- Every XFast benchmark run proves UFast tools were unavailable.
- The exact existing five XFast v3 cases remain unchanged.
- Luna, Terra, and Sol each contribute five pairs at high effort.
- The aggregate contains exactly 15 pairs from 30 fresh workload runs.
- Accuracy loss, slower latency, extra tokens, fallbacks, and limitations are
  shown rather than filtered.
- README content is generated from the checked-in result and passes check mode.
- Existing unrelated worktree changes remain preserved and uncommitted unless
  separately authorized.
- The intended UFast change is committed, pushed, and represented by an open
  pull request with green required checks.

## Self-Review

- **Completeness:** Research, prompt tuning, tool creation, UFast-only
  integration, deterministic proof, the fixed five-case/one-repetition/
  three-model matrix, README wording, commit, push, PR creation, and CI
  completion are all covered.
- **Simplicity:** The plan selects one benchmark-relevant vertical slice and
  reuses the existing case corpus and benchmark framework. Multi-language,
  generic AST, and universal-router work remain excluded.
- **Risks:** The original rename/reference slice does not naturally exercise
  the five selected feature cases; Task 2 must resolve that contradiction
  before code. One repetition is directional, tool isolation depends on host
  configuration, and the dirty worktree contains overlapping README/test
  changes. The research gate, condition-isolation tests, honest reporting, and
  selective staging address these risks.

## Decision Record

- **Active goal:** Plan Nerd UFast through a green pull request.
- **Decision:** Compare UFast directly with XFast on the exact five XFast v3
  cases, one repetition, and Luna, Terra, and Sol at high effort.
- **Reason:** This preserves the requested established corpus while producing
  15 paired results and testing UFast across all current XFast task shapes.
- **Queued next:** User review, then execution of this plan.
- **Accepted trade-off:** The results are directional, and the initial UFast
  tool slice must be revised if research confirms it cannot exercise these
  feature cases.
