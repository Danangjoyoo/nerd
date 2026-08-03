# Nerd UFast Research Findings

## Scope

Resolve the first UFast prompt, tool surface, and UFast-only integration path
for the approved five-case UFast-versus-XFast benchmark.

The public modifier is generic. The benchmark corpus is Python because it is
the unchanged requested comparison set, not because UFast is Python-only.

Research date: 2026-08-03.

Local baseline:

- Codex CLI 0.144.5.
- Python MCP SDK is not installed.
- The repository currently has no runtime dependency manager and its benchmark
  fixtures intentionally use the Python standard library.
- The final corpus is the unchanged five-case XFast v3 file with SHA-256
  d533163102f0c94ff294d555d15d2ad511782290ad31f02ba239d0821838d880.

## Primary Sources

- [OpenAI: Model Context Protocol](https://learn.chatgpt.com/docs/extend/mcp)
  documents local STDIO servers, isolated Codex configuration, tool allowlists,
  timeouts, and project or Codex-home configuration.
- [OpenAI: Build an MCP server](https://developers.openai.com/plugins/build/mcp-server)
  recommends focused tools with explicit schemas, structured results, accurate
  annotations, input validation, and representative invalid-input tests.
- [OpenAI: Define tools](https://developers.openai.com/plugins/plan/tools)
  recommends mapping user outcomes to coherent read and write operations and
  rejecting tools that do not serve a documented use case.
- [MCP 2025-11-25 STDIO transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
  defines newline-delimited UTF-8 JSON-RPC over standard input and output.
- [MCP tool specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
  defines tools/list, tools/call, JSON schemas, structured content, execution
  errors, annotations, and server-side validation requirements.
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
  is the preferred general SDK, but adds a runtime dependency and is in a
  major-version transition immediately before this research date.

## Case Operation Map

| Case | Required context | Required write | Focused proof |
| --- | --- | --- | --- |
| Batched edit | alpha.py, beta.py, test_math_ops.py | Replace three existing Python files | Syntax, fixture lint, focused tests, verify_behavior |
| Discovery edit | normalizers.py, registry.py, test_normalizers.py | Replace three existing Python files | Syntax, fixture lint, focused tests, verify_behavior |
| Independent work | alpha.py, beta.py, test_alpha.py, test_beta.py | Replace four existing Python files | Syntax, fixture lint, focused tests, verify_behavior |
| Greeting | feature.py, test_feature.py | Replace two existing Python files | Syntax, fixture lint, focused tests, verify_behavior |
| Slugify | text_tools.py, test_text_tools.py | Replace two existing Python files | Syntax, fixture lint, focused tests, verify_behavior |

The original reference/rename slice has no useful fast-path role in this
corpus. Keeping it as the MVP would benchmark fallback behavior rather than
UFast.

## Prompt Decision

### Selected: thin modifier

UFast inherits the active workflow, selects one installed namespaced route,
and uses this bundled workspace fast path when it matches:

1. Call `ufast_prepare_workspace_change` once.
2. Produce the complete requested text changes and required proof artifacts.
3. Call `ufast_apply_workspace_change` once.
4. If the transaction succeeds, report its proof.
5. If unsupported, fall back immediately.
6. Retry only once when the tool returns an exact, local, recoverable error.

The skill does not plan, route, or replace Smart or Execute. It does not compose
with XFast.

### Rejected: self-contained UFast workflow

This duplicates XFast’s ownership of the complete execution workflow and makes
the comparison about prompt policy rather than deterministic tools.

## Tool Decision

### ufast_prepare_workspace_change

Read-only. It returns a bounded snapshot of existing editable UTF-8 workspace
files, SHA-256 preconditions, detected verification adapters, and runtime
timing. It skips binary data and excludes hidden agent configuration, VCS data,
caches, dependencies, generated output, `lint_check.py`, and
`verify_behavior.py` contents.

Limits:

- Workspace root fixed by server configuration.
- Any workspace whose editable text fits the bounded snapshot.
- Existing files only.
- At most 12 files and 128 KiB of model-visible content.
- No symlinks, path traversal, generated caches, or hidden directories.

### ufast_apply_workspace_change

Write operation. It accepts complete replacement contents and the exact hashes
returned by prepare. It validates the entire batch, writes atomically, runs
applicable fixed adapters, and either commits the complete batch or restores
the original files. Plain UTF-8 text is generic; Python, JSON, and TOML receive
structural validation.

The server chooses checks; callers cannot submit arbitrary commands:

- Python syntax compile for changed Python files.
- JSON and TOML parsing before mutation.
- The repository-local `lint_check.py` when the Python fixture adapter applies.
- Changed Python test modules matching `test_*.py`.
- The repository-local `verify_behavior` module for Python fixture cases.

Results contain stable status, changed paths, check names, exit codes, bounded
output, cold-start time, operation time, and rollback state.

### Rejected alternatives

- Shell aliases around search, patch, or test add names but no measured
  capability or safety property.
- LSP rename and reference tools do not serve the selected feature cases.
- A generic AST engine and multi-language adapters exceed the MVP.
- A nested LLM inside the tool duplicates reasoning cost and weakens benchmark
  attribution.

## Transport Decision

Use a local dependency-free STDIO MCP server bundled under the UFast skill.
Implement only initialization, ping, tools/list, and tools/call from the stable
2025-11-25 protocol needed by Codex 0.144.5. Echo a supported client protocol
version during initialization and test the real Codex handshake before
freezing.

Why not the SDK in this MVP:

- The repository currently has no runtime dependency installation path.
- Fresh benchmark homes must not pay network or package-resolution cost.
- The server exposes only two tools and no resources, prompts, authentication,
  HTTP transport, tasks, or sampling.
- A later move to the official SDK remains compatible with the same tool
  schemas.

## UFast-Only Integration Decision

Benchmark isolation:

- XFast keeps its existing isolated home, ignored user configuration, and only
  the nerd-xfast skill.
- UFast receives nerd-smart, nerd-execute, and nerd-ufast.
- The runner writes a temporary Codex-home config only for the UFast condition.
- That config launches the copied UFast server and fixes its workspace root.
- The runner captures a private telemetry log before deleting the temporary
  home.
- Tests reject UFast runtime files, config, advertised tools, or events in the
  XFast condition.

Production integration:

- The server remains bundled with the skill.
- Codex is the only verified UFast tool host in the first release.
- Installation uses an explicit Codex MCP configuration step.
- Other hosts can install the skill, but the fast path reports unavailable and
  falls back until their integration is verified.
- Tool names remain globally visible on Codex once configured; UFast-only
  ownership is enforced by the nerd_ufast namespace, skill instructions, and
  exact benchmark isolation. README wording must not claim stronger host-level
  access control.

## Freeze Gates

The implementation can freeze when:

- Both tool schemas have deterministic contract tests.
- All five case shapes map to the two-tool path.
- A real isolated Codex smoke run advertises and invokes the tools.
- XFast materialization contains no UFast assets or configuration.
- The prompt invokes the fast path without weakening proof or scope.

No critical MVP design question remains unresolved.

## Calibration and Freeze Record

The public scope was corrected during calibration: UFast is generic, while the
Python corpus exercises only one verification adapter. The Python-specific
tool names and prompt wording were discarded before final evaluation.

Calibration history:

1. `20260803T034747Z-4fba672-gpt-5.6-luna-high` proved that Codex could call
   both MCP operations, but private telemetry was absent because the MCP child
   did not inherit the intended variables. The runner was changed to pass the
   workspace and log paths explicitly in the isolated MCP configuration.
2. `20260803T035029Z-4fba672-gpt-5.6-luna-high` proved the corrected telemetry
   and XFast isolation, but was superseded when the public contract was
   corrected from Python-only to generic.
3. `20260803T035820Z-4fba672-gpt-5.6-luna-high` is the accepted generic-route
   calibration. XFast and UFast both exited zero and passed the same three
   proof commands. UFast recorded
   `ufast_prepare_workspace_change:ready` and
   `ufast_apply_workspace_change:applied`; XFast recorded no UFast runtime,
   configuration, or event. Calibration latency was 45.1855 seconds for XFast
   and 47.4440 seconds for UFast, so no favorable latency assumption was used
   to justify the final experiment.

The first attempted Luna evaluation,
`20260803T040050Z-4fba672-gpt-5.6-luna-high`, produced ten valid workloads but
zero judge tasks. The shared scorer still resolved the `xfast` comparison to
the historical Fast-versus-XFast conditions instead of the two conditions in
the active config. That evidence was preserved but excluded. The scorer now
derives each pair from the frozen config, its regression test creates all five
UFast-versus-XFast judge tasks, and scorer source is part of provenance.

The next Luna result,
`20260803T041215Z-4fba672-gpt-5.6-luna-high`, passed all ten workload gates,
created five valid blinded judgments, and produced ten passing scores. The
following Terra result,
`20260803T042242Z-4fba672-gpt-5.6-terra-high`, also passed all functional and
isolation gates, but only three of five UFast runs selected the installed tool
route. On the other two supported cases, the model incorrectly treated lack of
prior repository inspection and a preferred red-green sequence as reasons to
fall back. Both results were excluded together to prevent mixed-source
evidence. The generic capability prompt now defines prepare as the eligibility
inspection and distinguishes those situations from real disqualifiers.
Targeted Terra routing calibration
`20260803T043327Z-4fba672-gpt-5.6-terra-routing-high` then reran the two
affected case shapes. Both runs exited zero, passed every proof command, and
recorded `prepare:ready` followed by `apply:applied`.

After those corrections, the complete 202-test deterministic suite passed and
the restarted final evaluation source was frozen at:

| Source | SHA-256 |
| --- | --- |
| Case corpus | `d533163102f0c94ff294d555d15d2ad511782290ad31f02ba239d0821838d880` |
| UFast skill | `ea81bd7f63c0e7544b7e53dcde1e052474a9ca56a2416adb7508681e1cdd5737` |
| UFast core | `a775850a573b2e9b6040392366804020d024804fa3aaec21d005109f9af40e7e` |
| UFast server | `42a5d615718dcc0f11cc45ad7924851c17ca8b5b5047e8480d67c553da019882` |
| Benchmark runner | `5f19bfd20fd1d475b5feccfdecc10e82bd8ea6a96d3be84733f31cae38ffe538` |
| Benchmark materializer | `92659940ca024eb33fb8bbd3116c498beb0d0ca33a0cfbcf270d37a83f94660c` |
| Benchmark adapter | `e95989490f0b75513e8432f766e7897a6f43061736f8a768fc3422e51cb0685a` |
| Benchmark scorer | `5afaa3d5bd90ddfe48811a37f17c993d553d57f54d3b82c1a6bd5170bbed4ba7` |
| UFast reporter | `8468734d6047144fe9545ecb7b39a33c8deaff0df80836c8ab299eb53deaa826` |

The final 30-run matrix must reject any result whose manifest differs from
these hashes or whose case corpus differs from the original baseline.

## Final Evaluation Record

The accepted result directories are:

- Luna: `20260803T043454Z-4fba672-gpt-5.6-luna-high`
- Terra: `20260803T044648Z-4fba672-gpt-5.6-terra-high`
- Sol: `20260803T045454Z-4fba672-gpt-5.6-sol-high`

Together they contain 30 fresh workloads, 15 matched pairs, 15 complete
blinded judgments, and 30 valid scores. Both conditions passed every run with
zero hard-gate failures. XFast contained no UFast runtime, configuration, or
tool event. UFast selected its tool route in all 15 runs, applied 14
transactions, and completed one honest fallback after hash-precondition
rejection.

The combined directional result was unfavorable to UFast: 95.33% mean score
versus 96.67% for XFast, 46.40 seconds versus 41.83 seconds median latency,
and 2.75% more paired-median output tokens. The paired speed calculation
reports UFast as 15.27% slower. Median UFast cold start was 25 ms and median
tool-operation time was 637 ms. These five Python cases and one repetition per
model do not establish universal accuracy or latency behavior for the generic
modifier.
