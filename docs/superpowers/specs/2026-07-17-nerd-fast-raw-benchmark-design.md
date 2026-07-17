# Nerd Fast Raw-Agent Smoke Benchmark Design

**Date:** 2026-07-17

## Goal

Measure the directional effect of `nerd-fast` on GPT-5.6 Sol at `xhigh` reasoning by comparing a raw agent with the same agent given only `nerd-fast`. Publish accuracy, end-to-end latency, and provider-reported output-token evidence in `README.md`.

This is intentionally a fast smoke benchmark: one case, one repetition, and two target-agent runs. It is not statistically representative and must not display confidence intervals or make population-level claims.

## Comparison Boundary

| Arm | Installed Nerd skills | Prompt prefix |
| --- | --- | --- |
| **Raw agent** | None | None |
| **Nerd Fast** | `nerd-fast` only | `Use $nerd-fast.` |

Neither arm receives `nerd-smart`, `nerd-execute`, `nerd-silent`, or another Nerd skill. The existing Fast-versus-Execute release comparison remains unchanged.

The benchmark setup must isolate condition-visible skills so globally installed Nerd skills cannot enter either arm. Both `CODEX_HOME` and `HOME` use a temporary directory because Codex can discover personal skills under either location. Authentication may be reused through a temporary symlink, but credentials must not be copied into an agent workspace or published with benchmark artifacts.

## Case and Run Matrix

Use a current-worktree snapshot and a repository-wide maintainer-summary task:

> Inspect this repository and write an accurate, concise technical summary for a new maintainer. Cover its purpose, all public Nerd skills and their composition, benchmark architecture, installation and validation, and major directories. Ground claims in repository paths and do not change files.

The fixture is `__repository__`, which copies tracked and non-ignored untracked repository contents into an isolated workspace. Run both arms once with:

- Agent: Codex CLI
- Model: `gpt-5.6-sol`
- Reasoning effort: `xhigh`
- Parallelism: `1`
- Identical fixture, prompt body, permission mode, and timeout
- Seeded arm ordering to reduce fixed order bias

The resulting matrix contains exactly two target-agent runs. A failed or missing run stays visible and is never silently retried into the published pair.

## Metrics

### Accuracy

Use deterministic coverage and cleanliness checks only so the smoke benchmark needs no additional model-judge calls:

- All six public Nerd skills are named (35 points).
- `skills/`, `benchmarks/`, `tests/`, and `scripts/` are covered (25 points).
- Codex, Claude, and Cursor support is covered (15 points).
- Installation and validation or test paths are covered (15 points).
- The workspace remains unchanged (10 points).

Score the two checks as a 100-point rubric and require both as hard gates. Report each arm's score and pass/fail result. Do not use latency, tokens, narration style, or skill identity when determining accuracy.

### Latency

Measure wall-clock seconds around the Codex CLI invocation, excluding fixture materialization and post-run proof execution. Report each raw value and the paired percentage delta:

`(fast - raw) / raw * 100`

Because each arm has one sample, do not label the values as stable medians or calculate p95.

### Tokens

Use only provider-reported output-token usage captured by the Codex event adapter. Report each raw count and the paired percentage delta using the same formula as latency. If either count is unavailable, report token comparison as unavailable rather than estimating from words or bytes.

## Harness Changes

Add explicit benchmark conditions for a skill-free raw agent and an agent with only `nerd-fast`. Raw condition prompting must return the case prompt unchanged; treatment prompting adds only the explicit Fast invocation. Reporting must reject raw evidence whose executed commands access a Nerd skill and Fast evidence that does not execute `symbol_index.py ensure` during complex discovery.

Create a dedicated pilot directory containing:

- The single deterministic case
- A GPT-5.6 Sol xhigh configuration with one repetition
- A checked-in summary artifact derived from the immutable raw run evidence

Keep live raw evidence under the existing ignored results directory. The summary records the run identifier, model, reasoning effort, Codex version, case, arm values, deltas, and proof status without credentials or unrelated event payloads.

## README Publication

Add a clearly labeled **Nerd Fast smoke benchmark** subsection. Show a compact table for raw versus Fast accuracy, latency, and output tokens, followed by percentage deltas and these limitations:

- One case and one repetition
- Directional evidence only
- Raw agent versus `nerd-fast` only
- Deterministic correctness proof

Link the pilot configuration and checked-in summary artifact so the numbers are reproducible and auditable. Do not replace or merge the existing release benchmark tables with this smoke result.

## Verification

Contract tests must prove:

- The pilot schedules exactly two runs.
- The raw condition installs and invokes no Nerd skills.
- The treatment condition installs and invokes only `nerd-fast`.
- The raw command stream contains no personal or workspace Nerd-skill access.
- The treatment command stream contains an executed bundled-indexer refresh attempt.
- The model is GPT-5.6 Sol with `xhigh` effort.
- The case has only deterministic hard-gate criteria.
- The summary computes latency and token deltas from one valid pair.
- Missing token usage remains explicitly unavailable.
- README values match the checked-in summary.

Run the focused benchmark tests, the complete repository test suite, skill validation, and `git diff --check`. Run the two live target-agent invocations once, then score and summarize that exact result directory without substituting `--latest` evidence.

## Success and Reporting

The benchmark itself succeeds when both arms complete, both deterministic correctness gates pass, and latency and output-token values are captured. The result may show Fast as better, equal, or worse; README wording must reflect the observed values without filtering an unfavorable outcome.
