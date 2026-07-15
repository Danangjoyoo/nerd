# Nerd Comparative Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `brainstorming-smart-execute`, which applies `superpowers:executing-plans` inline, to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a reproducible benchmark that compares Nerd Smart, Surgery, Execute, and Silent with their requested baselines while conformance-testing Patrol.

**Architecture:** A Python standard-library harness materializes each benchmark condition into a fresh synthetic repository, invokes Codex, Claude Code, or Cursor through a narrow adapter, captures structured events and wall-clock time, applies deterministic checks first, and uses a blinded judge only for conversational criteria. Raw runs remain immutable JSONL; a report step derives summaries and confidence intervals. Every comparison pairs the same case, repetition, harness, and model so skill behavior is the only intended variable.

**Tech Stack:** Python 3 standard library, JSON/JSONL, `unittest`, Git, Codex CLI, Claude Code CLI, Cursor Agent CLI, Agent Skills layout.

**Depends on:** `docs/plans/2026-07-15-nerd-skills.md` completed and passing.

## Global Constraints

- Pin the upstream baseline to `obra/superpowers` tag `v6.1.1`, commit `c984ea2e7aeffdcc865784fd6c5e3ab75da0209a`.
- Compare paired runs on the same agent executable, resolved model, case, fixture revision, repetition, and permission mode.
- Exclude skill installation and fixture-copy time from agent latency.
- Explicitly invoke the compared skill to measure method quality; test implicit routing separately in deterministic conformance tests.
- Never expose rubric answers, hidden assertions, or expected root causes inside the agent workspace.
- Use synthetic fixtures only; benchmark agents must not access production systems, user secrets, or unrelated repositories.
- Accuracy score is the mean weighted rubric score from `0` to `100`.
- Accuracy pass rate is the percentage of runs scoring at least `80` and passing every hard gate.
- Report latency as paired median and p95 wall-clock seconds; retain raw samples.
- Report Silent versus Regular with three first-class outcomes: accuracy percentage, latency, and tokens saved.
- Report Silent token savings only from agent-reported output-token usage. Do not substitute word counts or tokenizer estimates.
- A Silent run is eligible for token-savings aggregation only when both paired outputs pass hard gates and its accuracy score is no more than two points below Regular; still retain its accuracy and latency samples when those measurements are valid.
- Run Patrol conformance tests but do not add a Patrol comparison to the requested public benchmark table.
- Do not run paid live benchmarks in ordinary CI; CI runs parsers, scoring, fixtures, dry-run planning, and recorded-transcript tests.
- Sanitize environment values and tool events before committing benchmark artifacts.

---

## File Structure

### Benchmark core

- Create `benchmarks/nerdbench/__init__.py`: package marker.
- Create `benchmarks/nerdbench/models.py`: immutable case, condition, run, criterion, and result dataclasses.
- Create `benchmarks/nerdbench/cases.py`: JSON case loader and schema validation.
- Create `benchmarks/nerdbench/materialize.py`: isolated fixture and skill-condition setup.
- Create `benchmarks/nerdbench/adapters.py`: Codex, Claude, and Cursor command builders and event parsers.
- Create `benchmarks/nerdbench/runner.py`: paired run scheduler, timeout handling, and raw JSONL writer.
- Create `benchmarks/nerdbench/scorer.py`: deterministic checks, blinded judge contract, pass/fail, and paired metrics.
- Create `benchmarks/nerdbench/report.py`: aggregate statistics, confidence intervals, and summary JSON.
- Create `benchmarks/run.py`: command-line entry point.
- Create `benchmarks/config.json`: public release matrix and pinned upstream source.

### Cases and fixtures

- Create `benchmarks/cases/smart.json`.
- Create `benchmarks/cases/surgery.json`.
- Create `benchmarks/cases/execute.json`.
- Create `benchmarks/cases/silent.json`.
- Create `benchmarks/cases/patrol.json`.
- Create `benchmarks/fixtures/`: synthetic repositories copied once per run.
- Create `benchmarks/judge/schema.json`: strict blinded-judge output schema.
- Create `benchmarks/judge/prompt.md`: public judge instructions without case answers.

### Tests and recorded data

- Create `tests/test_benchmark_cases.py`.
- Create `tests/test_benchmark_adapters.py`.
- Create `tests/test_benchmark_scoring.py`.
- Create `tests/test_benchmark_report.py`.
- Create `tests/fixtures/benchmark-events/`: minimal sanitized event streams for all three adapters.
- Create `benchmarks/results/.gitkeep`: retain results directory before the first live run.

---

### Task 1: Define benchmark data contracts and scoring semantics

**Files:**
- Create: `benchmarks/nerdbench/__init__.py`
- Create: `benchmarks/nerdbench/models.py`
- Create: `benchmarks/nerdbench/cases.py`
- Create: `tests/test_benchmark_cases.py`
- Create: `tests/test_benchmark_scoring.py`

**Interfaces:**
- Produces: `BenchmarkCase`, `Criterion`, `RunSpec`, `RunResult`, and `ScoreResult` dataclasses.
- Produces: `load_cases(path: Path) -> tuple[BenchmarkCase, ...]`.
- Produces: `score_run(case: BenchmarkCase, run: RunResult, judge: dict | None) -> ScoreResult`.

- [ ] **Step 1: Write failing case-loader tests**

Use this minimal contract:

```python
class BenchmarkCaseTests(unittest.TestCase):
    def test_case_weights_sum_to_one_hundred(self):
        case = load_cases(FIXTURE)[0]
        self.assertEqual(sum(item.weight for item in case.criteria), 100)

    def test_case_requires_at_least_one_hard_gate(self):
        case = load_cases(FIXTURE)[0]
        self.assertTrue(any(item.hard_gate for item in case.criteria))

    def test_duplicate_case_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate case id"):
            load_cases(DUPLICATE_FIXTURE)
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_cases -v`

Expected: FAIL because `benchmarks.nerdbench.cases` does not exist.

- [ ] **Step 3: Implement immutable data models**

Define these fields exactly:

```python
@dataclass(frozen=True)
class Criterion:
    id: str
    weight: int
    hard_gate: bool
    evaluator: str       # regex, absent_regex, file, command, or judge
    expected: str


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    comparison: str
    prompt: str
    fixture: str | None
    endpoint: str
    timeout_seconds: int
    criteria: tuple[Criterion, ...]


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    case_id: str
    condition: str
    agent: str
    model: str | None
    repetition: int
    workspace: Path


@dataclass(frozen=True)
class RunResult:
    spec: RunSpec
    exit_code: int
    elapsed_seconds: float
    final_text: str
    output_tokens: int | None
    events: tuple[dict, ...]
    changed_files: tuple[str, ...]
    command_results: dict[str, int]


@dataclass(frozen=True)
class ScoreResult:
    score: float
    passed: bool
    hard_gate_failures: tuple[str, ...]
    criterion_results: dict[str, bool]
```

- [ ] **Step 4: Implement strict JSON loading**

Reject unknown evaluator kinds, empty prompts, non-positive timeouts, duplicate criterion IDs, weights not totaling `100`, and cases without a hard gate. Keep rubric details in the runner process; write only prompt and fixture into the agent workspace.

- [ ] **Step 5: Run GREEN**

Run: `python3 -m unittest tests.test_benchmark_cases -v`

Expected: PASS.

- [ ] **Step 6: Commit the contracts**

```bash
git add benchmarks/nerdbench tests/test_benchmark_cases.py tests/test_benchmark_scoring.py
git commit -m "test: define nerd benchmark contracts"
```

---

### Task 2: Create the case corpus and synthetic fixtures

**Files:**
- Create: `benchmarks/cases/smart.json`
- Create: `benchmarks/cases/surgery.json`
- Create: `benchmarks/cases/execute.json`
- Create: `benchmarks/cases/silent.json`
- Create: `benchmarks/cases/patrol.json`
- Create: `benchmarks/fixtures/**`
- Modify: `tests/test_benchmark_cases.py`

**Interfaces:**
- Produces: five cases per public workflow, each with weights totaling `100`.
- Produces: deterministic fixture setup and proof commands for mutation-capable cases.

- [ ] **Step 1: Add failing corpus-coverage tests**

Assert these exact IDs:

```python
EXPECTED_CASES = {
    "smart": {
        "smart-ambiguous-focus",
        "smart-compound-queue",
        "smart-invalid-premise",
        "smart-plan-endpoint",
        "smart-confirmed-small-task",
    },
    "surgery": {
        "surgery-trace-source",
        "surgery-component-boundary",
        "surgery-not-reproducible",
        "surgery-repair-under-uncertainty",
        "surgery-repeated-failure",
    },
    "execute": {
        "execute-small-feature",
        "execute-written-plan",
        "execute-repository-convention",
        "execute-preexisting-failure",
        "execute-blocker",
    },
    "silent": {
        "silent-final-only",
        "silent-code-only",
        "silent-findings-only",
        "silent-minimal-report",
        "silent-verification-conflict",
    },
    "patrol": {
        "patrol-auth-pr",
        "patrol-vague-scope",
        "patrol-advisory-without-reachability",
        "patrol-secret-logging",
        "patrol-no-findings",
    },
}
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_cases.BenchmarkCorpusTests -v`

Expected: FAIL because the case files are missing.

- [ ] **Step 3: Author Smart and Surgery cases**

Use judge criteria for intention, endpoint, scope, evidence, and unsupported claims. Use deterministic absent-regex hard gates for forbidden mutations, third clarification rounds, unverified success, and multiple stacked hypotheses.

For Surgery fixtures, build small Python repositories with `unittest` tests and one seeded root cause. Store the root-cause oracle only in case criteria outside the copied workspace. Each repair fixture must expose a command such as `python3 -m unittest -v` that fails before repair and passes only after the intended minimal correction.

- [ ] **Step 4: Author Execute cases**

Use synthetic Python repositories so correctness is deterministic. Each case must include:

- One written plan or concrete acceptance contract.
- One nearest implementation/test pattern.
- One targeted proof command.
- A clean expected diff boundary.
- For `execute-preexisting-failure`, one unrelated failing test and one passing targeted proof.
- For `execute-blocker`, a deliberately missing contract input that must stop implementation.

- [ ] **Step 5: Author Silent and Patrol cases**

Silent pairs use the same active Nerd workflow in both arms; the treatment adds `nerd-silent`. Hard gates require equivalent factual content and required verification evidence. Each case must produce paired accuracy scores, paired wall-clock latency, and provider-reported output-token counts so the report can compare correctness, speed, and savings independently.

Patrol cases are conformance-only and must cover exact scope, reachability, safe proof, validation-needed classification, and no-finding language.

- [ ] **Step 6: Run corpus tests and fixture baselines**

```bash
python3 -m unittest tests.test_benchmark_cases -v
python3 -m unittest discover -s benchmarks/fixtures -p 'test_*.py' -v
```

Expected: corpus tests pass. Seeded failure fixtures fail only where their case manifest explicitly expects a baseline failure; the fixture test helper records and verifies those expected exit codes.

- [ ] **Step 7: Commit cases and fixtures**

```bash
git add benchmarks/cases benchmarks/fixtures tests/test_benchmark_cases.py
git commit -m "test: add nerd benchmark corpus"
```

---

### Task 3: Implement isolated condition materialization

**Files:**
- Create: `benchmarks/nerdbench/materialize.py`
- Create: `benchmarks/config.json`
- Modify: `tests/test_benchmark_cases.py`

**Interfaces:**
- Produces: `materialize_run(case, condition, agent, destination) -> Path`.
- Produces: `fetch_superpowers(cache_dir: Path) -> Path`, verifying the pinned tag and commit.
- Produces condition labels: `nerd-smart`, `superpowers-brainstorming`, `nerd-surgery`, `superpowers-systematic-debugging`, `nerd-execute`, `superpowers-executing-plans`, `regular`, `nerd-silent`, and `nerd-patrol`.

- [ ] **Step 1: Write failing isolation tests**

Assert that materialization:

- Creates a fresh copy of the fixture.
- Copies only the condition's skill family into the agent-specific project skill directory.
- Never copies `benchmarks/cases` or rubric content into the workspace.
- Initializes an isolated Git repository for diff measurement.
- Rejects an upstream checkout whose HEAD differs from the pinned commit.

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_cases.MaterializationTests -v`

Expected: FAIL because `materialize.py` is missing.

- [ ] **Step 3: Implement the pinned upstream fetch**

Use the repository-local cache path:

```bash
mkdir -p benchmarks/.cache
git clone --depth 1 --branch v6.1.1 https://github.com/obra/superpowers.git benchmarks/.cache/superpowers-v6.1.1
git -C benchmarks/.cache/superpowers-v6.1.1 rev-parse HEAD
```

Require the exact commit `c984ea2e7aeffdcc865784fd6c5e3ab75da0209a`. Reuse a verified cache; delete and refetch only a mismatched benchmark cache, never a user checkout.

- [ ] **Step 4: Implement condition composition**

Materialize these comparison arms:

| Comparison | Treatment | Baseline |
| --- | --- | --- |
| Smart | `nerd-smart` family | Superpowers `brainstorming` |
| Surgery | `nerd-smart` + `nerd-surgery` | `systematic-debugging` + upstream TDD/verification references |
| Execute | `nerd-smart` + `nerd-execute` | `executing-plans` + upstream TDD/verification skills |
| Silent | active Nerd workflow + `nerd-silent` | identical active Nerd workflow without Silent |
| Patrol | `nerd-smart` + `nerd-patrol` | no comparative baseline |

Use project paths `.agents/skills/`, `.claude/skills/`, and `.cursor/skills/` as appropriate. Prompt each run with an explicit skill invocation; do not include rubric text.

- [ ] **Step 5: Add the release matrix config**

Set five cases per workflow, three repetitions, and all three agents. A full release run therefore schedules `360` paired-comparison agent runs plus `45` Patrol conformance runs. Set `parallelism` to `1` by default to avoid rate-limit and machine-contention distortion.

- [ ] **Step 6: Run GREEN and commit**

```bash
python3 -m unittest tests.test_benchmark_cases.MaterializationTests -v
git add benchmarks/config.json benchmarks/nerdbench/materialize.py tests/test_benchmark_cases.py
git commit -m "feat: isolate nerd benchmark conditions"
```

---

### Task 4: Implement Codex, Claude, and Cursor adapters

**Files:**
- Create: `benchmarks/nerdbench/adapters.py`
- Create: `tests/test_benchmark_adapters.py`
- Create: `tests/fixtures/benchmark-events/codex.jsonl`
- Create: `tests/fixtures/benchmark-events/claude.json`
- Create: `tests/fixtures/benchmark-events/cursor.jsonl`

**Interfaces:**
- Produces: `AgentAdapter.build_command(spec, prompt) -> list[str]`.
- Produces: `AgentAdapter.parse(stdout, stderr) -> tuple[str, int | None, tuple[dict, ...]]`.
- Produces: adapter IDs `codex`, `claude`, and `cursor`.

- [ ] **Step 1: Write failing adapter tests**

Test command safety, workspace selection, non-interactive mode, ephemeral sessions, event parsing, final-text extraction, output-token extraction, and missing-usage behavior.

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_adapters -v`

Expected: FAIL because adapters are missing.

- [ ] **Step 3: Implement command builders**

Build argument vectors equivalent to these templates, substituting the Python variables `workspace` and `prompt` without shell interpolation:

```text
codex exec --ephemeral --json --sandbox workspace-write -C {workspace} {prompt}
claude -p --output-format json --no-session-persistence --permission-mode acceptEdits {prompt}
cursor agent -p --output-format json --trust --sandbox enabled --workspace {workspace} {prompt}
```

If `model` is configured, pass the adapter's model option; otherwise omit it and record the resolved model from output when available. Never pass bypass-permission or unsandboxed flags.

- [ ] **Step 4: Implement strict event parsing**

Return the final assistant text and provider-reported output tokens. Preserve unknown events in raw output but never guess token usage. Redact environment-like keys matching `TOKEN`, `SECRET`, `KEY`, `PASSWORD`, or `AUTH` before serialization.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest tests.test_benchmark_adapters -v
git add benchmarks/nerdbench/adapters.py tests/test_benchmark_adapters.py tests/fixtures/benchmark-events
git commit -m "feat: add nerd benchmark agent adapters"
```

---

### Task 5: Implement paired execution and immutable raw results

**Files:**
- Create: `benchmarks/nerdbench/runner.py`
- Create: `benchmarks/run.py`
- Modify: `tests/test_benchmark_adapters.py`

**Interfaces:**
- Produces: CLI `python3 benchmarks/run.py plan|run|score|report`.
- Produces: `benchmarks/results/<run-id>/manifest.json`, append-only `raw.jsonl`, and `benchmarks/results/LATEST` containing the newest completed run ID.
- Produces: `plan` output listing exact runs without invoking agents.

- [ ] **Step 1: Write failing schedule tests**

Assert that the release matrix produces `405` agent runs, every comparative run has one matched opposite arm, and rerunning an existing `run_id` refuses to overwrite raw results.

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_adapters.RunnerTests -v`

Expected: FAIL because the runner is missing.

- [ ] **Step 3: Implement deterministic scheduling**

Generate run IDs from comparison, case, agent, repetition, and condition. Randomize treatment/baseline order using a recorded seed while retaining pair identity. Use `time.monotonic()` immediately before starting the agent process and immediately after it exits.

- [ ] **Step 4: Capture repository evidence**

After every run, record:

- Exit code and elapsed seconds.
- Final text, sanitized events, and output-token usage.
- `git status --short`, changed-file paths, and diff hash.
- Configured fixture proof-command exit codes.
- Agent executable version, resolved model when available, OS, Python version, Nerd commit, and upstream commit.

- [ ] **Step 5: Implement dry-run and resume behavior**

`plan` must never invoke an agent. `run --resume RUN_ID` may append only missing scheduled runs and must preserve the original manifest, seed, and configuration. Define the CLI argument as an actual run ID in `YYYYMMDDTHHMMSSZ-<short-commit>` form.

- [ ] **Step 6: Run GREEN and commit**

```bash
python3 -m unittest tests.test_benchmark_adapters.RunnerTests -v
python3 benchmarks/run.py plan --config benchmarks/config.json
git add benchmarks/run.py benchmarks/nerdbench/runner.py tests/test_benchmark_adapters.py
git commit -m "feat: run paired nerd benchmarks"
```

Expected dry-run output: `405 planned agent runs` with no new result directory.

---

### Task 6: Implement deterministic scoring and blinded judging

**Files:**
- Create: `benchmarks/nerdbench/scorer.py`
- Create: `benchmarks/judge/schema.json`
- Create: `benchmarks/judge/prompt.md`
- Modify: `tests/test_benchmark_scoring.py`

**Interfaces:**
- Produces: deterministic criterion evaluation.
- Produces: randomized labels `A` and `B` for pairwise judge input.
- Produces: one strict JSON judge result per paired conversational case.

- [ ] **Step 1: Write failing scoring tests**

Cover weighted scoring, hard-gate failure, threshold behavior, command/file evidence, absent regex, blinded order, and refusal to score malformed judge output.

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_scoring -v`

Expected: FAIL because the scorer is incomplete.

- [ ] **Step 3: Implement deterministic evaluators**

Evaluation order must be:

1. Exit/process validity.
2. Fixture command and file assertions.
3. Required/forbidden text assertions.
4. Blinded judge criteria only where `evaluator == "judge"`.

Compute:

```python
score = sum(c.weight for c in case.criteria if criterion_results[c.id])
passed = score >= 80 and not hard_gate_failures
```

- [ ] **Step 4: Implement blinded pairwise judging**

The judge sees the user prompt, allowed scope, rubric criterion labels, and anonymized outputs A/B. It must not see skill names, condition labels, latency, token counts, or prior aggregate results. Require one boolean per judge criterion per output plus a one-sentence evidence field. Validate with `benchmarks/judge/schema.json`.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest tests.test_benchmark_scoring -v
git add benchmarks/nerdbench/scorer.py benchmarks/judge tests/test_benchmark_scoring.py
git commit -m "feat: score nerd benchmarks"
```

---

### Task 7: Aggregate accuracy, latency, and token savings

**Files:**
- Create: `benchmarks/nerdbench/report.py`
- Create: `tests/test_benchmark_report.py`
- Create: `benchmarks/results/.gitkeep`

**Interfaces:**
- Produces: `summary.json` containing per-arm samples and paired deltas.
- Produces: `summary.md` suitable for review before README publication.
- Produces: Wilson 95% intervals for pass rate and seeded bootstrap 95% intervals for mean score and median paired deltas.

- [ ] **Step 1: Write failing report tests**

Use a fixed synthetic result set to assert exact accuracy score, pass rate, median latency, p95 latency, output-token totals, paired deltas, interval bounds, and Silent eligibility filtering. The fixture must prove that an ineligible token-saving pair can still contribute valid accuracy and latency samples.

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_report -v`

Expected: FAIL because the reporter is missing.

- [ ] **Step 3: Implement aggregate definitions**

Report for Smart, Surgery, and Execute:

- Mean accuracy score `%`.
- Accuracy pass rate `%`.
- Paired accuracy-score delta.
- Median and p95 agent latency seconds.
- Median paired latency delta `%`.

Report for Silent:

- Mean Regular and Silent accuracy scores `%`.
- Regular and Silent accuracy pass rates `%`.
- Paired Silent-minus-Regular accuracy-score delta and pass-rate delta.
- Regular and Silent median and p95 agent latency seconds.
- Median paired latency delta `%` using `(silent - regular) / regular * 100`; negative means Silent is faster.
- Median output tokens for eligible Regular and Silent pairs.
- Median paired tokens saved `%` using `(regular - silent) / regular * 100`.
- Separate valid-pair counts for accuracy, latency, and token savings, plus every exclusion reason.

- [ ] **Step 4: Prevent unsupported claims**

If any requested arm has fewer than five valid paired samples, missing token usage, mismatched model identity, or malformed judge results, set its publication state to `insufficient-data`. Do not compute a headline winner for that comparison.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest tests.test_benchmark_report -v
git add benchmarks/nerdbench/report.py benchmarks/results/.gitkeep tests/test_benchmark_report.py
git commit -m "feat: report nerd benchmark metrics"
```

---

### Task 8: Run the release benchmark and freeze evidence

**Files:**
- Create: `benchmarks/results/<run-id>/manifest.json`
- Create: `benchmarks/results/<run-id>/raw.jsonl`
- Create: `benchmarks/results/<run-id>/scores.jsonl`
- Create: `benchmarks/results/<run-id>/summary.json`
- Create: `benchmarks/results/<run-id>/summary.md`

**Interfaces:**
- Consumes: authenticated local Codex, Claude, and Cursor CLIs.
- Produces: immutable, sanitized evidence for the README plan.

- [ ] **Step 1: Verify prerequisites without running cases**

```bash
codex --version
claude --version
cursor agent --version
python3 benchmarks/run.py plan --config benchmarks/config.json
```

Expected: all three executables respond and the plan lists `405` runs.

- [ ] **Step 2: Run one smoke pair per comparison and Patrol**

```bash
python3 benchmarks/run.py run --config benchmarks/config.json --smoke
python3 benchmarks/run.py score --latest
python3 benchmarks/run.py report --latest
```

Expected: eight comparative runs plus one Patrol run complete, parse, and score; results remain marked `smoke`, never publishable.

- [ ] **Step 3: Run the full release matrix**

```bash
python3 benchmarks/run.py run --config benchmarks/config.json --release
python3 benchmarks/run.py score --latest
python3 benchmarks/run.py report --latest
```

Expected: `405/405` scheduled agent runs accounted for as completed or explicitly failed; no silent omissions.

- [ ] **Step 4: Audit the evidence**

Confirm the manifest records exact agent/model versions and commits, raw records contain no credentials, every comparison has matched pairs, and summary metrics recompute identically from raw data.

- [ ] **Step 5: Commit only sanitized benchmark evidence**

```bash
RUN_ID="$(cat benchmarks/results/LATEST)"
git add "benchmarks/results/$RUN_ID" benchmarks/results/LATEST
git commit -m "bench: record nerd comparative results"
```

## Plan Exit Proof

Run fresh:

```bash
python3 -m unittest tests.test_benchmark_cases tests.test_benchmark_adapters tests.test_benchmark_scoring tests.test_benchmark_report -v
python3 benchmarks/run.py plan --config benchmarks/config.json
RUN_ID="$(cat benchmarks/results/LATEST)"
python3 benchmarks/run.py report --results "benchmarks/results/$RUN_ID" --check
git status --short
```

The benchmark plan is complete only when all harness tests pass, the release summary is reproducible from immutable raw data, all requested metrics are supported or explicitly marked insufficient, and Patrol conformance evidence exists without appearing as a comparative headline.
