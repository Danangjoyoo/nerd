# Nerd README and Benchmark Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `brainstorming-smart-execute`, which applies `superpowers:executing-plans` inline, to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder README with a sharp public introduction, accurate skill catalog, reproducible testing instructions, and benchmark results generated from committed evidence.

**Architecture:** The hand-written README owns the product message, installation, skill descriptions, supported agents, and concise methodology. A benchmark-owned marked region is generated from `summary.json`, preventing manually edited metrics. Tests enforce naming, commands, skill coverage, attribution, and exact synchronization between the README and the selected benchmark run.

**Tech Stack:** Markdown, Python 3 standard library, `unittest`, GitHub Actions, `npx skills` CLI.

**Depends on:** Both `docs/plans/2026-07-15-nerd-skills.md` and `docs/plans/2026-07-15-nerd-benchmarks.md` completed with a publishable release result.

**Implementation status (2026-07-15):** The public README, guarded evidence renderer, publisher, and CI checks are complete. Task 4 remains open because the release benchmark is blocked on Cursor authentication; the README intentionally shows the exact pending sentence and no numeric claims.

## Global Constraints

- Repository and product name is Nerd; remove all public `mensa` branding and install URLs.
- Primary install command is exactly `npx skills add danangjoyoo/nerd`.
- README lists exactly five public skills and never presents internal references as installable skills.
- Descriptions must state the trigger and outcome in one short sentence.
- README benchmark numbers must be generated from a committed `summary.json`; no hand-entered results.
- Report both accuracy score and pass rate; never collapse them into an ambiguous single “accuracy” number.
- Report latency as p50 and p95 seconds with matched-run context.
- Report Silent token savings only when provider-reported output tokens and accuracy eligibility are available.
- Mark insufficient evidence explicitly instead of naming a winner.
- Keep the root README concise: target 120 lines or fewer after generated tables.
- Link the exact raw-result directory and identify date, Nerd commit, upstream Superpowers commit, agents, models, cases, and repetitions.
- Preserve the repository MIT license and credit Superpowers-derived internal knowledge.

---

## File Structure

- Modify `README.md`: public product page and generated benchmark regions.
- Modify `benchmarks/nerdbench/report.py`: README rendering and synchronization check.
- Create `tests/test_readme.py`: static README contract and result-sync tests.
- Create `.github/workflows/ci.yml`: deterministic skill, benchmark-harness, README, and discovery checks.

---

### Task 1: Define the README contract before rewriting it

**Files:**
- Create: `tests/test_readme.py`

**Interfaces:**
- Consumes: `README.md`, the five `SKILL.md` frontmatter descriptions, and the benchmark summary selected by the README marker.
- Produces: deterministic failures for stale branding, missing skills, invalid install commands, fabricated metrics, or summary drift.

- [x] **Step 1: Write failing static-contract tests**

Create tests equivalent to:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SKILLS = (
    "nerd-smart",
    "nerd-surgery",
    "nerd-patrol",
    "nerd-execute",
    "nerd-silent",
)


class ReadmeContractTests(unittest.TestCase):
    def test_install_command_is_current(self):
        body = README.read_text()
        self.assertIn("npx skills add danangjoyoo/nerd", body)
        self.assertNotIn("danangjoyoo/mensa", body.casefold())

    def test_every_public_skill_is_listed_once(self):
        body = README.read_text()
        for name in SKILLS:
            self.assertEqual(body.count(f"`{name}`"), 1)

    def test_benchmark_markers_are_unique(self):
        body = README.read_text()
        self.assertEqual(body.count("<!-- BENCHMARK_RESULTS:START -->"), 1)
        self.assertEqual(body.count("<!-- BENCHMARK_RESULTS:END -->"), 1)

    def test_readme_remains_sharp(self):
        self.assertLessEqual(len(README.read_text().splitlines()), 120)
```

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_readme -v`

Expected: FAIL because the current README still says `mensa` and lacks the required content.

- [x] **Step 3: Add benchmark-sync test scaffolding**

Add a test that reads the run ID from the `BENCHMARK_RUN` marker, loads `benchmarks/results/$RUN_ID/summary.json`, calls the report renderer, and requires byte-for-byte equality with the content between the result markers. When no publishable run exists during initial TDD, the test must require the exact sentence `Benchmark results pending a complete release run.` and forbid numeric claims.

- [x] **Step 4: Commit the red README contract**

```bash
git add tests/test_readme.py
git commit -m "test: define nerd readme contract"
```

---

### Task 2: Rewrite the README around the five public skills

**Files:**
- Modify: `README.md`
- Modify: `tests/test_readme.py`

**Interfaces:**
- Produces: a public entry point that takes a reader from value proposition to installation, skill choice, evidence, and reproduction.

- [x] **Step 1: Replace the old brand and opening**

Use this information hierarchy:

````markdown
# Nerd

Focused operating skills for coding agents: think clearly, diagnose before fixing, audit with evidence, build against repository reality, and stay silent when narration adds no value.

## Install

```bash
npx skills add danangjoyoo/nerd
```
````

Keep the opening factual; do not claim higher intelligence, superiority, or benchmark wins before the evidence table.

- [x] **Step 2: Add the exact skill catalog**

Use these descriptions:

| Skill | Description |
| --- | --- |
| `nerd-smart` | Aligns intention, endpoint, scope, and one working specialty before substantive work. |
| `nerd-surgery` | Diagnoses broken behavior from evidence and repairs only at an authorized execute endpoint. |
| `nerd-patrol` | Examines a confirmed security scope and reports only reachable, evidence-backed findings. |
| `nerd-execute` | Implements approved plans or confirmed small changes using repository patterns and fresh proof. |
| `nerd-silent` | Suppresses optional narration and effort while preserving correctness and the complete result. |

Follow the table with one sentence: Smart routes one primary specialty; Silent composes with any active workflow.

- [x] **Step 3: Add supported-agent and attribution lines**

State that the Agent Skills layout supports Codex, Claude Code, and Cursor. State that Nerd includes shortened internal knowledge derived from MIT-licensed Superpowers and link `THIRD_PARTY_NOTICES.md`; do not tell users to install Superpowers separately.

- [x] **Step 4: Add the generated benchmark region**

Insert exactly:

```markdown
## Benchmarks

<!-- BENCHMARK_RUN:pending -->
<!-- BENCHMARK_RESULTS:START -->
Benchmark results pending a complete release run.
<!-- BENCHMARK_RESULTS:END -->
```

Add a short methodology line after the markers: paired same-agent/model runs, five cases per workflow, three repetitions, accuracy from weighted rubrics and hard gates, latency excluding setup, and tokens from provider-reported usage.

- [x] **Step 5: Add concise reproduction commands**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
python3 benchmarks/run.py plan --config benchmarks/config.json
```

For live results, link to the benchmark plan or show only `python3 benchmarks/run.py run --config benchmarks/config.json --release`; do not imply that live agent calls run in CI.

- [x] **Step 6: Run GREEN for the pending state**

Run: `python3 -m unittest tests.test_readme -v`

Expected: PASS with no numeric benchmark claims and at most 120 README lines.

- [x] **Step 7: Commit the public README shell**

```bash
git add README.md tests/test_readme.py
git commit -m "docs: introduce nerd skill family"
```

---

### Task 3: Generate README benchmark tables from release evidence

**Files:**
- Modify: `benchmarks/nerdbench/report.py`
- Modify: `benchmarks/run.py`
- Modify: `tests/test_benchmark_report.py`
- Modify: `tests/test_readme.py`

**Interfaces:**
- Produces: `render_readme_results(summary: dict) -> str`.
- Produces: `python3 benchmarks/run.py publish --results benchmarks/results/$RUN_ID --readme README.md`.
- Produces: the same command with `--check`, which verifies without writing.

- [x] **Step 1: Write failing renderer tests**

Use a fixed summary fixture and require this structure:

```markdown
| Comparison | Nerd score | Baseline score | Score delta | Nerd pass | Baseline pass | p50 latency delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Smart vs Superpowers Brainstorming | 88.0% | 80.0% | +8.0 | 80.0% | 60.0% | -12.5% |
| Surgery vs Superpowers Systematic Debugging | 84.0% | 82.0% | +2.0 | 80.0% | 80.0% | -5.0% |
| Execute vs Superpowers Executing Plans | 92.0% | 86.0% | +6.0 | 100.0% | 80.0% | +3.2% |

| Silent comparison | Regular | Silent | Change |
| --- | ---: | ---: | ---: |
| Eligible paired output tokens | 500 | 300 | -40.0% |
| Accuracy score | 90.0% | 91.0% | +1.0 |
```

These numbers are synthetic test-fixture values, not publishable benchmark results. Require percentages to one decimal place, latency to two decimals, sample counts in the accompanying sentence, and `insufficient data` rather than numeric placeholders for unsupported metrics.

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_benchmark_report tests.test_readme -v`

Expected: FAIL because README rendering is not implemented.

- [x] **Step 3: Implement pure rendering**

`render_readme_results` must not read files or mutate state. It accepts validated summary data and returns Markdown. Include:

- Release run date and ID.
- Agent/model matrix.
- Number of cases, repetitions, and valid paired runs.
- Accuracy score, pass rate, and latency for the three requested comparisons.
- Silent token savings and its accuracy delta.
- A relative link to `benchmarks/results/$RUN_ID/summary.md`.

- [x] **Step 4: Implement guarded publication**

The `publish` command must refuse to update README when:

- `publication_state` is not `publishable`.
- The summary Nerd commit differs from current `HEAD` unless `--allow-historical` is explicitly provided.
- Any requested comparison is absent.
- The README markers are missing or duplicated.
- The result directory is outside `benchmarks/results/`.

When valid, replace only the benchmark run marker and the content between result markers. Preserve all hand-written text byte-for-byte.

- [x] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest tests.test_benchmark_report tests.test_readme -v
git add benchmarks/nerdbench/report.py benchmarks/run.py tests/test_benchmark_report.py tests/test_readme.py
git commit -m "feat: publish benchmark results to readme"
```

---

### Task 4: Publish the measured result and verify every claim

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the committed publishable release result from the benchmark plan.
- Produces: a README whose benchmark table is mechanically synchronized with that result.

- [ ] **Step 1: Select the release result**

Choose the newest result directory whose `summary.json` has `publication_state: publishable` and whose manifest records all requested comparisons.

- [ ] **Step 2: Update README mechanically**

```bash
RUN_ID="$(cat benchmarks/results/LATEST)"
python3 benchmarks/run.py publish \
  --results "benchmarks/results/$RUN_ID" \
  --readme README.md \
  --allow-historical
```

Expected: only the benchmark marker and generated region change.

- [ ] **Step 3: Verify synchronization and public claims**

```bash
RUN_ID="$(cat benchmarks/results/LATEST)"
python3 benchmarks/run.py publish \
  --results "benchmarks/results/$RUN_ID" \
  --readme README.md \
  --allow-historical \
  --check
python3 -m unittest tests.test_readme -v
```

Expected: both commands pass. Manually compare the README table to `summary.md`; every number and label must match.

- [ ] **Step 4: Commit the measured README**

```bash
git add README.md
git commit -m "docs: publish nerd benchmark results"
```

---

### Task 5: Add deterministic public CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: pull-request and push verification without agent credentials or paid live benchmark calls.

- [x] **Step 1: Add a failing workflow-presence assertion**

Extend `tests/test_readme.py` to require `.github/workflows/ci.yml` and the deterministic commands below.

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_readme -v`

Expected: FAIL because the workflow is missing.

- [x] **Step 3: Create the CI workflow**

Configure checkout, Python, and Node, then run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
npx skills add . --list
python3 benchmarks/run.py plan --config benchmarks/config.json
RUN_ID="$(sed -n 's/<!-- BENCHMARK_RUN:\([^ ]*\) -->/\1/p' README.md)"
if [ "$RUN_ID" = "pending" ]; then
  grep -F "Benchmark results pending a complete release run." README.md
else
  python3 benchmarks/run.py publish --results "benchmarks/results/$RUN_ID" --readme README.md --allow-historical --check
fi
```

The workflow resolves the committed result at runtime from the README marker; it never carries a manually maintained result path.

- [x] **Step 4: Run GREEN and commit**

```bash
python3 -m unittest tests.test_readme -v
git add .github/workflows/ci.yml tests/test_readme.py
git commit -m "ci: verify nerd skills and benchmark evidence"
```

## Plan Exit Proof

Run fresh from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
npx skills add . --list
python3 benchmarks/run.py plan --config benchmarks/config.json
RUN_ID="$(sed -n 's/<!-- BENCHMARK_RUN:\([^ ]*\) -->/\1/p' README.md)"
python3 benchmarks/run.py publish --results "benchmarks/results/$RUN_ID" --readme README.md --allow-historical --check
git diff --check
git status --short
```

The publication plan is complete only when all checks pass, the README is no longer than 120 lines, exactly five public skills are listed, every benchmark number is generated from committed evidence, and the install command points to `danangjoyoo/nerd`.
