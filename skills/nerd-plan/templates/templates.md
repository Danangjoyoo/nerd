# Nerd Plan Templates

## Reusable Plan Template

Fill this template using confirmed repository evidence. Replace placeholders,
omit uninformative optional fields, and repeat tasks and per-goal task tables as
needed. Keep one goal ledger table. Use the skill's planning rules and the
size-based artifact layout; the full example below illustrates the single-file layout.

````markdown
# [Feature] Implementation Plan

**Goal:** [Observable outcome]
**Approach:** [Simplest sufficient design]
**Scope:** [Included boundary and explicit non-goals]
**Proof:** [Completion verification]
**Spec:** [Optional source spec path]
**Sub-Agent Driven:** [YES/NO; default NO; continue asking unless explicitly requested]

## File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `exact/path` | Create / Modify / Test | [Why it changes] |

## Goal Ledger

| Goal ID | Source requirement / outcome | Task ledger | Depends on | Status | Completion proof |
| --- | --- | --- | --- | --- | --- |
| G1 | [Accepted outcome] | [G1 tasks](#g1-goal-outcome) | none | queued | [Command and expected result] |

## Task Ledgers

### G1: [Goal outcome]

| Task ID | Deliverable and link | Depends on | Status | Completion proof |
| --- | --- | --- | --- | --- |
| T1 | [Deliverable](#task-1-deliverable) | none | queued | [Command and expected result] |

[Repeat exactly one task ledger table per goal. Embed below 300 lines;
otherwise link the goal ledger and each task ledger section in ledger.md.]

## Tasks

### Task 1: [Deliverable]

**Outcome:** [Independently reviewable deliverable]
**Goal:** [Owning goal ID]
**Files:** `exact/path`, `tests/exact/path`
**Depends on:** [Optional task IDs]

**Focus Record**

- **Intention:** [Real goal]
- **Expectation:** [Endpoint from Smart's mapping]
- **Scope:** [Core task plus at most three approved adjacents]
- **Role:** [Single best role]
- **Skills:** [Bullet list of skills to use]
- **Review Required:** [YES/NO; use nerd-review for independently reviewable tasks]
- **Sub-agent Model:** [Only if enabled; inherit unless the user explicitly requests manual or automatic selection via references/subagent-model-mapping.md]

**Code skeleton and contract:** [Required for code changes; otherwise state why inapplicable]
```text
class ActualClass:                              # omit for standalone functions
    function actualName(input: ConcreteInput) -> ConcreteOutput:
        validate input; return/raise specified errors
        apply named transformations
        return defined output, including empty results
```
[Define concrete types and required boundary contracts; use task-specific names.]

1. Add the failing test or baseline check.
2. Run `[command]`; expect `[specific failure or baseline]`.
3. Make `[specific code or artifact change]`.
4. Run `[focused command]`; expect `[specific success]`.
5. Run `[regression command]`; expect `[specific success]`.

**Proof:** `[command or inspection]` → `[expected result]`

## Final Verification

- `[command]` → `[expected result]`
````

## Full Example

This fictional Python repository has an existing `tests/` directory, no tag
normalizer or tag reference page, and uses standard-library `unittest`. Paths,
commands, expected failures, and results below are illustrative inputs, not
verified facts about the current workspace. Save only the adapted plan; do not
execute these instructions while planning. The example has two goals and one
task ledger table per goal; all implementation statuses remain queued.

````markdown
# Tag Normalization Implementation Plan

**Goal:** Normalize tag labels consistently and document the accepted inputs.
**Approach:** Add one pure Python function and a short reference page.
**Scope:** Trim and lowercase string labels; reject empty labels and non-strings.
No Unicode normalization, persistence, or API changes.
**Proof:** Standard-library unit tests and a documentation contract check.
**Sub-Agent Driven:** NO
**Complete plan lines:** 108; under 300, single Markdown file with embedded ledgers.

## File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `src/tag.py` | Create | Pure normalization function |
| `tests/test_tag.py` | Create | Success and invalid-input regression tests |
| `docs/tags.md` | Create | Input/output and error reference |

## Goal Ledger

| Goal ID | Source requirement / outcome | Task ledger | Depends on | Status | Completion proof |
| --- | --- | --- | --- | --- | --- |
| G1 | Deterministic tag normalization | [G1 tasks](#g1-normalize-tags) | none | queued | `python3 -m unittest discover -s tests -v`; all normalization tests pass |
| G2 | Document the normalization contract | [G2 tasks](#g2-document-tags) | G1 | queued | T2 contract check passes; examples agree with G1 |

## Task Ledgers

### G1: Normalize tags

| Task ID | Deliverable and link | Depends on | Status | Completion proof |
| --- | --- | --- | --- | --- |
| T1 | [Normalization function and tests](#task-1-normalize-tag-labels) | none | queued | `python3 -m unittest discover -s tests -v`; all cases pass |

### G2: Document tags

| Task ID | Deliverable and link | Depends on | Status | Completion proof |
| --- | --- | --- | --- | --- |
| T2 | [Tag contract reference](#task-2-document-the-tag-contract) | T1 | queued | T2 documentation check exits 0; manual comparison finds no contract mismatch |

## Tasks

### Task 1: Normalize tag labels

**Outcome:** A tested pure function with predictable output and typed failures.
**Goal:** G1
**Files:** `src/tag.py`, `tests/test_tag.py`

**Focus Record**

- **Intention:** Normalize valid tag strings and reject invalid inputs.
- **Expectation:** Execute
- **Scope:** Function and standard-library unit tests; no transport or storage work.
- **Role:** Python developer
- **Skills:**
  - nerd-execute
- **Review Required:** YES; nerd-review

**Code skeleton and contract:** `normalize_tag` accepts strings, returns a nonempty
trimmed lowercase string, and has no side effects. Non-strings raise `TypeError`;
empty or whitespace-only strings raise `ValueError`.

```python
def normalize_tag(value: str) -> str:
    # Reject non-string runtime inputs with TypeError.
    # Strip surrounding whitespace, then lowercase the string.
    # Raise ValueError if the normalized string is empty.
    # Return the normalized string.
    ...
```

1. Add `unittest` cases importing `normalize_tag` from `src.tag`: `"  News  "`
   becomes `"news"`, `"news"` stays `"news"`, internal whitespace in `"New Tag"`
   remains `"new tag"`, `""` and `"   "` raise `ValueError`, and `None` and `7`
   raise `TypeError`. Use `assertEqual` and `assertRaises` for the exact contract.
2. Run `python3 -m unittest discover -s tests -p test_tag.py -v`; expect an import
   failure because `src/tag.py` does not exist.
3. Create `src/tag.py` with the smallest function satisfying the contract above.
4. Rerun the focused command; expect all defined cases to pass.
5. Run `python3 -m unittest discover -s tests -v`; expect the full suite to pass.

**Proof:** Focused and full-suite commands exit 0 after the observed import failure.

### Task 2: Document the tag contract

**Outcome:** A reference page matching the tested function, including failures.
**Goal:** G2
**Files:** `docs/tags.md`
**Depends on:** T1

**Focus Record**

- **Intention:** Explain supported tag inputs, outputs, and errors.
- **Expectation:** Document
- **Scope:** Tag reference page using T1's confirmed contract.
- **Role:** Technical writer
- **Skills:**
  - nerd-document
- **Review Required:** YES; nerd-review

**Code skeleton and contract:** No code skeleton applies. The Markdown artifact
must contain `## Inputs`, `## Outputs`, `## Examples`, and `## Errors`; describe
string-only input, trimming/lowercasing, preserved internal whitespace, and exact
`TypeError`/`ValueError` conditions. Examples must match T1's test cases.

1. Run `test ! -e docs/tags.md`; expect exit 0 for the confirmed missing page.
2. Write the four sections with valid examples and both error conditions.
3. Run the following check; expect exit 0:

```sh
python3 - <<'CHECK'
from pathlib import Path
text = Path('docs/tags.md').read_text()
for heading in ('Inputs', 'Outputs', 'Examples', 'Errors'):
    assert f'## {heading}' in text, heading
assert 'TypeError' in text and 'ValueError' in text
CHECK
```

4. Compare every documented rule and example with T1's tests and function;
   expect agreement. The structural check alone does not establish correctness.

**Proof:** The structural check exits 0 and manual comparison confirms agreement.

## Final Verification

- `python3 -m unittest discover -s tests -v` exits 0.
- T2's structural and manual checks pass; all requested behavior is documented.
- Record actual evidence in each ledger before marking tasks or goals done;
  this saved plan leaves all statuses queued and stops before implementation.
````
