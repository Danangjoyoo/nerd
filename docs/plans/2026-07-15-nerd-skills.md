# Nerd Skill Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `brainstorming-smart-execute`, which applies `superpowers:executing-plans` inline, to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish five self-contained Nerd skills whose Superpowers-derived methods are bundled as non-triggerable internal references.

**Architecture:** Each public skill lives in `skills/<skill-name>/` with one triggerable `SKILL.md`, Codex UI metadata, and only the references it needs. Superpowers-derived material is shortened and stored as ordinary Markdown without skill frontmatter, so it cannot be discovered independently. A repository-relative Python validator proves naming, routing, reference ownership, attribution, and cross-agent installation shape.

**Tech Stack:** Markdown, YAML, Python 3 standard library, `unittest`, `npx skills` CLI.

**Implementation status (2026-07-15):** Complete. Exactly five public skills validate and install locally for Codex, Claude Code, and Cursor; Superpowers-derived material remains internal reference knowledge.

## Global Constraints

- Public skill names are exactly `nerd-smart`, `nerd-surgery`, `nerd-patrol`, `nerd-execute`, and `nerd-silent`.
- Every public skill frontmatter contains only `name` and `description`; its folder name matches `name`.
- Internal knowledge files never use YAML frontmatter and are never named `SKILL.md`.
- No public skill requires `superpowers:*` at runtime.
- `nerd-smart` routes exactly one primary specialty; `nerd-silent` remains a modifier, never a primary specialty.
- All five skills install and load on Codex, Claude Code, and Cursor through the Agent Skills layout.
- Preserve the current Nerd behavior and approved record formats while renaming the private `brainstorming-smart` family.
- Superpowers-derived files must carry the upstream MIT notice with the installed skill.
- Do not create client-specific symlinks in the repository; the `skills` CLI owns installation links or copies.
- Do not fabricate benchmark results in this plan; benchmark publication is handled by the dependent benchmark and README plans.

---

## File Structure

### Repository validation

- Create `scripts/validate_skills.py`: repository-relative structural and behavioral contract validator.
- Create `tests/test_skill_structure.py`: frontmatter, discovery, references, metadata, and license tests.
- Create `tests/test_skill_contracts.py`: routing, record, composition, and validation-scenario tests.

### Public skills

- Create `skills/nerd-smart/SKILL.md`: base focus, routing, scope, disagreement, and endpoint workflow.
- Create `skills/nerd-smart/agents/openai.yaml`: Codex-facing UI metadata.
- Create `skills/nerd-smart/references/brainstorming.md`: shortened Superpowers brainstorming method.
- Create `skills/nerd-smart/LICENSE.superpowers`: upstream MIT license.

- Create `skills/nerd-surgery/SKILL.md`: Doctor specialty for diagnosis and optional repair.
- Create `skills/nerd-surgery/agents/openai.yaml`.
- Create `skills/nerd-surgery/references/systematic-debugging.md`.
- Create `skills/nerd-surgery/references/test-first-repair.md`.
- Create `skills/nerd-surgery/references/verification.md`.
- Create `skills/nerd-surgery/LICENSE.superpowers`.

- Create `skills/nerd-patrol/SKILL.md`: Police specialty for scoped security examination and optional remediation.
- Create `skills/nerd-patrol/agents/openai.yaml`.
- Create `skills/nerd-patrol/references/test-first-remediation.md`.
- Create `skills/nerd-patrol/references/verification.md`.
- Create `skills/nerd-patrol/LICENSE.superpowers`.

- Create `skills/nerd-execute/SKILL.md`: Builder specialty for approved plans and confirmed small implementations.
- Create `skills/nerd-execute/agents/openai.yaml`.
- Create `skills/nerd-execute/references/plan-execution.md`.
- Create `skills/nerd-execute/references/test-first-build.md`.
- Create `skills/nerd-execute/references/verification.md`.
- Create `skills/nerd-execute/LICENSE.superpowers`.

- Create `skills/nerd-silent/SKILL.md`: Economist modifier for output and optional-cost suppression.
- Create `skills/nerd-silent/agents/openai.yaml`.

### Attribution

- Create `THIRD_PARTY_NOTICES.md`: identify `obra/superpowers` v6.1.1 as the source of shortened internal knowledge and reproduce its MIT notice.

---

### Task 1: Build the repository-relative validation contract

**Files:**
- Create: `scripts/validate_skills.py`
- Create: `tests/test_skill_structure.py`
- Create: `tests/test_skill_contracts.py`

**Interfaces:**
- Produces: `validate_repository(root: pathlib.Path) -> list[str]` returning human-readable violations.
- Produces: CLI `python3 scripts/validate_skills.py [repo-root]`, exiting `0` with `PASS ...` records or `1` with violations.
- Consumes later: all skill tasks add expectations to the validator tests before creating files.

- [x] **Step 1: Write the failing structure tests**

Create tests that define the public contract before any skill exists:

```python
from pathlib import Path
import unittest

from scripts.validate_skills import PUBLIC_SKILLS, validate_repository


ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_public_skill_set_is_exact(self):
        self.assertEqual(
            PUBLIC_SKILLS,
            (
                "nerd-smart",
                "nerd-surgery",
                "nerd-patrol",
                "nerd-execute",
                "nerd-silent",
            ),
        )

    def test_repository_contract(self):
        self.assertEqual(validate_repository(ROOT), [])
```

- [x] **Step 2: Run the tests and verify RED**

Run: `python3 -m unittest tests.test_skill_structure -v`

Expected: FAIL because `scripts.validate_skills` does not exist.

- [x] **Step 3: Implement the validator skeleton**

Implement these constants and checks:

```python
PUBLIC_SKILLS = (
    "nerd-smart",
    "nerd-surgery",
    "nerd-patrol",
    "nerd-execute",
    "nerd-silent",
)

REQUIRED_REFERENCES = {
    "nerd-smart": ("brainstorming.md",),
    "nerd-surgery": (
        "systematic-debugging.md",
        "test-first-repair.md",
        "verification.md",
    ),
    "nerd-patrol": ("test-first-remediation.md", "verification.md"),
    "nerd-execute": (
        "plan-execution.md",
        "test-first-build.md",
        "verification.md",
    ),
    "nerd-silent": (),
}
```

`validate_repository` must report:

- Missing or extra directories containing `SKILL.md` beneath `skills/`.
- Missing `SKILL.md`, `agents/openai.yaml`, required reference, or required license.
- Folder/frontmatter name mismatch or frontmatter keys other than `name` and `description`.
- Reference files containing leading `---` frontmatter or nested `SKILL.md` files.
- A default prompt that does not explicitly contain `$<skill-name>`.
- A stale `brainstorming-smart`, `mensa`, or `superpowers:` runtime reference in public `SKILL.md` files.
- A missing reference link from its owning `SKILL.md`.

- [x] **Step 4: Run the tests and verify the contract now fails on missing skills**

Run: `python3 -m unittest tests.test_skill_structure -v`

Expected: FAIL with a non-empty violation list naming all five missing skill directories.

- [x] **Step 5: Add contract tests for routing and records**

Create `tests/test_skill_contracts.py` with helpers that read skill bodies and assert:

```python
ROUTES = {
    "nerd-surgery": ("broken", "unexpected", "diagnosis", "repair"),
    "nerd-patrol": ("security", "vulnerability", "exploitability"),
    "nerd-execute": ("approved plan", "confirmed", "implement"),
    "nerd-silent": ("minimal output", "final only", "findings only"),
}
```

The tests must preserve the approved Focus Record, Decision Record, Case Record, Patrol Scope, Build Contract, Build Result, Silent Conflict, and final result requirements. They must also assert that Smart names exactly one primary specialty and describes Silent as a modifier.

- [x] **Step 6: Commit the red contract**

```bash
git add scripts/validate_skills.py tests/test_skill_structure.py tests/test_skill_contracts.py
git commit -m "test: define nerd skill contracts"
```

---

### Task 2: Implement `nerd-smart` and its internal brainstorming knowledge

**Files:**
- Create: `skills/nerd-smart/SKILL.md`
- Create: `skills/nerd-smart/agents/openai.yaml`
- Create: `skills/nerd-smart/references/brainstorming.md`
- Create: `skills/nerd-smart/LICENSE.superpowers`
- Modify: `tests/test_skill_contracts.py`

**Interfaces:**
- Produces: the base Focus Record and router for exactly one of Surgery, Patrol, or Execute.
- Produces: Silent modifier activation without changing the primary specialty.
- Consumes: internal `references/brainstorming.md` only for material design or exploration decisions.

- [x] **Step 1: Add failing Smart behavior assertions**

Assert that `nerd-smart/SKILL.md`:

- Uses the exact frontmatter name `nerd-smart`.
- Routes bugs to `nerd-surgery`, security examinations to `nerd-patrol`, and confirmed implementation to `nerd-execute`.
- Activates `nerd-silent` only for explicit invocation or concrete output constraints.
- Keeps a two-round clarification ceiling and the accepted Focus Record semantics.
- Links `references/brainstorming.md` conditionally rather than invoking another skill.
- Contains no `superpowers:` runtime instruction.

- [x] **Step 2: Run the targeted test and verify RED**

Run: `python3 -m unittest tests.test_skill_contracts.SmartContractTests -v`

Expected: FAIL because `skills/nerd-smart/SKILL.md` is missing.

- [x] **Step 3: Create Smart by adapting the private base skill**

Use `/Users/danangjoyo.agus/.codex/skills/brainstorming-smart/SKILL.md` as the behavioral source and apply these exact transformations:

- Rename skill/title to `nerd-smart` / `Nerd Smart`.
- Replace every specialty reference with the approved `nerd-*` name.
- Replace Cheap terminology with Silent while keeping the Economist role and modifier semantics.
- Replace the Superpowers supersession block with a foundation block that conditionally reads `references/brainstorming.md`.
- Preserve Focus First, one-primary-specialty routing, disagreement, scope, endpoint, and record semantics.
- Replace the machine-specific validator instruction with `python3 scripts/validate_skills.py`.

Create `references/brainstorming.md` as a concise derivative of Superpowers v6.1.1 `skills/brainstorming/SKILL.md`, preserving only:

- Understand context before proposing design.
- Ask one material question at a time.
- Recommend one direction and at most two alternatives.
- Present only enough design detail for the task's complexity.
- Confirm material decisions before implementation.
- Stop at the requested endpoint.

Keep this reference at or below 120 lines and remove overlapping Smart rules, long examples, automatic design-document creation, and subagent assumptions.

- [x] **Step 4: Generate Codex metadata**

Create:

```yaml
interface:
  display_name: "Nerd Smart"
  short_description: "Focused alignment and specialty routing"
  default_prompt: "Use $nerd-smart to align this request and stop at the confirmed endpoint."
policy:
  allow_implicit_invocation: true
```

- [x] **Step 5: Add upstream license and run GREEN**

Copy the full Superpowers v6.1.1 MIT text into `LICENSE.superpowers`.

Run:

```bash
python3 -m unittest tests.test_skill_contracts.SmartContractTests -v
python3 /Users/danangjoyo.agus/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/nerd-smart
```

Expected: all Smart tests pass and `quick_validate.py` reports a valid skill.

- [x] **Step 6: Commit Smart**

```bash
git add skills/nerd-smart tests/test_skill_contracts.py
git commit -m "feat: add nerd smart skill"
```

---

### Task 3: Implement `nerd-surgery` with internal debugging, repair, and proof knowledge

**Files:**
- Create: `skills/nerd-surgery/SKILL.md`
- Create: `skills/nerd-surgery/agents/openai.yaml`
- Create: `skills/nerd-surgery/references/systematic-debugging.md`
- Create: `skills/nerd-surgery/references/test-first-repair.md`
- Create: `skills/nerd-surgery/references/verification.md`
- Create: `skills/nerd-surgery/LICENSE.superpowers`
- Modify: `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: an approved Smart Focus Record.
- Produces: Case Record, Diagnosis, Uncertainty Check, Source Request, and Verification Experiment.
- Loads: debugging knowledge for diagnosis; repair and verification knowledge only at an execute endpoint.

- [x] **Step 1: Add failing Surgery assertions**

Test the exact record blocks and require the conditional links:

```text
references/systematic-debugging.md
references/test-first-repair.md
references/verification.md
```

Assert that diagnosis can stop without mutation, repair under uncertainty is called an attempt, and success is impossible without fresh proof.

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_skill_contracts.SurgeryContractTests -v`

Expected: FAIL because Surgery is missing.

- [x] **Step 3: Adapt the private Surgery skill**

Use `/Users/danangjoyo.agus/.codex/skills/brainstorming-smart-surgery/SKILL.md` as source. Rename the base and specialty, replace runtime Superpowers invocations with conditional reads of the three internal references, and preserve the exact approved records.

Shorten the upstream methods as follows:

- `systematic-debugging.md`: evidence, reproduction, recent changes, boundary tracing, one active hypothesis, minimal experiment, architecture stop after repeated failed fixes; maximum 140 lines.
- `test-first-repair.md`: reproduce failure, observe correct RED, apply one root-cause correction, observe GREEN, retain regression test; maximum 80 lines.
- `verification.md`: identify proof, run fresh complete command, read exit/output, state only supported claims; maximum 60 lines.

- [x] **Step 4: Create metadata and license**

Use display name `Nerd Surgery`, short description `Evidence-first diagnosis and verified repair`, and a default prompt explicitly naming `$nerd-surgery`. Copy the upstream MIT license.

- [x] **Step 5: Run GREEN and validate**

```bash
python3 -m unittest tests.test_skill_contracts.SurgeryContractTests -v
python3 /Users/danangjoyo.agus/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/nerd-surgery
```

Expected: PASS.

- [x] **Step 6: Commit Surgery**

```bash
git add skills/nerd-surgery tests/test_skill_contracts.py
git commit -m "feat: add nerd surgery skill"
```

---

### Task 4: Implement `nerd-patrol` with internal remediation knowledge

**Files:**
- Create: `skills/nerd-patrol/SKILL.md`
- Create: `skills/nerd-patrol/agents/openai.yaml`
- Create: `skills/nerd-patrol/references/test-first-remediation.md`
- Create: `skills/nerd-patrol/references/verification.md`
- Create: `skills/nerd-patrol/LICENSE.superpowers`
- Modify: `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: an approved Smart Focus Record and exact audit target.
- Produces: Patrol Scope, Security Finding, Validation Needed, and Patrol Result.
- Loads: remediation and verification references only when the endpoint authorizes code changes.

- [x] **Step 1: Add failing Patrol assertions**

Require exact evidence classifications, scope boundaries, safe proof ladder, `No confirmed findings within this scope`, and the rule that an advisory without reachable installed usage is not a finding.

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_skill_contracts.PatrolContractTests -v`

Expected: FAIL because Patrol is missing.

- [x] **Step 3: Adapt the private Patrol skill**

Use `/Users/danangjoyo.agus/.codex/skills/brainstorming-smart-patrol/SKILL.md` as source. Rename it to `nerd-patrol`, require `nerd-smart` as base, preserve all approved records, and replace Superpowers remediation invocations with conditional internal reference reads.

Keep each reference role-specific and concise:

- `test-first-remediation.md`: safe failing reproduction, minimal correction, red-green proof.
- `verification.md`: confirm original exploit path is closed and relevant regression checks pass before claiming remediation.

- [x] **Step 4: Create metadata and license**

Use display name `Nerd Patrol`, short description `Scope-bound security findings with evidence`, and a default prompt explicitly naming `$nerd-patrol`. Copy the upstream MIT license.

- [x] **Step 5: Run GREEN and validate**

```bash
python3 -m unittest tests.test_skill_contracts.PatrolContractTests -v
python3 /Users/danangjoyo.agus/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/nerd-patrol
```

Expected: PASS.

- [x] **Step 6: Commit Patrol**

```bash
git add skills/nerd-patrol tests/test_skill_contracts.py
git commit -m "feat: add nerd patrol skill"
```

---

### Task 5: Implement `nerd-execute` with internal plan, test-first, and proof knowledge

**Files:**
- Create: `skills/nerd-execute/SKILL.md`
- Create: `skills/nerd-execute/agents/openai.yaml`
- Create: `skills/nerd-execute/references/plan-execution.md`
- Create: `skills/nerd-execute/references/test-first-build.md`
- Create: `skills/nerd-execute/references/verification.md`
- Create: `skills/nerd-execute/LICENSE.superpowers`
- Modify: `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: approved Focus Record plus either a written plan or concrete acceptance criteria.
- Produces: Build Contract, Baseline, optional Repository Gravity, checkpoints, conflicts, and Build Result.
- Loads: plan execution only for written plans; test-first knowledge for behavior changes; verification before Build Result.

- [x] **Step 1: Add failing Execute assertions**

Require all approved Build records, proof-first checkpoint ordering, two correction attempts, repository topology handling, no subagent dispatch, and Silent presentation precedence.

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_skill_contracts.ExecuteContractTests -v`

Expected: FAIL because Execute is missing.

- [x] **Step 3: Adapt the private Execute skill**

Use `/Users/danangjoyo.agus/.codex/skills/brainstorming-smart-execute/SKILL.md` as source. Rename all family references, preserve the repository-session context and exact record blocks, and replace upstream runtime skill calls with conditional reference reads.

Create concise internal knowledge:

- `plan-execution.md`: load and challenge the plan, map outcome checkpoints, execute in dependency order, stop on blockers, verify each checkpoint; maximum 70 lines.
- `test-first-build.md`: RED, verify correct failure, minimal GREEN, verify full relevant suite, refactor while green; maximum 90 lines.
- `verification.md`: map every acceptance criterion to fresh evidence and report gaps explicitly; maximum 60 lines.

- [x] **Step 4: Create metadata and license**

Use display name `Nerd Execute`, short description `Repository-aligned implementation with proof`, and a default prompt explicitly naming `$nerd-execute`. Copy the upstream MIT license.

- [x] **Step 5: Run GREEN and validate**

```bash
python3 -m unittest tests.test_skill_contracts.ExecuteContractTests -v
python3 /Users/danangjoyo.agus/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/nerd-execute
```

Expected: PASS.

- [x] **Step 6: Commit Execute**

```bash
git add skills/nerd-execute tests/test_skill_contracts.py
git commit -m "feat: add nerd execute skill"
```

---

### Task 6: Implement `nerd-silent` as the global presentation modifier

**Files:**
- Create: `skills/nerd-silent/SKILL.md`
- Create: `skills/nerd-silent/agents/openai.yaml`
- Modify: `tests/test_skill_contracts.py`

**Interfaces:**
- Consumes: any active Nerd workflow and confirmed scope.
- Produces: suppressed process narration and reduced optional work without reducing the final deliverable.
- Must not: override correctness, verification, authorization, safety, or required user interaction.

- [x] **Step 1: Add failing Silent assertions**

Require explicit/concrete activation, the Economist role, hard narration suppression, permitted interaction records, and the normal complete final result.

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_skill_contracts.SilentContractTests -v`

Expected: FAIL because Silent is missing.

- [x] **Step 3: Adapt the private Cheap skill**

Use `/Users/danangjoyo.agus/.codex/skills/brainstorming-smart-cheap/SKILL.md` as source. Rename `Cheap` to `Silent`, remove the 100-example narration blacklist in favor of concise category rules, preserve the event record semantics, and keep the complete final result requirement. Target 100–140 lines.

- [x] **Step 4: Create metadata**

```yaml
interface:
  display_name: "Nerd Silent"
  short_description: "Minimal narration without correctness loss"
  default_prompt: "Use $nerd-silent with this task to suppress optional process output."
```

- [x] **Step 5: Run GREEN and validate**

```bash
python3 -m unittest tests.test_skill_contracts.SilentContractTests -v
python3 /Users/danangjoyo.agus/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/nerd-silent
```

Expected: PASS.

- [x] **Step 6: Commit Silent**

```bash
git add skills/nerd-silent tests/test_skill_contracts.py
git commit -m "feat: add nerd silent modifier"
```

---

### Task 7: Add attribution and verify the complete installable family

**Files:**
- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `scripts/validate_skills.py`
- Modify: `tests/test_skill_structure.py`

**Interfaces:**
- Produces: one repository-level attribution record and a passing family validator.
- Proves: local discovery and copied installation for Codex, Claude Code, and Cursor.

- [x] **Step 1: Add failing attribution and discovery tests**

Assert that `THIRD_PARTY_NOTICES.md` names `obra/superpowers`, version `6.1.1`, Jesse Vincent, and MIT. Assert that every derived skill carries an identical `LICENSE.superpowers`.

- [x] **Step 2: Run RED**

Run: `python3 -m unittest tests.test_skill_structure -v`

Expected: FAIL because the repository notice is missing.

- [x] **Step 3: Add the notice and complete validator output**

Document that the internal references are shortened derivatives, list the affected Nerd skills, reproduce the upstream MIT text, and link the source repository. Make `validate_skills.py` print one `PASS <skill>` line per public skill plus `PASS routing`, `PASS references`, and `PASS attribution`.

- [x] **Step 4: Run all deterministic verification**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
npx skills add . --list
```

Expected:

- All unit tests pass.
- Validator prints all PASS records and exits `0`.
- The CLI lists exactly the five approved Nerd skills and no reference files.

- [x] **Step 5: Smoke-install for each supported agent in a temporary directory**

Run the installer with `--copy` and verify each target receives all five skill directories:

```bash
TMPDIR="$(mktemp -d)"
cd "$TMPDIR"
npx skills add /Users/danangjoyo.agus/work/playground/mensa --copy --all -y
npx skills list
```

Expected: Codex, Claude Code, and Cursor discover the five Nerd skills; no internal reference is listed as a skill.

- [x] **Step 6: Update the renamed Git remote**

```bash
git remote set-url origin https://github.com/Danangjoyoo/nerd.git
git remote -v
```

Expected: fetch and push URLs both end in `Danangjoyoo/nerd.git`.

- [x] **Step 7: Commit the complete family**

```bash
git add THIRD_PARTY_NOTICES.md scripts tests skills
git commit -m "chore: validate nerd skill family"
```

## Plan Exit Proof

Run fresh from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
npx skills add . --list
git status --short
```

The skill plan is complete only when all deterministic checks pass, the CLI lists exactly five skills, and `git status --short` contains no uncommitted implementation files.
