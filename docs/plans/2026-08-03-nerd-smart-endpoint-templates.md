# Nerd Smart Endpoint Templates Implementation Plan

## Goal

Add a small, original Markdown template library under
`skills/nerd-smart/references/` for the Specify, Plan, Document, and Diagnose
endpoints. Nerd Smart must select templates lazily, adapt them to the confirmed
Focus Record, and stop at the active endpoint.

This document is the review boundary. Do not implement the templates until the
user approves this plan.

## Confirmed Design

- Keep every template as a flat reference directly under
  `skills/nerd-smart/references/`; do not add nested directories or another
  template registry.
- Add eight templates: behavior specification, system design, implementation
  plan, three generic document forms, diagnosis, and RCA.
- Split generic documentation by reader intent:
  - overview for understanding what something is and why it matters;
  - how-to for completing a concrete task;
  - reference for precise lookup of contracts, options, or facts.
- Select one template by default. Read a second template only for an explicitly
  combined artifact, such as a specification that also requires a system
  design.
- Treat every template as adaptable scaffolding, not a mandatory output shape.
  Preserve an explicit user format, omit irrelevant sections, remove template
  instructions from the delivered artifact, and label material unknowns rather
  than inventing facts.
- A template never changes the endpoint. A plan does not authorize execution,
  and a diagnosis or RCA does not authorize repair.
- Author all template text from first principles. Do not import third-party
  skill content, add a runtime dependency, or add source-specific license
  files.

## KISS Breakdown

- **Required outcome:** Nerd Smart can produce consistently complete artifacts
  for the four requested endpoint families using narrowly selected templates.
- **Smallest change:** Add eight reference files, one concise routing section in
  `SKILL.md`, and focused additions to the existing validator and contract
  tests.
- **Proof:** Smart-specific contract tests verify selection and content
  boundaries; repository validation verifies every reference exists and is
  directly linked.
- **Not needed:** A template engine, generator script, schema, index file,
  nested reference hierarchy, new dependency, installer change, README change,
  metadata change, or templates for the other six endpoints.

## Worktree Constraint and Baseline

The worktree already contains unrelated documentation moves, installer and
prompt-hook work, and pending XFast changes. Implementation must patch the
current files in place and must not reset, revert, overwrite, or complete those
adjacent changes.

At planning time:

- `scripts/validate_skills.py` passes;
- `SmartContractTests` passes all eight existing tests;
- the complete structure test has two pre-existing XFast registration
  mismatches between `tests/test_skill_structure.py` and
  `scripts/validate_skills.py`.

Re-run and record the baseline immediately before implementation. Focused Smart
checks must pass cleanly. A final repository-wide run must distinguish any
unchanged baseline failure from a regression introduced by this work; do not
repair unrelated XFast state as part of this plan.

## Planned Files

Create:

```text
skills/nerd-smart/references/spec-template.md
skills/nerd-smart/references/system-design-template.md
skills/nerd-smart/references/plan-template.md
skills/nerd-smart/references/document-overview-template.md
skills/nerd-smart/references/document-how-to-template.md
skills/nerd-smart/references/document-reference-template.md
skills/nerd-smart/references/diagnosis-template.md
skills/nerd-smart/references/rca-template.md
```

Modify:

```text
skills/nerd-smart/SKILL.md
scripts/validate_skills.py
tests/test_skill_contracts.py
tests/test_skill_structure.py
```

Leave `skills/nerd-smart/references/brainstorming.md`, installer and hook files,
`agents/openai.yaml`, README files, and all other skills unchanged.

## Template Content Contract

Each new reference must have no YAML frontmatter and must contain four compact
parts:

1. **Use When** — the selection boundary and closest template it should not be
   confused with.
2. **Adaptation Rules** — preserve known facts and requested format, mark
   unknowns, omit irrelevant sections, and remove placeholder instructions.
3. **Template** — an editable Markdown skeleton with short bracketed prompts.
4. **Completion Check** — artifact-specific quality checks plus the active
   endpoint's stopping rule.

Use the following file-specific contracts:

| Reference | Select when | Core skeleton |
| --- | --- | --- |
| `spec-template.md` | Defining externally observable requirements or behavior | Summary; problem; goals and non-goals; users or stakeholders; functional and quality requirements; behavior and edge cases; interfaces or data; constraints and dependencies; acceptance criteria; open questions |
| `system-design-template.md` | Defining internal architecture or technical boundaries | Context and drivers; goals and non-goals; constraints; architecture overview; components and responsibilities; data and control flow; interfaces and persistence; failure and recovery; security and privacy; observability; rollout or migration; alternatives and trade-offs; proof; open questions |
| `plan-template.md` | Turning a confirmed outcome into ordered implementation work | Outcome; confirmed inputs; KISS Breakdown; constraints and non-goals; worktree or baseline state; ordered tasks with files, change, and proof; final validation; acceptance criteria; brief self-review |
| `document-overview-template.md` | Explaining what a subject is, why it matters, and how its parts relate | Audience and purpose; summary; key concepts; detailed explanation; examples; limitations; related material |
| `document-how-to-template.md` | Guiding a reader through one concrete outcome | Outcome; audience and prerequisites; ordered steps; verification; troubleshooting; conditional rollback or recovery; related material |
| `document-reference-template.md` | Providing precise lookup information | Scope; terminology; exact entries, contracts, or options; defaults and invariants; examples; errors or limitations; related material |
| `diagnosis-template.md` | Investigating a current broken, unexpected, or inconsistent behavior | Problem; expected and actual behavior; scope and environment; evidence; hypotheses and experiments; ruled-out causes; cause classified as Confirmed, Probable, or Unknown; impact; remaining gaps; recommended next authorized action |
| `rca-template.md` | Producing a retrospective incident or root-cause analysis | Summary; impact; timeline; detection and response; evidence; root cause; contributing factors; corrective and preventive actions; lessons; follow-up validation; remaining unknowns |

For RCA actions, include owner, due date, or status only when supplied or
confirmed. Never fabricate accountability data. Keep recommendations inside the
artifact; do not perform them at the Diagnose endpoint.

## Task 1: Lock the Smart Template Contracts

Modify `tests/test_skill_contracts.py` before creating the references.

- Add one small helper for reading a named Nerd Smart reference.
- Add a single canonical tuple of the eight new filenames inside the Smart test
  scope.
- Add a test that requires Nerd Smart to:
  - link every template directly;
  - select after focus is resolved;
  - read only the selected reference or references;
  - use one template by default;
  - preserve an explicit user format;
  - permit omission of irrelevant sections;
  - mark unknowns instead of inventing facts;
  - keep template choice from changing the endpoint.
- Add table-driven content checks for the common four-part structure and the
  file-specific concepts in the Template Content Contract.
- Add explicit distinction checks for spec versus system design, the three
  document intents, and live diagnosis versus retrospective RCA.
- Assert that none of the new references has frontmatter, runtime skill calls,
  or third-party source/license language.

Run the focused test and confirm RED is caused only by missing template files
or routing:

```bash
rtk python3 -m unittest tests.test_skill_contracts.SmartContractTests -v
```

## Task 2: Create the Eight Original References

Create the eight files in the Planned Files section using the shared structure
and the file-specific skeletons above.

- Keep instructions imperative and concise.
- Use neutral Markdown placeholders such as `[Required: ...]` and
  `[Optional: omit when irrelevant]`.
- Make required versus conditional sections apparent without forcing empty
  headings into final artifacts.
- Keep evidence, acceptance, and uncertainty language concrete.
- Do not embed another workflow, invoke another skill, or authorize a later
  endpoint.

After creation, run the Smart contract tests. Content tests should pass; direct
link and routing tests may remain RED until Task 3.

## Task 3: Add Lazy Endpoint Routing to Nerd Smart

Modify `skills/nerd-smart/SKILL.md` with one concise `## Use Endpoint
Templates` section immediately before `## Decide and Work`.

The section must:

- map Specify behavior to `spec-template.md` and Specify architecture to
  `system-design-template.md`;
- map Plan to `plan-template.md`;
- map Document by reader intent to overview, how-to, or reference;
- map a current investigation to `diagnosis-template.md` and an explicit
  incident retrospective or RCA to `rca-template.md`;
- say templates are optional for tiny outputs and explicit user structures take
  precedence;
- say to read only the matched reference files, with one selected by default;
- allow combined spec and system-design loading only when the requested artifact
  genuinely includes both;
- require removing template prompts and explicitly preserving unknowns;
- restate that template selection does not authorize planning, execution, or
  repair.

Do not change the ten endpoint rows, specialty-routing rules, automatic hook,
or existing brainstorming behavior.

Run:

```bash
rtk python3 -m unittest tests.test_skill_contracts.SmartContractTests -v
```

Expected: all Smart contract tests pass.

## Task 4: Register Exact Reference Ownership

Modify `scripts/validate_skills.py` and `tests/test_skill_structure.py`.

- Expand only `REQUIRED_REFERENCES["nerd-smart"]` to contain
  `brainstorming.md` plus the eight templates in the logical order shown in
  Planned Files.
- Update the existing exact ownership expectation without removing or
  reconciling unrelated pending skill entries.
- Add a separate
  `test_smart_reference_files_match_registry` method asserting that the actual
  `*.md` filenames under Smart's `references/` directory exactly equal the
  declared set. Keeping this check separate makes its result visible even when
  an unrelated ownership assertion has a pre-existing failure.
- Reuse the existing validator behavior for file existence, forbidden
  frontmatter, direct `SKILL.md` links, and nested-skill rejection. Do not add a
  new validator abstraction.

Run:

```bash
rtk python3 -m unittest \
  tests.test_skill_contracts.SmartContractTests \
  tests.test_skill_structure.SkillStructureTests.test_smart_reference_files_match_registry \
  -v
rtk python3 scripts/validate_skills.py
```

Expected: the Smart checks, Smart filename registry check, and repository
validator pass. Leave any unchanged XFast baseline mismatch to the final full
suite report; do not broaden the patch.

## Task 5: Validate the Skill and Review the Diff

Run fresh proof from the repository root:

```bash
rtk python3 /Users/mac/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/nerd-smart
rtk python3 -m unittest tests.test_skill_contracts.SmartContractTests -v
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest discover -s tests -v
rtk git diff --check
rtk git status --short
```

Review the diff and confirm:

- only the twelve planned implementation files changed for this feature;
- every new reference is linked exactly once from the routing section;
- the references contain original guidance and no runtime dependency;
- no existing endpoint, routing, hook, installer, or unrelated XFast behavior
  changed;
- any repository-wide failure matches the captured pre-implementation baseline
  and is not hidden or claimed as passing.

## Acceptance Criteria

- All eight requested templates exist under `skills/nerd-smart/references/`.
- Nerd Smart chooses the correct template from the confirmed endpoint and
  artifact intent without preloading the whole library.
- The spec/system-design, overview/how-to/reference, and diagnosis/RCA
  distinctions are explicit and covered by deterministic tests.
- Templates adapt to user format, omit irrelevant sections, and expose unknowns
  instead of fabricating details.
- Plan and Diagnose outputs stop before execution or repair.
- Smart-specific tests, skill validation, and the repository validator pass.
- The full test suite has no new failure relative to the recorded baseline.

## Self-Review Record

- **Completeness:** Covers every template family requested by the user and the
  routing, structure, and content contracts needed to make them usable.
- **Simplicity:** Uses eight direct references and three document intents; no
  shared base template, index, engine, dependency, or unrelated endpoint work.
- **Primary risks handled:** Lazy selection limits context growth, adaptation
  rules limit over-templating, explicit unknowns limit fabrication, and endpoint
  stop rules prevent implementation drift.
- **Review decision:** Stop after publishing this plan and wait for approval
  before creating or modifying the planned implementation files.
