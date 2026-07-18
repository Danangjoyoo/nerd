# Nerd Fast Ctags Feature Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `symbol_index.py ensure` use Homebrew Universal Ctags directly without a feature-list wrapper.

**Architecture:** Keep `require_universal_ctags(binary, runner)` as the capability boundary. Normalize each nonempty `--list-features` row to its first whitespace-delimited field so both legacy single-column output and Homebrew's `#NAME DESCRIPTION` table expose the same feature-name set.

**Tech Stack:** Python standard library, `unittest`, Universal Ctags 6.2.x.

## Global Constraints

- Do not create or require a Ctags wrapper.
- Preserve the existing CLI, cache schema, indexing behavior, error contract, and JSON capability requirement.
- Keep the implementation standard-library only.
- Verify the direct `/opt/homebrew/bin/ctags` path against the reported KIALS repository.

---

### Task 1: Accept Tabular Universal Ctags Features

**Files:**
- Modify: `skills/nerd-fast/scripts/symbol_index.py:157-165`
- Test: `tests/test_fast_symbol_index.py`
- Modify: `docs/superpowers/specs/2026-07-16-nerd-fast-design.md`

**Interfaces:**
- Consumes: `require_universal_ctags(binary: str, runner=subprocess.run) -> None`
- Produces: The same interface, accepting `json` as either a single-column line or the first field of a tabular feature row.

- [ ] **Step 1: Write the failing Homebrew-format regression test**

```python
def test_accepts_tabular_universal_ctags_features(self):
    indexer = load_indexer()
    calls = iter(
        (
            indexer.subprocess.CompletedProcess(
                ["ctags", "--version"],
                0,
                stdout="Universal Ctags 6.2.1\n",
                stderr="",
            ),
            indexer.subprocess.CompletedProcess(
                ["ctags", "--list-features"],
                0,
                stdout=(
                    "#NAME DESCRIPTION\n"
                    "wildcards can use glob matching\n"
                    "json supports json format output\n"
                ),
                stderr="",
            ),
        )
    )
    indexer.require_universal_ctags(
        "ctags", runner=lambda *args, **kwargs: next(calls)
    )
```

- [ ] **Step 2: Run the regression test and confirm RED**

Run: `python3 -m unittest tests.test_fast_symbol_index.CtagsContractTests.test_accepts_tabular_universal_ctags_features`

Expected: `FAIL` because the current implementation compares each complete table row with the exact string `json`.

- [ ] **Step 3: Parse the first field of every nonempty feature row**

```python
available = {
    line.split(maxsplit=1)[0].casefold()
    for line in features.stdout.splitlines()
    if line.strip()
}
```

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run: `python3 -m unittest tests.test_fast_symbol_index.CtagsContractTests`

Expected: all Ctags contract tests pass, including rejection of non-Universal and non-JSON binaries.

- [ ] **Step 5: Verify direct KIALS usage without a wrapper**

Run:

```bash
index_cache_dir=$(mktemp -d /tmp/nerd-ctags-verify.XXXXXX)
python3 skills/nerd-fast/scripts/symbol_index.py ensure \
  --root /Users/mac/dev/projects/mms/kials/kials-service-courses \
  --cache "$index_cache_dir/index.sqlite3" \
  --ctags /opt/homebrew/bin/ctags
```

Expected: exit 0 with JSON status `ready`; no wrapper path is used.

- [ ] **Step 6: Run repository regression validation**

Run: `python3 -m unittest discover -s tests`

Expected: all tests pass.

Run: `python3 scripts/validate_skills.py`

Expected: all skill, routing, reference, and attribution checks pass.

- [ ] **Step 7: Commit**

```bash
git add skills/nerd-fast/scripts/symbol_index.py tests/test_fast_symbol_index.py docs/superpowers/specs/2026-07-16-nerd-fast-design.md docs/superpowers/plans/2026-07-18-nerd-fast-ctags-feature-compatibility.md
git commit -m "fix: accept tabular ctags feature output"
```
