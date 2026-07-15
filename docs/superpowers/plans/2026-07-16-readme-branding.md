# README Branding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display the supplied Nerd banner and the skills.sh install-count badge in the README header.

**Architecture:** Keep all visible branding in the existing README header and protect the exact banner path, badge URLs, and ordering with the existing Python README contract suite. Track the supplied PNG unchanged and use standard Markdown so GitHub handles responsive rendering.

**Tech Stack:** Markdown, PNG, Python 3 standard-library `unittest`

## Global Constraints

- Render `assets/nerd-banner.png` immediately below `# Nerd` with descriptive alt text.
- Keep the existing CI badge unchanged and place the skills.sh badge beside it.
- Use `https://skills.sh/b/danangjoyoo/nerd` for the badge image and `https://skills.sh/danangjoyoo/nerd` for its link target.
- Do not resize, regenerate, or otherwise modify the supplied PNG.
- Do not change product copy, installation commands, benchmarks, or skill definitions.

---

### Task 1: Add the README banner and install-count badge

**Files:**
- Modify: `tests/test_readme.py`
- Modify: `README.md`
- Add: `assets/nerd-banner.png`

**Interfaces:**
- Consumes: the user-supplied `assets/nerd-banner.png` file and the existing README CI badge markup
- Produces: a README header with an exact, repository-relative banner reference and exact skills.sh badge URLs

- [x] **Step 1: Write the failing README branding contract**

Add this method to `ReadmeContractTests` in `tests/test_readme.py`:

```python
def test_header_has_nerd_banner_and_skills_badge(self):
    body = README.read_text(encoding="utf-8")
    expected_header = (
        "# Nerd\n\n"
        "![Nerd mascot banner](assets/nerd-banner.png)\n\n"
        "[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/"
        "badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml) "
        "[![skills.sh](https://skills.sh/b/danangjoyoo/nerd)]"
        "(https://skills.sh/danangjoyoo/nerd)\n"
    )
    self.assertTrue(body.startswith(expected_header))

    banner = ROOT / "assets" / "nerd-banner.png"
    self.assertTrue(banner.is_file())
    self.assertEqual(banner.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
```

- [x] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest tests.test_readme.ReadmeContractTests.test_header_has_nerd_banner_and_skills_badge -v
```

Expected: `FAIL` at `self.assertTrue(body.startswith(expected_header))` because `README.md` does not yet reference the banner or skills.sh badge.

- [x] **Step 3: Add the minimal README header markup**

Replace the current title-and-CI-badge header in `README.md` with:

```markdown
# Nerd

![Nerd mascot banner](assets/nerd-banner.png)

[![CI](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml/badge.svg)](https://github.com/Danangjoyoo/nerd/actions/workflows/ci.yml) [![skills.sh](https://skills.sh/b/danangjoyoo/nerd)](https://skills.sh/danangjoyoo/nerd)
```

Do not modify `assets/nerd-banner.png`; add the existing user-supplied file to version control as-is.

- [x] **Step 4: Run focused and README contract tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_readme.ReadmeContractTests.test_header_has_nerd_banner_and_skills_badge -v
python3 -m unittest tests.test_readme -v
```

Expected: both commands exit `0`; the focused test passes and every README contract remains green.

- [x] **Step 5: Run full verification and inspect the scoped diff**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_skills.py
git diff --check
git diff -- README.md tests/test_readme.py
git status --short
```

Expected: all tests and validation pass; `git diff --check` reports no errors; the diff contains only the approved header and contract changes; `assets/nerd-banner.png` is the only new binary asset.

- [x] **Step 6: Commit the implementation**

```bash
git add README.md tests/test_readme.py assets/nerd-banner.png docs/superpowers/plans/2026-07-16-readme-branding.md
git commit -m "docs: add Nerd banner and skills badge"
```
