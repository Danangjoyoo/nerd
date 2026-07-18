# Nerd Fast Read-Volume Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Nerd Fast choose `symbol_index.py` from the estimated total source lines a task would otherwise read.

**Architecture:** Add an early `Read-Volume Gate` to `nerd-fast`, before its general gates and discovery rules. Replace the late lookup-count heuristic with a binary line-volume contract and protect its placement, boundary, fallback, and navigation behavior with a focused contract test.

**Tech Stack:** Markdown skill/spec documentation, Python `unittest` contract tests.

## Global Constraints

- At task start, before the first source read, estimate `x`: the total estimated lines direct navigation would require.
- For `x <= 200`, skip the symbol index and read or search directly.
- For `x > 200`, run `scripts/symbol_index.py ensure` once before source reads, then navigate with `find` without implicit refresh.
- Do not wait until 200 lines have already been read before applying the gate.
- Fall back to exact-file reads or narrow text search when Universal Ctags or a usable index is unavailable, stale, or incomplete.
- Confirm index matches in source before mutation.

---

### Task 1: Enforce the Early Read-Volume Gate

**Files:**
- Modify: `tests/test_skill_contracts.py`
- Modify: `skills/nerd-fast/SKILL.md`
- Modify: `docs/superpowers/specs/2026-07-16-nerd-fast-design.md`

**Interfaces:**
- Consumes: `scripts/symbol_index.py` commands `ensure` and `find`.
- Produces: A stable Markdown contract headed `## Read-Volume Gate` before `## Gates`.

- [ ] **Step 1: Replace the lookup-count contract test with the read-volume contract**

```python
def test_uses_early_read_volume_gate_for_symbol_index(self):
    body = skill_body("nerd-fast")
    self.assertIn("## Read-Volume Gate", body)
    self.assertLess(body.index("## Read-Volume Gate"), body.index("## Gates"))
    gate = body.split("## Read-Volume Gate", 1)[1].split("## Gates", 1)[0]
    assert_terms(
        self,
        gate,
        (
            "At task start, before the first source read",
            "total estimated lines",
            "`x <= 200`",
            "skip `symbol_index.py`",
            "`x > 200`",
            "run `ensure` once before source reads",
            "`find` without implicit refresh",
            "Do not wait until 200 lines have already been read",
            "exact-file read or narrow text search",
            "confirm source before mutation",
            "scripts/symbol_index.py",
            "Universal Ctags is optional",
        ),
    )
    self.assertNotIn("three or more exact-symbol lookups", body)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python3 tests/test_skill_contracts.py FastContractTests.test_uses_early_read_volume_gate_for_symbol_index -v`

Expected: FAIL because `nerd-fast` does not contain `## Read-Volume Gate`.

- [ ] **Step 3: Add the minimal early skill contract and remove the old heuristic**

```markdown
## Read-Volume Gate

At task start, before the first source read, estimate `x`: the total estimated lines direct navigation would require. Estimate from the named scope, known ranges or file sizes, and likely supporting files; do not read targets merely to calculate an exact count.

- `x <= 200`: skip `symbol_index.py`; read or search the targets directly.
- `x > 200`: resolve `scripts/symbol_index.py` relative to this `SKILL.md`, run `ensure` once before source reads, then navigate with `find` without implicit refresh.

Do not wait until 200 lines have already been read. This gate replaces lookup-count heuristics. Universal Ctags is optional: if it or a usable index is unavailable, stale, or incomplete, fall back to an exact-file read or narrow text search. Treat index matches as navigation candidates and confirm source before mutation.
```

Delete the late `### Index Only When It Pays` section so the skill has one authoritative index-selection rule.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `python3 tests/test_skill_contracts.py FastContractTests.test_uses_early_read_volume_gate_for_symbol_index -v`

Expected: PASS.

- [ ] **Step 5: Run repository verification**

Run: `python3 scripts/validate_skills.py && python3 -m unittest discover -s tests -v && git diff --check`

Expected: All skill validations and tests pass; no whitespace errors.

- [ ] **Step 6: Commit and push the PR branch**

```bash
git add skills/nerd-fast/SKILL.md tests/test_skill_contracts.py docs/superpowers/specs/2026-07-16-nerd-fast-design.md docs/superpowers/plans/2026-07-18-nerd-fast-read-volume-gate.md
git commit -m "docs: route large reads through nerd-fast index"
git push
```
