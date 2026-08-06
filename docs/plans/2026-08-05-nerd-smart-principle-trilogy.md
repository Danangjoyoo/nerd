# Nerd Smart Principle Trilogy (KISS / DRY / YAGNI) Implementation Plan

> **Status: partially superseded.** This plan describes a three-principle,
> first-match ladder. The shipped design has four principles — DRY, KISS, YAGNI
> (scripting only), and Comprehensive — where DRY composes with the selected
> scale principle instead of competing with it. Tasks 1-10 were executed as
> written; the selection rules in Task 3 were later replaced. See
> `benchmarks/pilots/smart-principle-two-cases/result.json` for the pilot
> outcome and its caveats.

## Outcome

Nerd Smart selects exactly one implementation principle — KISS, DRY, or YAGNI —
at the Plan and Execute endpoints, states it in a single `Principle Breakdown`
artifact, and justifies the choice from evidence. Three new references define
each principle. A two-case pilot benchmark measures baseline against the change
on two models.

This document is the review boundary. Do not implement until the user approves
this plan.

## Confirmed Inputs

- Add three references under `skills/nerd-smart/references/`: `kiss.md`,
  `dry.md`, `yagni.md`.
- `SKILL.md` gains a mapping of endpoint and condition to principle.
- Output shape: **one** block named `Principle Breakdown` carrying a
  `**Principle:**` field plus the existing four fields, whose meaning adapts per
  principle reference. (User decision.)
- Benchmark baseline comes from a **frozen snapshot condition**, following the
  `nerd-ufast` precedent, so both arms run in one command. (User decision.)
- Benchmark shape: 2 cases, 1 repetition, 2 targets — `claude-sonnet-4-6`
  medium and `claude-opus-4-8` medium — each with a baseline and an
  after-improvement condition.
- Principle semantics agreed during brainstorming:
  - KISS is the default and is structural: fewest concepts, files, and
    boundaries right now.
  - DRY overrides KISS only on **proven existing** duplication (rule of three)
    or a cross-module contract that will drift; never on predicted duplication.
  - YAGNI is temporal: cut speculative features, configuration, and extension
    points from a simple task. It never strips work an approved architectural
    outcome requires.

## Principle Breakdown

- **Principle:** KISS
- **Required outcome:** Nerd Smart emits one principle selection with evidence
  at Plan and Execute; three references exist; a paired pilot reports baseline
  versus change.
- **Smallest change:** Rename and extend the one existing KISS section in
  `skills/nerd-smart/SKILL.md`, add three reference files, update the two
  registries that pin them (`scripts/validate_skills.py`,
  `tests/test_skill_contracts.py`), update the single downstream row in
  `nerd-execute`, and add one pilot directory reusing the existing harness.
- **Proof:** `python3 scripts/validate_skills.py` and
  `python3 -m unittest discover -s tests -v` pass; the pilot produces a scored
  paired result for both targets.
- **Not needed:** No new selection engine, no scoring heuristic in code, no
  principle field in `nerd-fast`/`nerd-patrol`/`nerd-silent`, no change to
  `nerd-xfast`, no new report module, no README benchmark publication.

## Constraints and Non-goals

- `skills/nerd-xfast/SKILL.md` is contractually self-contained
  (`tests/test_skill_contracts.py:1010-1030` asserts it never names another Nerd
  skill). Its existing "KISS-first" wording stays untouched.
- `scripts/validate_skills.py:21-43` pins the exact reference list for
  `nerd-smart`; new files fail validation until registered.
- `tests/test_skill_contracts.py` pins literal strings at lines ~196-228
  (KISS discipline), ~346 (`plan-template.md`), and ~596-623 (`nerd-execute`
  discipline row). Renaming the block requires editing those assertions in the
  same change.
- `benchmarks/nerdbench/materialize.py:160-168` hardcodes the one out-of-tree
  skill source (`nerd-ufast`). A second frozen source needs a small,
  data-driven source map rather than a second `if`.
- The frozen baseline snapshot must be taken **before** any `SKILL.md` edit.
- Non-goal: changing endpoint semantics, the Focus Record, Multi-Goal Intake, or
  routing rules.

## Worktree and Baseline

- Branch `master`, clean tree at plan time.
- Run `python3 -m unittest discover -s tests -v` before Task 1 and record any
  pre-existing failure so it is not attributed to this change.

## Ordered Work

### Task 1: Freeze the current Nerd Smart as a benchmark baseline

**Files:**

- Create: `docs/experiments/nerd-smart-principle-baseline/skill/` (verbatim copy
  of today's `skills/nerd-smart/`)
- Create: `docs/experiments/nerd-smart-principle-baseline/README.md`

**Change:**

- Copy `skills/nerd-smart/` unmodified, including `references/`, `scripts/`, and
  `agents/`. The `README.md` records the source commit and states the snapshot
  exists only as a benchmark control and is not installed.

**Proof:**

- `diff -r skills/nerd-smart docs/experiments/nerd-smart-principle-baseline/skill`
  reports no differences.

### Task 2: Add the three principle references

**Files:**

- Create: `skills/nerd-smart/references/kiss.md`
- Create: `skills/nerd-smart/references/dry.md`
- Create: `skills/nerd-smart/references/yagni.md`

**Change:**

Each reference is short, original prose in the house style of
`references/brainstorming.md`, and each covers the same four headings so the
model can compare them:

- **Use When** — the evidence conditions that select this principle.
- **Field Meaning** — how `Required outcome`, `Smallest change`, `Proof`, and
  `Not needed` are interpreted under this principle.
- **Guardrails** — what this principle must not be used to justify.
- **Endpoint** — the stopping boundary; the principle never advances the
  endpoint.

Principle-specific content:

- `kiss.md`: default choice. Structural simplicity now. `Smallest change` is the
  most direct existing path. Guardrail: KISS may knowingly leave duplication in
  place; record that trade-off rather than pre-abstracting.
- `dry.md`: selected only on observed duplication at three or more call sites,
  or a single behavior that must change in several places, or a cross-module
  contract that will drift. `Smallest change` names the single source of truth
  and every call site being unified. Guardrail: never chosen on predicted
  duplication, and never a licence for a general framework.
- `yagni.md`: selected when a simple task carries speculative features,
  configuration, or extension points that the confirmed outcome does not
  require. `Not needed` is the primary field and lists what is deliberately
  deferred. Guardrail: never used to strip work required by an approved
  architectural outcome, a correctness constraint, or a security constraint.

**Proof:**

- Files exist and each contains all four headings; `rg '^## ' skills/nerd-smart/references/{kiss,dry,yagni}.md`
  shows the same heading set.

### Task 3: Add principle selection to `SKILL.md`

**Files:**

- Modify: `skills/nerd-smart/SKILL.md`

**Change:**

- Rename `## KISS Implementation Discipline` to
  `## Principle Selection and Discipline`.
- Insert the selection table before the breakdown template:

  | Condition observed in the confirmed scope | Principle | Reference |
  | --- | --- | --- |
  | Default; single call site; local change; unclear future | KISS | `references/kiss.md` |
  | Duplication already exists at three or more call sites, one behavior must change in several places, or a cross-module contract will drift | DRY | `references/dry.md` |
  | A simple task carries speculative features, configuration, or extension points the confirmed outcome does not require | YAGNI | `references/yagni.md` |

- State the tie-break explicitly: KISS is the default; DRY overrides KISS only
  on proven existing duplication; YAGNI never removes work an approved
  architectural outcome requires. Select exactly one principle and load exactly
  one reference.
- Replace the `**KISS Breakdown**` block with:

  > **Principle Breakdown**
  > - **Principle:** [KISS, DRY, or YAGNI plus the deciding evidence]
  > - **Required outcome:** [Smallest observable behavior that must change]
  > - **Smallest change:** [Most direct path under the selected principle]
  > - **Proof:** [Focused check that demonstrates the outcome]
  > - **Not needed:** [Excluded abstractions, refactors, infrastructure, or future features]

- Keep every surrounding rule intact: subordinate to the Focus Record, shown
  immediately after it, no second confirmation when clear, stop when **Proof**
  passes, and out of scope means out of scope.
- Update the **Plan** and **Execute** rows in Endpoint Mapping from
  "Create a KISS breakdown alongside it" to "Create a principle breakdown
  alongside it".

**Proof:**

- `python3 scripts/validate_skills.py` passes (after Task 4).
- Manual read confirms the section appears once and no orphan "KISS Breakdown"
  string remains in `skills/nerd-smart/`.

### Task 4: Register the new references in the validator

**Files:**

- Modify: `scripts/validate_skills.py`

**Change:**

- Add `"kiss.md"`, `"dry.md"`, `"yagni.md"` to
  `REQUIRED_REFERENCES["nerd-smart"]`.

**Proof:**

- `python3 scripts/validate_skills.py` exits `0`.

### Task 5: Align the plan template and the downstream execute contract

**Files:**

- Modify: `skills/nerd-smart/references/plan-template.md`
- Modify: `skills/nerd-execute/SKILL.md`

**Change:**

- `plan-template.md`: rename `## KISS Breakdown` to `## Principle Breakdown` and
  add the `**Principle:**` line as the first bullet.
- `nerd-execute`: rename the discipline row `| **KISS** | Mandatory |` to
  `| **Principle** | Mandatory |` and reword it to obey Nerd Smart's Principle
  Breakdown, defaulting to KISS when the handoff omits the principle. Keep the
  existing "Apply KISS throughout execution" paragraph's intent but generalize
  it to the selected principle without adding a user-facing gate.

**Proof:**

- `rg -n 'KISS Breakdown' skills/` returns nothing.

### Task 6: Update the pinned contract tests

**Files:**

- Modify: `tests/test_skill_contracts.py`

**Change:**

- `test_kiss_discipline_defines_compact_breakdown` (~line 196): rename to
  `test_principle_discipline_defines_compact_breakdown`, split on
  `## Principle Selection and Discipline`, assert `Create a principle breakdown`
  in the Plan and Execute rows, and assert the new terms:
  `**Principle Breakdown**`, `**Principle:**`, `KISS, DRY, or YAGNI`,
  `references/kiss.md`, `references/dry.md`, `references/yagni.md`,
  `Select exactly one principle`, plus the retained
  `Treat **Not needed** as out of scope` and `stop when **Proof** passes`.
- `test_multi_goal_intake_...` (~line 156): update the section split string.
- Template assertions (~line 346): `## KISS Breakdown` becomes
  `## Principle Breakdown`.
- `nerd-execute` discipline test (~lines 596-623): change the row regex
  alternation `KISS` to `Principle` and the literal
  `| **KISS** | Mandatory |` to `| **Principle** | Mandatory |`.
- Leave every `nerd-xfast` assertion unchanged.

**Proof:**

- `python3 -m unittest discover -s tests -v` passes.

### Task 7: Teach the harness the frozen baseline condition

**Files:**

- Modify: `benchmarks/nerdbench/materialize.py`

**Change:**

- Add `"nerd-smart-baseline": ("nerd-smart-baseline",)` to `LOCAL_CONDITIONS`.
- Replace the hardcoded `nerd-ufast` branch in `_install_condition` with a
  module-level `OUT_OF_TREE_SKILL_SOURCES` map holding both `nerd-ufast` and
  `nerd-smart-baseline`, and install the skill under the directory name
  `nerd-smart` so the agent sees the same skill identity in both arms.

**Proof:**

- New unit test in `tests/test_benchmark_cases.py` materializes the
  `nerd-smart-baseline` condition into a temporary directory and asserts
  `.claude/skills/nerd-smart/SKILL.md` exists and matches the snapshot.

### Task 8: Add the two-case pilot and its fixture

**Files:**

- Create: `benchmarks/pilots/smart-principle-two-cases/cases.json`
- Create: `benchmarks/fixtures/smart-principle-duplication/` (a small Python
  module with the same validation logic copy-pasted at three call sites, plus
  its test)

**Change:**

- Case 1 `smart-principle-dry`: `comparison` `smart`, `endpoint` `plan`,
  `fixture` `smart-principle-duplication`. Prompt asks for a plan to change the
  shared validation rule. Criteria: a `judge` criterion (weight 70) expecting
  the response to select DRY, cite the three existing call sites as the
  evidence, and name a single source of truth; an `absent_regex` hard gate
  (weight 30) blocking implementation claims.
- Case 2 `smart-principle-yagni`: `comparison` `smart`, `endpoint` `plan`,
  `fixture` `null`. Prompt requests a tiny utility plus speculative extras
  (plugin registry, config file, future backends). Criteria: a `judge`
  criterion (weight 70) expecting YAGNI selection with the speculative extras
  listed under **Not needed**; an `absent_regex` hard gate (weight 30) blocking
  a plugin-registry or config-system design.
- Both cases use `timeout_seconds` 300 and only fields in
  `benchmarks/nerdbench/cases.py:CRITERION_FIELDS`.

**Proof:**

- `python3 -c "from benchmarks.nerdbench.cases import load_cases; print(load_cases(['benchmarks/pilots/smart-principle-two-cases/cases.json']))"`
  loads without error.

### Task 9: Add the two medium-effort target configs

**Files:**

- Create: `benchmarks/pilots/smart-principle-two-cases/claude-sonnet-4-6-medium.json`
- Create: `benchmarks/pilots/smart-principle-two-cases/claude-opus-4-8-medium.json`

**Change:**

- Copy the shape of `benchmarks/pilots/xfast-v3-five-cases/gpt-5.6-luna-high.json`.
- `agents: ["claude"]`; `models.claude` is `claude-sonnet-4-6` and
  `claude-opus-4-8` respectively; `target.reasoning_effort` is `"medium"`;
  `case_files` is the pilot `cases.json`;
  `conditions: {"smart": ["nerd-smart-baseline", "nerd-smart"]}`;
  `repetitions: 1`; `parallelism: 1`; keep the existing `seed` and pinned
  `upstream` block; keep the standard `judge` block.
- Confirm the Claude CLI accepts `--effort medium`
  (`benchmarks/nerdbench/adapters.py:188`) before the real run; if it does not,
  stop and report rather than silently substituting an effort level.

**Proof:**

- `python3 benchmarks/run.py plan --config benchmarks/pilots/smart-principle-two-cases/claude-sonnet-4-6-medium.json`
  lists exactly 4 runs (2 cases x 2 conditions x 1 repetition), same for the
  Opus config.

### Task 10: Add a pilot regression test

**Files:**

- Create: `tests/test_smart_principle_pilot.py`

**Change:**

- Follow `tests/test_second_pilot.py`. Assert both target configs exist, name
  the expected models, set `reasoning_effort` `"medium"` and `repetitions` 1,
  reference the pilot `cases.json`, and declare the exact condition pair
  `["nerd-smart-baseline", "nerd-smart"]`. Assert the two case IDs and that the
  DRY case points at the duplication fixture.

**Proof:**

- `python3 -m unittest tests.test_smart_principle_pilot -v` passes.

### Task 11: Run the pilot and record results

**Files:**

- Create: `benchmarks/pilots/smart-principle-two-cases/result.json`

**Change:**

- For each target config, run in order:

  ```bash
  python3 benchmarks/run.py run --config <config> --smoke
  python3 benchmarks/run.py score --config <config> --latest
  python3 benchmarks/run.py judge --config <config> --latest
  python3 benchmarks/run.py pair-report --results <run dir> --output <tmp>
  ```

- Merge both targets into one `result.json` recording, per target and per case,
  the baseline and after-change score, the chosen principle, and the run
  directory. Report honestly if a run fails or a hard gate trips; do not
  re-roll to get a better number.

**Proof:**

- `result.json` contains four scored pairs and a short written finding on
  whether principle selection improved over baseline.

## Final Validation

```bash
python3 scripts/validate_skills.py
python3 -m compileall -q scripts benchmarks tests
python3 -m unittest discover -s tests -v
rg -n 'KISS Breakdown' skills/ docs/plans/2026-08-05-nerd-smart-principle-trilogy.md
```

The final `rg` must match only this plan document.

## Acceptance Criteria

- `skills/nerd-smart/references/` contains `kiss.md`, `dry.md`, and `yagni.md`,
  each with the same four headings.
- `skills/nerd-smart/SKILL.md` contains one selection table, one tie-break rule,
  and one `Principle Breakdown` block carrying a `**Principle:**` field.
- Plan and Execute rows require a principle breakdown; no other endpoint does.
- `nerd-execute` obeys the Principle Breakdown and defaults to KISS when it is
  absent; `nerd-xfast` is unchanged.
- `scripts/validate_skills.py` and the full test suite pass.
- The pilot runs 4 paired runs per target with `repetitions: 1` and produces
  `result.json` comparing baseline to the change on both models.

## Self-Review

- **Completeness:** Covers all seven requested items — context, the trilogy
  rationale, three references, the SKILL.md mapping, single-principle output,
  and a two-case, one-repetition, two-model baseline-versus-change benchmark.
- **Simplicity:** Reuses the existing breakdown block, the existing pilot
  harness, and the existing out-of-tree skill precedent. No new code module, no
  new report format, no scoring logic.
- **Risks:**
  - The Claude CLI may not accept `--effort medium`; Task 9 gates on verifying
    it and stopping rather than substituting.
  - Renaming the breakdown block is a cross-file contract change; Tasks 5 and 6
    must land in the same commit as Task 3 or the suite breaks.
  - A judge criterion for "chose the right principle" is subjective at one
    repetition; the result is directional evidence, not a significance claim.
  - `claude-sonnet-4-6` is not yet used by any config in this repository; the
    model identifier needs confirmation at run time.
