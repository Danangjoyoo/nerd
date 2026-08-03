# Nerd UFast Research Findings

## Scope and Correction

Research date: 2026-08-03.

UFast is a generic tool-backed modifier, not a Python change tool. Its first
implementation used only a full-workspace snapshot and batch writer. That
experiment was useful but did not implement the requested project map, search,
standalone verification, or extensible router. It also measured 15.27% slower
paired latency than XFast across the historical five-case run. Those results
remain historical evidence for the superseded source and are not reused for
the corrected architecture.

The corrected Phase 1 decision is an operation registry with four independent
tools: project index, fast search, safe edit, and test runner. Language Server
and AST/codemod backends extend that registry in later phases.

## Primary Sources

- [OpenAI: Model Context Protocol](https://learn.chatgpt.com/docs/extend/mcp)
  documents local STDIO servers and Codex MCP configuration.
- [OpenAI: Build an MCP server](https://developers.openai.com/plugins/build/mcp-server)
  recommends focused tools, explicit schemas, structured results, accurate
  annotations, validation, and representative error tests.
- [OpenAI: Define tools](https://developers.openai.com/plugins/plan/tools)
  recommends mapping tools to coherent user outcomes.
- [MCP 2025-11-25 STDIO transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
  defines newline-delimited UTF-8 JSON-RPC over standard input and output.
- [MCP tool specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
  defines tool discovery, invocation, JSON schemas, structured content,
  annotations, and execution errors.
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
  remains the preferred general SDK, but the dependency-free server is the
  smaller reproducible choice for this repository and its isolated benchmarks.

Local constraints at research time:

- Codex CLI 0.144.5.
- No installed Python MCP SDK.
- No repository runtime dependency manager.
- Benchmark fixtures intentionally rely on standard-library Python.

## Prompt Research

### Selected: thin intent modifier

The active workflow first resolves endpoint, scope, authorization, and proof.
UFast then resolves one mechanical intent and asks the registry for a backend:

1. Unknown project shape: project index.
2. Target discovery: fast indexed search.
3. Deterministic existing-file mutation: safe edit.
4. Repository proof: test runner.
5. Unsupported semantic or structural intent: immediate workflow fallback.

The prompt names stable outcomes, not implementation libraries. It accepts
exact structured proof without rerunning it, allows one evidence-specific
invocation correction, and never turns lack of prior inspection into a fallback
reason because index and search provide that inspection.

Its batching discipline matches Fast at the host boundary while moving more
work inside each deterministic operation. Known independent searches share one
multi-query call, all file changes share one transaction, and selected checks
share one test-runner call whose independent commands run concurrently. Search
can build the cache directly, so project index is not a mandatory extra round.

Proof is selected once. V0 reuses fresh structured evidence or avoids a proof
claim for eligible non-mutating work. V1 runs safe local focused checks
automatically when authorized and proportionate, or asks first when proof is
broad, slow, stateful, external, destructive, configuration-dependent, or
requires more authority. UFast never downgrades the active workflow's proof.

### Rejected prompt directions

- A self-contained UFast workflow duplicates Smart and Execute.
- A two-call “prepare/apply” prompt makes a particular transaction backend the
  architecture and returns unnecessary full-workspace content.
- Python-specific wording confuses the exercised benchmark adapter with UFast's
  public scope.
- A large catalog of backend-specific tools forces the model to perform routing
  that belongs in the registry.

## Tooling Research

### Level 1: shell commands

Small shell tools remain useful prototypes, but aliases around search, edit, or
test commands do not create a meaningful UFast capability. An accepted tool
must reduce model/tool rounds, enforce a safety property, or both. Arbitrary
shell-command execution is explicitly outside the test-runner contract.

### Level 2: MCP operation server — selected for Phase 1

The dependency-free STDIO server exposes four namespaced operations through a
shared registry and result envelope.

#### `ufast_project_index`

- Builds or reuses a bounded in-process UTF-8 project map.
- Returns paths, types, sizes, line counts, hashes, cache status, and index ID.
- Does not return all file bodies to the model.
- Excludes VCS data, agent configuration, dependencies, caches, build output,
  symlinks, binaries, and protected fixture support files.

#### `ufast_fast_search`

- Searches cached text using one or up to ten batched literal or
  regular-expression queries.
- Returns only relevant context, exact locations, and source hashes.
- Reuses the project map and reports cache hit or rebuild behavior.

#### `ufast_safe_edit`

- Accepts complete contents or deterministic exact-text replacements.
- Requires source hashes and rejects stale or ambiguous batches before writing.
- Applies existing-file UTF-8 changes atomically with workspace containment.
- Validates Python, JSON, and TOML before mutation.
- Runs detected allowlisted checks and restores originals after check failure or
  partial filesystem replacement.

#### `ufast_test_runner`

- Detects Python, Node, Go, Rust, Maven, and Gradle repositories.
- Selects only allowlisted, changed-language-relevant checks and runs
  independent commands concurrently with deterministic result ordering.
- Accepts check names but no arbitrary command input.
- Returns bounded output, exit codes, backends, and durations.

The benchmark case happens to exercise the Python adapter. The public index,
search, mutation, router, transport, and result envelopes are language neutral.

### Level 3: Language Servers — Phase 2

Semantic reference lookup and rename should use mature language servers such as
Pyright, JDT LS, gopls, or an available Kotlin server. Adapters will register
`find_references` and `rename_symbol` intents only when the relevant server is
already available or installation is separately authorized. Phase 1 must not
approximate semantic rename with global text replacement.

### Level 4: AST and codemods — Phase 3

Use existing codemods or language-specific AST libraries only for operations an
LSP cannot safely perform. A universal tree mutation engine is deferred because
language semantics, formatting preservation, and dependency cost differ by
ecosystem. These adapters use the same registry and shared safety envelope.

## Router Decision

The model reasons in four Phase 1 intents while the registry owns backend
selection. The registry maps a public operation name and intent to a handler,
backend label, schema, and MCP annotation. Later LSP and AST routes register at
the same boundary. This keeps the prompt stable as capabilities grow and makes
unsupported semantic intents explicit rather than silently lossy.

## Transport and UFast-Only Integration

Use a local dependency-free STDIO MCP server bundled inside the UFast skill. It
implements initialization, ping, `tools/list`, and `tools/call` for the stable
protocol surface used by Codex. No network resolution or package installation
is required in a fresh benchmark home.

Benchmark isolation has three layers:

- All public names use the `ufast_` namespace.
- Only the UFast condition receives the skill, runtime modules, and temporary
  Codex MCP configuration.
- Private telemetry proves route/backend use and tests reject any UFast asset,
  config, advertisement, or event in XFast.

Production installation is explicit and Codex-only for this release. Once an
MCP server is configured, Codex can see its tools globally; UFast-only ownership
therefore comes from namespacing and skill policy, not hidden host capabilities.
Other hosts must fall back until their integration is verified.

## Verification Corpus Decision

The user reduced the corrected verification to one case, one repetition, and
two models: Luna and Terra. The source is a byte-for-byte copy of the existing
`xfast-v3-discovery-edit` case, including fixture, prompt, proof commands, and
criteria.

- Source: `benchmarks/cases/ufast-phase1-verification.json`
- SHA-256: `6f6ba4ea8c190189428deb9e411b63acd9be3026f53cb954614159002e456791`
- Conditions: XFast and UFast.
- Total: four workloads and two matched pairs.

This pilot verifies integration and yields a directional comparison only. It
does not establish stable latency, statistical significance, all-language
correctness, or a universal speed factor.

## Freeze Gates

The corrected source can freeze after:

- deterministic contracts cover all four tool schemas and routes;
- a real STDIO session invokes index, search, safe edit, and test runner;
- path, hash, ambiguity, atomicity, rollback, and command-allowlist failures are
  covered;
- installation copies every runtime module and remains idempotent;
- UFast benchmark materialization contains the runtime and MCP config while
  XFast contains neither;
- the complete repository suite passes;
- the prompt invokes project context plus safe edit on the selected case.

The final source hashes, accepted result directories, scores, and directional
measurements are recorded here only after the corrected four-workload run is
complete.

## Corrected Source Freeze

The 212-test staged-tree suite, skill validator, Python compilation, and diff
checks passed before live evaluation. The corrected benchmark source is frozen
at:

| Source | SHA-256 |
| --- | --- |
| Case corpus | `6f6ba4ea8c190189428deb9e411b63acd9be3026f53cb954614159002e456791` |
| XFast skill | `a3657d201205571d045acb0249be74e11eb66f2d211fe81aa86ff0fb7426c0f3` |
| UFast skill | `3b607171572ddb425279145a899a61972d8af0f3a54a008a4bfeff3e798cd216` |
| UFast core | `5386cf18786a320d8e3c93eb8489358bdcac8941fcc9740ac5e9fa9e4fd545c9` |
| UFast index | `310ea272e50086865dbd10911a5e78bdffc0c96de65be7011a6ddda13666dd76` |
| UFast registry | `81f7cd62eae20de1fcf901acb94ce7787c05ab08dd063054b8c5e870098e724e` |
| UFast verifier | `afbbf5ecfe11a89169b062cc5789f70517e907227d3f34f988185e3e41166ea3` |
| UFast server | `57cf069818250fa5c22fae471cb0134bafd39f55c6a7c55fb737bd58fee8d02f` |
| Benchmark runner | `e910818e8cb73ae2bd2a7fce1a3a95993854ba8188318b9a7270859fe4232d0b` |
| Benchmark materializer | `92659940ca024eb33fb8bbd3116c498beb0d0ca33a0cfbcf270d37a83f94660c` |
| Benchmark adapter | `e95989490f0b75513e8432f766e7897a6f43061736f8a768fc3422e51cb0685a` |
| Benchmark scorer | `5afaa3d5bd90ddfe48811a37f17c993d553d57f54d3b82c1a6bd5170bbed4ba7` |
| UFast reporter | `a781de87b510a4db7f6f5a5047244ed6507e4378408767ecec84377494114208` |

The accepted Luna and Terra result directories and their measured values are
appended after judging and scoring succeeds.
