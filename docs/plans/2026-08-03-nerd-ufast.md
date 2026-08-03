# Nerd UFast v0.1 Implementation and Benchmark Plan

## Outcome

Publish `nerd-ufast` as an explicitly invoked deterministic execution skill,
verify its bounded execution contract, and run the existing two-case,
one-repetition Luna/high pilot against `nerd-xfast`.

The pilot is directional evidence only. It must not be presented as a release
benchmark or generalized performance claim.

Before considering another feedback file, produce and present one sanitized,
trace-first response to `docs/feedbacks/ufast-1.md` from the fresh pilot
evidence, then stop for user review.

## Confirmed Inputs

- Design source: `docs/specs/nerd-ufast-initial-design.md`.
- UFast is narrower than XFast: it accepts only fully resolved, low-risk work
  with known targets, an existing pattern, one mutation chain, and focused
  proof.
- UFast recommends escalation instead of automatically loading another Nerd
  skill.
- The benchmark baseline is `nerd-xfast`; the treatment is `nerd-ufast`.
- Pilot controls are fixed at two cases, one repetition, one Codex target, and
  `gpt-5.6-luna` at `high` reasoning effort.
- The benchmark-first corpus, config, and scheduling test already exist under
  `benchmarks/pilots/ufast-v1-two-cases/` and
  `tests/test_ufast_benchmark.py`.
- `docs/feedbacks/ufast-1.md` is the only active feedback. Its primary request
  is a complete execution trace of one real task, followed by trace-derived
  latency, token, tool-use, context, and architecture evidence.
- The feedback output must compare XFast and UFast on the same
  `ufast-v1-high-complexity` case so observed differences share one task and
  fixture.

## KISS Breakdown

- **Required outcome:** Add the UFast skill, make the four-run UFast pilot
  executable, and present a reproducible Feedback 1 evidence pack before any
  later feedback is considered.
- **Smallest change:** Add one two-file skill package, extend existing public
  skill and benchmark condition registries, and add one small UFast result
  reporter around the existing pilot.
- **Proof:** Skill-family validation, focused contract and benchmark tests, a
  four-run schedule, four fresh workload runs with two valid XFast/UFast
  pairs, and one sanitized trace-first Feedback 1 output.
- **Not needed:** New fixtures, cache tooling, project-map generation, changes
  to Fast or XFast behavior, more models or repetitions, a new benchmark
  framework, a 20-case benchmark expansion, speculative prompt reconstruction,
  or a README performance headline.

## Constraints and Non-goals

- Preserve authorization, safety, repository authority, and honest reporting.
- Do not classify CRUD, dependency bumps, refactors, or configuration changes
  as deterministic without applying the eligibility gate.
- Do not send security, authentication, migration, concurrency, data-loss, or
  distributed-system work to XFast automatically.
- Do not regenerate stale caches inside UFast.
- Reuse the existing XFast fixtures for both cases.
- Keep both benchmark arms isolated from user configuration and globally
  installed skills.
- Treat two cases and one repetition as insufficient for publication.
- Do not read, analyze, or incorporate another feedback file until the
  Feedback 1 output has been shown and the user explicitly continues.
- Redact secrets, credentials, authentication material, absolute temporary
  paths, and sensitive environment values from trace artifacts.
- Do not expose or reconstruct hidden system or developer prompts. Report the
  accessible invocation, skill prompt, and context layers, and mark unavailable
  runtime internals as unavailable rather than inferring them.
- Keep the confirmed two-case pilot. The feedback's proposed 20-task corpus is
  a possible later experiment, not part of this plan.

## Worktree and Baseline

The worktree currently contains these untracked in-scope files:

```text
docs/specs/nerd-ufast-initial-design.md
benchmarks/pilots/ufast-v1-two-cases/cases.json
benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json
tests/test_ufast_benchmark.py
```

The benchmark-first test currently passes two tests. Implementation must patch
these files in place and preserve unrelated user changes.

## Ordered Work

### Task 1: Finalize the UFast v0.1 Contract

**Files:**

- Modify: `docs/specs/nerd-ufast-initial-design.md`

**Change:**

- Replace unconditional task-category claims with a testable eligibility gate.
- Define explicit-only activation and the bounded sequence: reuse, one exact
  navigation batch when needed, one mutation batch, one proof wave, and at
  most one evidence-driven repair.
- Make `.nerd/project-map.json` canonical and `.nerd/cache/` advisory.
- Define cache invalidation, failure, escalation recommendation, and honest
  output rules.
- State that high-risk or unresolved work is ineligible before mutation.

**Proof:**

- Inspect the final document against every confirmed input and verify that it
  contains no automatic cross-skill routing or unsafe escalation rule.

### Task 2: Create the Self-Contained UFast Skill

**Files:**

- Create: `skills/nerd-ufast/SKILL.md`
- Create: `skills/nerd-ufast/agents/openai.yaml`

**Change:**

- Implement explicit activation, the eligibility gate, and one immutable
  action chain.
- Forbid planning artifacts, subagents, reviewers, exploratory discovery,
  intermediate validation, unrelated cleanup, and cache regeneration.
- Allow one narrow navigation batch, one structured mutation, one focused end
  proof wave, and one exact repair retry.
- Require a blocker plus recommended escalation when the task is ineligible;
  do not load or invoke XFast, Fast, Smart, or another specialty.
- Preserve the Nerd incompatible-skills boundary and compact final output.
- Expose `$nerd-ufast` in metadata and state its deterministic-task boundary.

**Proof:**

```bash
rtk python3 scripts/validate_skills.py
```

Expected: validation passes after registration is complete.

### Task 3: Register the Eighth Public Skill

**Files:**

- Modify: `scripts/validate_skills.py`
- Modify: `tests/test_skill_structure.py`
- Modify: `tests/test_workflows.py`
- Modify: `tests/test_readme.py`
- Modify: `.github/workflows/release.yml`
- Modify: `README.md`

**Change:**

- Add `nerd-ufast` to the exact public skill set with no required references or
  scripts.
- Update release assertions and installation loops from seven to eight public
  skills.
- Add a concise Skills-table entry without publishing pilot performance.
- Preserve wildcard installer behavior; add no UFast-specific installer path.

**Proof:**

```bash
rtk python3 -m unittest tests.test_skill_structure tests.test_workflows tests.test_readme -v
```

Expected: all public-skill, release, and README contracts pass with exactly
eight skills.

### Task 4: Add Deterministic UFast Contract Tests

**Files:**

- Modify: `tests/test_skill_contracts.py`

**Change:**

- Add `UFastContractTests` covering explicit-only activation, the complete
  eligibility gate, bounded navigation/mutation/proof waves, one repair retry,
  no planning artifacts, no subagents or reviewers, no cache regeneration,
  no automatic Nerd composition, high-risk rejection before mutation, compact
  output, and `$nerd-ufast` metadata.
- Enforce that the skill recommends XFast only for resolved work needing
  bounded inference, and recommends the accuracy-preserving workflow for
  uncertainty or high-risk domains.

**Proof:**

```bash
rtk python3 -m unittest tests.test_skill_contracts -v
```

Expected: all existing contracts and the new UFast contract pass.

### Task 5: Make the UFast Benchmark Conditions Executable

**Files:**

- Modify: `benchmarks/nerdbench/runner.py`
- Modify: `benchmarks/nerdbench/materialize.py`
- Modify: `benchmarks/nerdbench/adapters.py`
- Modify: `benchmarks/nerdbench/scorer.py`
- Modify: `tests/test_ufast_benchmark.py`

**Change:**

- Register `nerd-ufast` as a self-contained local condition.
- Register the `ufast` pair as treatment `nerd-ufast` versus baseline
  `nerd-xfast`.
- Isolate both arms with fresh workspaces and temporary Codex homes while
  ignoring user configuration and global rules.
- Assert exact prompts, installed skill sets, target model, high effort, one
  repetition, two cases, two arms, and four unique scheduled runs.
- Keep the case prompts outcome-only and reuse the existing greeting and
  batched-edit fixtures.

**Proof:**

```bash
rtk python3 -m unittest tests.test_ufast_benchmark -v
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json
```

Expected: the tests pass and the plan prints exactly four workload runs.

### Task 6: Add Trace Capture and a Directional UFast Reporter

**Files:**

- Modify: `benchmarks/nerdbench/models.py`
- Modify: `benchmarks/nerdbench/adapters.py`
- Modify: `benchmarks/nerdbench/runner.py`
- Create: `benchmarks/nerdbench/ufast_report.py`
- Modify: `benchmarks/run.py`
- Modify: `tests/test_ufast_benchmark.py`

**Change:**

- Preserve the complete sanitized Codex JSON event sequence for every run.
- Capture available input, cached-input, and output token counts instead of
  retaining output tokens alone.
- Record monotonic offsets for observable agent events and durations for
  benchmark-run and proof commands. Never fabricate per-LLM-call or per-tool
  timing when the Codex event stream does not expose a boundary.
- Derive observable LLM/turn counts, tool calls, repeated exact searches,
  repeated exact reads, edits, verification commands, and output verbosity
  from typed events. Mark metrics unavailable when event types are insufficient.
- Add `ufast-report` for one immutable Luna/high result directory.
- Require exactly two cases, one repetition, two arms, and two complete pairs.
- Reject wrong models, efforts, conditions, duplicate runs, missing scores,
  mismatched pair identities, invalid latency, or invalid token counts.
- Report per-case and aggregate accuracy, hard-gate failures, latency delta,
  token delta, tool counts, repeated work, and verification cost without
  claiming statistical significance.
- Write `benchmarks/pilots/ufast-v1-two-cases/result.json` without overwriting
  different evidence unless explicitly authorized.

**Proof:**

```bash
rtk python3 -m unittest tests.test_ufast_benchmark -v
```

Expected: valid fixture evidence produces two pairs and trace-derived metrics;
malformed or incomplete evidence is rejected; unsupported metrics are marked
unavailable; limitations name two cases, one repetition, one model, and
directional evidence only.

### Task 7: Run Deterministic Repository Verification

**Files:** None.

**Change:**

- Run focused checks first, then the repository-wide deterministic suite
  because public skill registration and benchmark infrastructure are shared
  release surfaces.

**Proof:**

```bash
rtk python3 -m compileall -q scripts benchmarks tests
rtk git diff --check
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest tests.test_ufast_benchmark tests.test_skill_contracts tests.test_skill_structure tests.test_workflows tests.test_readme -v
rtk python3 -m unittest discover -s tests -v
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json
```

Expected: all commands pass and the pilot plans four runs.

### Task 8: Execute and Record the Directional Pilot

**Files:**

- Create after fresh evidence exists:
  `benchmarks/pilots/ufast-v1-two-cases/result.json`

**Change:**

1. Run the Luna/high configuration once without changing source between arms.
2. Complete blinded judging before deterministic scoring.
3. Generate the UFast summary from the immutable result directory.
4. Check the generated result for reproducibility.
5. Preserve the sanitized full traces for both arms of
   `ufast-v1-high-complexity` as the Feedback 1 comparison trace.
6. If either arm has a hard-gate failure or UFast is not faster, record the
   observed result and stop; do not tune the skill or expand the pilot without
   a new decision.

**Proof:**

```bash
rtk python3 benchmarks/run.py run --config benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json --release
rtk python3 benchmarks/run.py judge --config benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json --results <result-dir>
rtk python3 benchmarks/run.py score --config benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json --results <result-dir>
rtk python3 benchmarks/run.py ufast-report --results <result-dir> --output benchmarks/pilots/ufast-v1-two-cases/result.json
```

Expected workload:

```text
2 cases × 1 repetition × 2 arms × 1 model = 4 workload runs
```

Expected evidence: two complete paired comparisons, with all limitations
preserved in `result.json`.

### Task 9: Produce and Show the Feedback 1 Evidence Pack

**Files:**

- Create after fresh evidence exists:
  `benchmarks/pilots/ufast-v1-two-cases/feedback-1-trace.json`
- Create after fresh evidence exists: `docs/feedbacks/ufast-1-output.md`

**Change:**

1. Export a chronological, sanitized trace for both XFast and UFast executions
   of `ufast-v1-high-complexity`. Include the user task, condition invocation,
   observable events, tool calls, files read, edits, proof commands, token
   usage, timestamps or offsets when available, final output, and unavailable
   fields.
2. Present a side-by-side performance table covering elapsed time, observable
   LLM or turn count, tool-call count by type, input/cached/output tokens,
   repeated reads, repeated searches, verification count and duration, and
   output verbosity.
3. Document the accessible runtime context: Codex CLI, model and effort,
   isolated workspace and Codex home, installed skill set, condition prompt,
   observed tools, fixture materialization, and known context-construction
   order.
4. Label hidden system/developer prompt content, the runtime's complete tool
   capability manifest, and unobservable injection boundaries as unavailable.
   Do not quote, infer, or reconstruct them.
5. Add a compact Fast/XFast/UFast overlap table based only on repository skill
   text, identifying duplicated latency guidance and UFast's narrower boundary.
6. State that the current two-task pilot does not satisfy the feedback's
   suggested 20-task statistical benchmark and defer that expansion.
7. End with the observed bottlenecks and at most three evidence-backed UFast
   changes to consider. Do not implement those changes in this plan run.
8. Show `docs/feedbacks/ufast-1-output.md` to the user and stop. Do not open or
   process another feedback file until the user explicitly continues.

**Proof:**

- Every metric in the Markdown output must resolve to a field in
  `feedback-1-trace.json` or be labeled unavailable.
- Both artifacts must contain no credential values, authentication paths,
  hidden prompt content, or unresolved temporary-workspace paths.
- The final response must link the Feedback 1 output and explicitly state that
  later feedback remains untouched.

## Final Validation

```bash
rtk python3 -m compileall -q scripts benchmarks tests
rtk git diff --check
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest discover -s tests -v
rtk python3 benchmarks/run.py plan --config benchmarks/pilots/ufast-v1-two-cases/gpt-5.6-luna-high.json
```

After live evidence exists, rerun the UFast reporter in check mode or compare
its deterministic output byte-for-byte with the committed `result.json`.
Validate that the Feedback 1 Markdown is derived only from the sanitized trace
artifact, present it to the user, and stop before another feedback file.

## Acceptance Criteria

- `nerd-ufast` is the eighth valid, installable public skill.
- The skill rejects ineligible or high-risk work before mutation.
- Eligible work is bounded to one navigation batch, one mutation batch, one
  proof wave, and one evidence-driven repair.
- UFast never automatically composes or routes another Nerd skill.
- The Luna/high pilot schedules and executes exactly four isolated runs.
- The result contains exactly two valid XFast/UFast pairs.
- Accuracy, failures, latency, tokens, and limitations are reported honestly.
- The Feedback 1 output shows complete observable traces for the same
  high-complexity task under XFast and UFast.
- Trace-derived metrics distinguish measured values from unavailable runtime
  internals and contain no secrets or hidden prompt content.
- `docs/feedbacks/ufast-1-output.md` is presented before any other feedback is
  opened or incorporated.
- No README performance claim is made from the directional pilot.
- Existing user work remains preserved.

## Self-Review

- **Completeness:** Covers the finalized contract, skill package, public
  registration, deterministic contracts, benchmark execution, trace
  instrumentation, and the required Feedback 1 presentation gate.
- **Simplicity:** Reuses existing fixtures and benchmark infrastructure; adds
  only one small specialized reporter because generic release reporting would
  misclassify a two-pair pilot.
- **Risks:** One repetition cannot separate implementation effects from runtime
  variance. Codex may not expose individual LLM-call timing, the full tool
  manifest, or hidden prompt placement; the output must mark those gaps rather
  than estimate them. A later, separately approved larger benchmark may be
  justified, but this plan does not include one.
