# Inspect and Apply/Verify Tool Latency Experiment Plan

## Outcome

Build a self-contained experiment that measures only these two comparisons:

1. Custom `inspect` versus the fastest equivalent existing inspect path.
2. Custom `apply_verify` versus the fastest equivalent existing edit-and-verify path.

The experiment excludes skills, task-quality comparisons, prompt changes, and
LLM reasoning. Correctness is a hard gate; client-observed latency is the
result.

## Confirmed Inputs

- Keep all prototype, fixture, runner, and report files under
  `docs/experiments/inspect-apply-verify/`.
- `inspect` is compared with one batched existing command path using exact
  `rg` lookup plus bounded file reads. It is not compared with deliberately
  unbatched commands.
- `apply_verify` is compared with the existing `apply_patch` followed by one
  batched targeted-verification command.
- Both sides receive identical inputs and must produce equivalent outputs.
- No Nerd skill, benchmark condition, model, judge, or agent task is involved.

## KISS Breakdown

- **Required outcome:** Produce reproducible latency evidence for the two tool
  substitutions without involving skill or model behavior.
- **Smallest change:** Add one isolated prototype, deterministic fixtures, one
  benchmark driver, and one report generator under `docs/experiments/`.
- **Proof:** Equivalent results on every sample, followed by paired p50 and p95
  dispatch-to-result latency for each comparison.
- **Not needed:** UFast changes, benchmark-framework registration, agent runs,
  model tokens, task scoring, README claims, or production installation.

## Measurement Boundary

The primary timer starts immediately before dispatching the tool request and
stops after its response is fully received and decoded. Fixture creation,
workspace reset, report generation, and benchmark-driver startup are excluded.

Measure two layers separately:

1. **Operation time:** Time spent performing search/read or patch/check work.
2. **Observed tool time:** Full request/response time, including serialization,
   transport, process startup, and orchestration.

Never infer observed tool time from operation time. If the host runtime does
not expose a programmable timing boundary for an existing tool, mark that
measurement unavailable instead of replacing it with an estimate.

Run a persistent warm-tool measurement as the primary result. Record cold
startup separately so initialization cost cannot distort normal-call latency.

## Comparisons

### 1. `inspect` versus the existing inspect path

Use the same exact query and return this normalized result on both sides:

```text
path, start_line, end_line, content, content_sha256, truncated
```

Cases:

- **Small:** One known symbol in one small file; return one bounded slice.
- **Large:** One exact symbol across a generated multi-file fixture; return
  three bounded slices in stable path order.

Baseline:

```text
one batched command request -> rg exact symbol -> bounded reads -> result
```

Candidate:

```text
one inspect request -> exact lookup and bounded reads -> result
```

Correctness gate: normalized results and content hashes must match exactly.

### 2. `apply_verify` versus the existing edit-and-verify path

Use the same unified patch, starting file hashes, working directory, and
verification commands on both sides. Return this normalized result:

```text
patch_status, changed_paths, diff_sha256, checks, exit_codes, rolled_back
```

Cases:

- **Small:** One-file, one-line patch plus one fast focused test.
- **Large:** Three-file patch plus one batched compile, lint, and unit-test
  verification wave.

Baseline:

```text
apply_patch request -> batched targeted-verification request -> result
```

Candidate:

```text
one apply_verify request -> apply patch -> run targeted checks -> result
```

Correctness gate: final diff hash, changed paths, and check exit codes must
match. Add untimed negative checks for a stale starting hash and a failing
verification command; `apply_verify` must reject or roll back without leaving
a partial workspace.

## Sampling

- Use five warm-up pairs per case and discard them.
- Use 100 measured pairs per case.
- Alternate order within each pair using a fixed seed so neither side always
  runs first.
- Run sequentially on the same machine and filesystem.
- Reset from the same fixture snapshot before every pair.
- Disable unrelated network work and background benchmark parallelism.
- Record OS, CPU architecture, Python version, tool versions, and experiment
  commit in the raw result.

## Reported Metrics

For every tool and case, report:

- successful samples and failures;
- p50 and p95 observed latency in milliseconds;
- p50 operation latency when exposed;
- median paired latency difference;
- speed change: `(baseline - candidate) / baseline * 100`;
- request bytes, response bytes, and spawned-process count;
- baseline request count versus candidate request count.

Include raw paired samples. Do not report only an aggregate percentage.

## Proof Rule

Call the candidate faster for a case only when all conditions are true:

1. Every correctness gate passes.
2. No timed sample falls back to the other path.
3. Candidate p50 and p95 observed latency are both lower.
4. The 95% bootstrap interval for the paired median difference stays above
   zero.

Otherwise report `equal`, `slower`, or `inconclusive`. Results prove local tool
latency on the recorded environment only; they do not prove agent or skill
speed.

## Ordered Work

### Task 1: Create deterministic fixtures and contracts

**Files:**

- Create: `docs/experiments/inspect-apply-verify/README.md`
- Create: `docs/experiments/inspect-apply-verify/cases.json`
- Create: `docs/experiments/inspect-apply-verify/fixtures.py`

**Change:**

- Define the four cases, normalized outputs, fixed seed, warm-up count, sample
  count, and workspace-reset rules.
- Generate fixtures deterministically instead of depending on the current
  repository size or state.

**Proof:**

- Generate each fixture twice and require identical tree and content hashes.

### Task 2: Build the isolated candidate tools

**Files:**

- Create: `docs/experiments/inspect-apply-verify/tools.py`
- Create: `docs/experiments/inspect-apply-verify/tool_server.py`

**Change:**

- Implement only the `inspect` and `apply_verify` contracts needed by the four
  cases.
- Expose operation timing in the response while keeping host-observed timing
  outside the tool.
- Confine paths and commands to the temporary fixture workspace.
- Keep the server persistent for warm measurements and dependency-free unless
  the actual tool transport requires an already-approved runtime package.

**Proof:**

- Direct contract tests prove stable output, path confinement, stale-hash
  rejection, check-result capture, and rollback on failure.

### Task 3: Implement fair baseline adapters

**Files:**

- Create: `docs/experiments/inspect-apply-verify/baselines.py`

**Change:**

- Implement the best existing batched inspect route.
- Implement the existing patch request followed by one batched verification
  request.
- Normalize both baseline responses to the same schemas as the candidates.
- Do not add artificial waits or extra calls to either side.

**Proof:**

- For every case, baseline and candidate normalized outputs are byte-for-byte
  equal before timing is enabled.

### Task 4: Add the paired latency driver

**Files:**

- Create: `docs/experiments/inspect-apply-verify/bench.py`
- Create: `docs/experiments/inspect-apply-verify/test_experiment.py`

**Change:**

- Measure request dispatch through decoded response with
  `time.perf_counter_ns()`.
- Exclude fixture reset and result serialization from timed regions.
- Alternate pair order with the fixed seed, capture cold startup separately,
  and retain every raw sample.
- Fail the run on output mismatch, contamination, partial mutation, or missing
  timing fields.

**Proof:**

```bash
rtk python3 -m unittest docs/experiments/inspect-apply-verify/test_experiment.py -v
```

Expected: fixture, equivalence, isolation, failure, and timing-boundary tests
pass.

### Task 5: Run and report the tool-only experiment

**Files:**

- Create: `docs/experiments/inspect-apply-verify/results/raw.json`
- Create: `docs/experiments/inspect-apply-verify/results/report.md`

**Change:**

- Run the four comparisons with five discarded warm-up pairs and 100 measured
  pairs each.
- Preserve unfavorable and inconclusive results.
- Generate tables for raw latency, paired differences, payload size, process
  count, and request count.
- State separately whether any advantage comes from faster operations, fewer
  host requests, or both.

**Proof:**

```bash
rtk python3 docs/experiments/inspect-apply-verify/bench.py --check
```

Expected: raw evidence validates, report values reproduce from it, and every
reported winner satisfies the proof rule.

## Acceptance Criteria

- No skills, prompts, models, judges, or agent task outcomes enter the test.
- The baseline uses the fastest equivalent batched existing path.
- Both sides receive identical inputs and return equivalent normalized output.
- Each case contains 100 valid measured pairs after warm-up.
- Tool startup and warm-call latency are reported separately.
- `apply_verify` failure paths leave no partial mutation.
- Every speed claim is backed by raw paired samples and the proof rule.
- The report clearly limits conclusions to tool latency on the measured host.

## Self-Review

- **Completeness:** Separately measures `inspect` and `apply_verify`, including
  operation cost, host round trips, correctness, and failure behavior.
- **Simplicity:** Uses four deterministic cases and one local driver; it does
  not modify the shared Nerd benchmark framework.
- **Risk:** The current host may not expose direct programmable dispatch timing
  for built-in tools. In that event, operation latency remains measurable but
  end-to-end built-in-tool latency must be reported as unavailable until the
  host supplies that boundary.
