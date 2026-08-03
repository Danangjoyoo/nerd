# Nerd UFast Phase 1 Research, Build, Benchmark, and Release Plan

## Outcome

Deliver UFast as a generic, explicitly invoked, tool-backed execution modifier.
Phase 1 must expose a registry/router plus four independent MCP operations:

- `ufast_project_index`
- `ufast_fast_search`
- `ufast_safe_edit`
- `ufast_test_runner`

The implementation must be verified against XFast with one unchanged case, one
repetition, and the Luna and Terra models only. Completion means the code,
evidence, README, commit, pull request, and required checks are all complete.

## Confirmed Boundaries

- UFast is generic; it is not a Python-change tool.
- The active Nerd workflow owns intent, authorization, residual reasoning, and
  proof. UFast replaces supported mechanical rounds with deterministic tools.
- Phase 1 operates on existing UTF-8 text files and detects common repository
  verification backends without installing dependencies.
- Language Server operations are Phase 2. AST and codemod operations are Phase
  3. Both extend the same registry rather than changing the UFast prompt.
- UFast and XFast do not compose in one workload.
- Codex is the only host whose MCP integration is verified in this release.
- Do not merge the pull request without separate user authorization.

## Worktree Safety

The worktree contains unrelated user changes in existing Smart, Fast, XFast,
agent metadata, and shared contract-test files. Preserve those changes and
stage only UFast-owned files or UFast-specific hunks. Recheck status and the
staged diff before every commit and push boundary.

## 1. Research

### 1.1 Tune the UFast prompt

1. Compare the current Fast and XFast contracts with the approved UFast design.
2. Keep UFast as a thin modifier: resolve one intent, choose one registered
   route, consume structured evidence, and fall back immediately when the route
   is unavailable or unsafe.
3. Make the speed discipline explicit: XFast batches native text/patch calls
   and accepts bounded loss; UFast batches higher-level registry inputs and
   preserves the active workflow's accuracy contract.
4. Test the prompt against four behaviors:
   - unknown project shape uses project index;
   - target discovery uses indexed search;
   - deterministic changes use one hash-guarded safe-edit batch;
   - returned verification is accepted without duplicate proof.
5. Add a V0/V1 proof ladder: reuse structured evidence at V0, run safe focused
   V1 automatically, and ask before proof that expands cost, state, side
   effects, configuration, or authority.
6. Reject wording that makes the model emulate the backend, assumes Python, or
   turns UFast into another end-to-end workflow.
7. Freeze the prompt before the published benchmark.

### 1.2 Resolve how UFast creates new tools

Evaluate the feedback’s four implementation levels by capability, safety, and
round-trip reduction:

1. Shell scripts are suitable only for prototypes; wrappers around `rg`,
   `sed`, or arbitrary test commands do not justify a public tool.
2. Phase 1 uses a dependency-free STDIO MCP server with an operation registry.
   Implement project index, fast search, safe edit, and test runner as distinct
   handlers with bounded schemas and a shared result envelope.
3. Phase 2 registers Language Server adapters for semantic references and
   rename, preferring existing LSP implementations over new parsers.
4. Phase 3 registers mature codemods or AST adapters for transformations an LSP
   cannot perform safely.

Each accepted backend must reduce a model/tool round, add a deterministic
safety property, or both. New operations register by intent and do not require
the model to know backend-specific implementation details.

### 1.3 Resolve UFast-only integration

1. Bundle the runtime with `nerd-ufast` and use namespaced `ufast_*` tool names.
2. Add an explicit Codex installation path that copies all runtime modules and
   writes one MCP configuration entry.
3. In benchmarks, materialize UFast only in the UFast condition. XFast receives
   no UFast skill, runtime, configuration, advertised tools, or telemetry.
4. Capture private tool telemetry with route, backend, cache status, timing,
   changed paths, checks, and rollback state.
5. State the real boundary: an installed Codex MCP server is host-visible, so
   UFast-only ownership is enforced by namespacing, skill policy, and exact
   benchmark isolation—not by an unsupported host-level visibility claim.

Research is complete only when the prompt, registry, transport, installation,
fallback, and isolation contracts have no unresolved implementation decision.

## 2. Build Phase 1

### Project index and search

- Cache bounded UTF-8 project content in the MCP process.
- Return project metadata and hashes without returning every file body.
- Invalidate after workspace signature changes or a successful safe edit.
- Support up to ten bounded literal or regular-expression queries per call with
  context and exact hashes suitable for the next edit.
- Exclude VCS data, agent configuration, dependencies, caches, generated
  output, symlinks, binary files, and protected fixture support files.

### Safe edit

- Accept exact-text replacements or complete contents for existing files.
- Require SHA-256 preconditions and reject stale or ambiguous batches.
- Enforce workspace containment, file-count, and byte limits.
- Validate Python, JSON, and TOML structurally before mutation.
- Write the batch atomically and restore every original after a failed check or
  partial replacement.

### Test runner

- Accept changed paths and allowlisted check names, never arbitrary commands.
- Detect Python, Node, Go, Rust, Maven, and Gradle repositories.
- Select only adapters relevant to changed files; a pathless call may select
  the complete detected repository plan.
- Run independent detected checks concurrently and return bounded output, exit
  codes, backend names, and duration in deterministic order.

### Registry and MCP transport

- Map intent to handler and backend through one extension registry.
- Advertise exactly the four Phase 1 tools.
- Keep a stable structured result envelope and error behavior.
- Reserve semantic rename/reference and AST/codemod intents for later adapters;
  do not approximate them with unsafe text replacement.

## 3. Verify and Benchmark Against XFast

### Deterministic verification

- Unit-test cache build, hit, invalidation, limits, and bounded search.
- Unit-test exact replacement, stale hash, ambiguity, traversal, symlink,
  atomic replacement failure, verification failure, and rollback.
- Unit-test language-aware verification detection and command allowlisting.
- Exercise a real STDIO MCP session across all four tools.
- Verify installer idempotence, runtime completeness, UFast-only condition
  materialization, telemetry parsing, and README generation.
- Run the complete repository test and validation suites before benchmarking.

### Published benchmark matrix

Use a byte-for-byte copy of the existing `xfast-v3-discovery-edit` case and its
proof criteria. The copied case source is
`benchmarks/cases/ufast-phase1-verification.json`, SHA-256
`6f6ba4ea8c190189428deb9e411b63acd9be3026f53cb954614159002e456791`.

| Dimension | Value |
| --- | --- |
| Cases | 1 discovery/edit case |
| Repetitions | 1 |
| Models | GPT 5.6 Luna high, GPT 5.6 Terra high |
| Conditions | XFast, UFast |
| Workloads | 4 |
| Matched pairs | 2 |

Validity gates:

- Same model, effort, prompt, fixture, proof commands, and clean materialized
  workspace inside each pair.
- Every workload exits zero and passes all deterministic hard gates.
- UFast records project context through index or search plus safe edit; any
  fallback is retained and reported.
- XFast records no UFast runtime, config, advertised tool, or event.
- Manifests contain the frozen source hashes and exact copied-case digest.
- Blind judgment and scoring complete for both pairs.

Report correctness, median latency, paired speed delta, output tokens, tool
calls, cache behavior, cold start, operation time, and fallback count. With one
case and one repetition, label all comparisons directional and make no claim of
statistical significance or general language coverage.

## 4. Update the README

1. Describe UFast as tool-backed execution, not another prompt-only speed mode.
2. Name the Phase 1 registry routes in plain language: reusable project map,
   indexed search, atomic safe edit, and repository-aware test runner.
3. Explain that LSP and AST/codemod adapters are later phases.
4. Explain explicit Codex setup and the verified-host limitation.
5. Generate the benchmark block from the checked result artifact; never hand
   edit measured values.
6. Publish unfavorable or neutral results honestly and keep the one-case,
   one-repetition limitation adjacent to the numbers.

## 5. Release and Terminal Verification

1. Freeze implementation and benchmark source hashes.
2. Run Luna and Terra, then judge and score each result directory.
3. Generate `benchmarks/pilots/ufast-vs-xfast/result.json` and publish/check the
   README benchmark region.
4. Run the full deterministic suite again, including validation, compile checks,
   case-digest checks, and skill discovery.
5. Stage only intended files and shared-file hunks; inspect the staged diff.
6. Commit, push `feat/nerd-ufast`, update pull request #13, and monitor required
   checks until green.

Completion requires all four tools, valid four-workload evidence, synchronized
README wording, preserved user changes, a pushed commit, and a green open pull
request.
