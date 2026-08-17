# Endpoint Route Skill Split Implementation Plan

## Outcome

Refactor `nerd-smart` into a focused alignment/router skill that selects exactly
one of ten endpoints across nine route skills. Eight new skills will be created;
the existing `nerd-execute` will become the Execute route owner.

| Endpoint | Owning skill | Route resources |
| --- | --- | --- |
| Discuss | `nerd-brainstorm` | None |
| Ideate | `nerd-brainstorm` | `brainstorming.md` |
| Explore | `nerd-explore` | None |
| Diagnose | `nerd-diagnose` | Diagnosis and RCA templates |
| Review | `nerd-review` | None |
| Specify | `nerd-spec` | Behavior and system-design templates |
| Document | `nerd-document` | Overview, how-to, and reference templates |
| Plan | `nerd-plan` | Plan template and delivery-principle references |
| Execute | `nerd-execute` | Existing inline execution workflow |
| Monitor | `nerd-monitor` | None |

## Confirmed Inputs

- Every row under `## Endpoint Mapping` maps to one `nerd-*` skill; Discuss and
  Ideate share Brainstorm.
- `nerd-smart` retains Focus resolution, multi-goal intake, authority
  boundaries, and endpoint routing.
- The approved endpoint is Plan; this artifact does not authorize repository
  implementation.
- Existing `nerd-execute` must be adapted, not duplicated.
- New skills follow Skill Creator requirements: initialize through
  `init_skill.py`, keep `SKILL.md` concise, generate `agents/openai.yaml`, and
  validate each skill individually.

## Delivery Breakdown

- **Approach:** KISS + Comprehensive, because the split affects public skill
  contracts, references, release discovery, benchmarks, and tests.
- **Required outcome:** Ten mutually exclusive endpoints with one owner each;
  Brainstorm owns Discuss and Ideate.
- **Simplest sufficient design:** Keep shared alignment in Smart; move endpoint
  behavior and resources to their route owner.
- **Required surfaces:** Skills, metadata, references, validator, contract
  tests, benchmark materialization, release assertions, README, and
  attribution.
- **Proof:** Structural validation, unit tests, local skill discovery, and
  unchanged benchmark planning.
- **Deferred:** New live benchmark runs, historical benchmark rewrites, new
  plugins, and unrelated skill-family improvements.

## Constraints and Non-goals

- Preserve the mandatory Focus Record and multi-goal intake before route work.
- Keep `skills/nerd-smart/references/multi-goal-ledger.md` and
  `skills/nerd-smart/scripts/prompt_hook.py` under Smart.
- Move references rather than copying them; each reference has one route owner.
- Preserve the incompatible-skills boundary in every new skill.
- Keep frozen experiment snapshots and historical plans unchanged.
- Do not add a shared `nerd-endpoint` or another extra abstraction.
- `nerd-surgery` and `nerd-patrol` remain optional specialties, not competing
  endpoint owners.
- Fast, Silent, Loop, Memory, and XFast retain their current modifier/runtime
  roles.

## Worktree and Baseline

- Worktree was clean when this plan was produced.
- `python3 scripts/validate_skills.py` passed for all current skills.
- The focused contract, structure, README, and workflow suites passed 96 tests.
- Benchmark planning reported 513 planned runs.

## Ordered Work

### Task 1: Encode the new route topology as failing contracts

**Files:**

- Modify: `scripts/validate_skills.py`
- Modify: `tests/test_skill_structure.py`
- Modify: `tests/test_skill_contracts.py`

**Change:**

- Add an exact endpoint-to-skill registry for all ten routes.
- Expand the public inventory from 9 to 17 skills.
- Register route-specific reference ownership.
- Replace Smart tests that expect embedded workflows with tests asserting:
  - exactly ten endpoint mappings across nine route skills;
  - one owner per endpoint;
  - Smart owns only alignment and multi-goal behavior;
  - every route consumes a resolved Focus Record;
  - read-only endpoints cannot mutate;
  - Plan cannot execute and Diagnose cannot repair.

**Proof:**

- The focused tests initially fail because the eight new skill directories and
  relocated references do not yet exist.

### Task 2: Initialize and author the eight new route skills

**Files:**

- Create `SKILL.md` and `agents/openai.yaml` under:
  - `skills/nerd-brainstorm/`
  - `skills/nerd-explore/`
  - `skills/nerd-diagnose/`
  - `skills/nerd-review/`
  - `skills/nerd-spec/`
  - `skills/nerd-document/`
  - `skills/nerd-plan/`
  - `skills/nerd-monitor/`

**Change:**

- Run the Skill Creator initializer once per new skill.
- Give every description explicit intent and stop-condition triggers;
  Brainstorm's description covers both Discuss and Ideate.
- Add generated UI metadata with quoted strings, a 25-64 character short
  description, and a default prompt explicitly naming `$nerd-*`.
- Make each route:
  - require or resolve Smart's Focus Record;
  - accept exactly its endpoint set;
  - own only its endpoint behavior;
  - stop before crossing into another endpoint.

**Proof:**

- Run Skill Creator's `quick_validate.py` against every new route directory.

### Task 3: Relocate endpoint resources to their owners

**Files:**

- Move from `skills/nerd-smart/references/`:
  - `brainstorming.md` to `skills/nerd-brainstorm/references/`;
  - `diagnosis-template.md` and `rca-template.md` to
    `skills/nerd-diagnose/references/`;
  - `spec-template.md` and `system-design-template.md` to
    `skills/nerd-spec/references/`;
  - the three document templates to `skills/nerd-document/references/`;
  - `plan-template.md`, `principle-selection.md`, `comprehensive.md`, `dry.md`,
    `kiss.md`, and `yagni.md` to `skills/nerd-plan/references/`.
- Retain `multi-goal-ledger.md` under Smart.

**Change:**

- Update internal relative links and replace Smart-specific wording with the
  owning route's terminology.
- Keep Plan's KISS/Comprehensive/DRY selection progressively disclosed.
- Keep Execute's proportionate delivery rules inline so `nerd-execute` remains
  reference-free.

**Proof:**

- The validator reports no missing, unregistered, unreachable, unsafe, or
  duplicated references.

### Task 4: Slim Smart and reconcile specialties

**Files:**

- Modify: `skills/nerd-smart/SKILL.md`
- Modify: `skills/nerd-smart/agents/openai.yaml`
- Modify: `skills/nerd-execute/SKILL.md`
- Modify as required:
  - `skills/nerd-surgery/SKILL.md`
  - `skills/nerd-patrol/SKILL.md`

**Change:**

- Reduce Smart to foundation/authority, Focus, multi-goal intake, ten-route
  mapping, composition boundaries, and endpoint-change protection.
- Remove templates, brainstorming, Plan/Execute delivery mechanics, and
  endpoint execution behavior from Smart.
- Make `nerd-execute` the formal Execute endpoint owner.
- Clarify that Surgery composes with Diagnose or Execute, while Patrol composes
  with Review or Execute; neither replaces the endpoint route.
- Update Smart metadata to describe alignment and exact-one-route handoff.

**Proof:**

- Contract tests confirm Smart has only `multi-goal-ledger.md` as a reference
  and contains no endpoint-specific templates or delivery workflow.

### Task 5: Update public consumers and discovery

**Files:**

- Modify: `README.md`
- Modify: `THIRD_PARTY_NOTICES.md`
- Modify: `.github/workflows/release.yml`
- Modify: `benchmarks/nerdbench/materialize.py`
- Modify:
  - `tests/test_readme.py`
  - `tests/test_workflows.py`
  - `tests/test_benchmark_cases.py`

**Change:**

- List all 17 public skills and explain endpoint routes versus
  specialties/modifiers.
- Update attribution for references moved out of Smart.
- Change release discovery from 9 to 17 exact skill names.
- Ensure benchmark workspaces using Smart install the complete endpoint route
  suite while preserving explicit condition prompts, cases, results, and the
  513-run plan.
- Add materialization proof that endpoint route skills are available for Smart
  handoff.

**Proof:**

- README, workflow, and benchmark materialization tests pass.
- Local skill discovery returns exactly the expected 17 skills.

### Task 6: Run complete validation

```bash
rtk python3 -m compileall -q scripts benchmarks tests
rtk python3 -m unittest discover -s tests -v
rtk python3 scripts/validate_skills.py
rtk python3 benchmarks/run.py plan --config benchmarks/config.json
rtk npx skills add . --list
rtk git diff --check
```

Expected results:

- All tests and validation pass.
- Benchmark planning remains at 513 runs.
- Discovery lists exactly 17 public skills.
- No malformed frontmatter, dangling references, or whitespace errors remain.

## Acceptance Criteria

- Every original endpoint maps to exactly one `nerd-*` skill.
- Eight new route skills exist; `nerd-execute` owns Execute.
- Smart performs alignment and handoff but no endpoint work.
- Smart's reference ownership drops from fifteen files to
  `multi-goal-ledger.md` only.
- Templates and guidance load only with their owning route.
- Existing specialties and modifiers compose without redefining endpoints.
- Installation and release discovery recognize all 17 public skills.
- Full deterministic validation passes.

## Self-Review

- **Completeness:** Covers all ten endpoints, resource ownership, metadata,
  integration consumers, and verification.
- **Simplicity:** Reuses the existing Execute skill and existing references;
  adds no shared abstraction or dependency.
- **Risks:** Trigger overlap and unavailable handoff skills are addressed
  through mutually exclusive descriptions, exact routing contracts, and
  benchmark materialization tests.

This plan stops before implementation and does not authorize its execution.
