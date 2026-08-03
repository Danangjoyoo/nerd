# Nerd UFast Specification and Design

## Decision

UFast will be an explicitly invoked, tool-backed execution modifier.

- The skill chooses when to use the fast path.
- A bundled UFast registry routes bounded generic project operations to
  deterministic backends.
- The active workflow retains scope, authorization, reasoning, and verification.
- Unsupported operations return immediately to the active workflow.
- UFast does not weaken correctness or proof to gain speed.

This differs from XFast, which intentionally trades exploration and proof breadth
for latency.

## Position in the Nerd family

| Skill | Primary speed mechanism | Accuracy contract |
| --- | --- | --- |
| `nerd-fast` | Better operation selection, batching, reuse, and narrow proof | No deliberate accuracy reduction |
| `nerd-xfast` | Batch native text/patch calls, stop exploration early, and use V0 or one end-only V1 wave | Explicitly lossy |
| `nerd-ufast` | Batch routed project, search, edit, and proof operations inside deterministic tools | Preserve the active workflow's accuracy contract |

UFast may compose with Fast and an active specialty. It should not compose with
XFast initially because their guarantees and benchmarks would become difficult
to interpret.

## Goals

- Complete any supported operation with fewer model/tool round trips.
- Move mechanical work from the model into deterministic tools.
- Preserve existing user changes, workspace boundaries, and proof requirements.
- Expose a generic routing contract whose installed tools can remain narrowly
  specialized.
- Fall back cleanly when the operation cannot be handled safely.
- Measure real wall-clock improvement before advertising “ultra-fast” claims.

## Non-goals

- Providing a deterministic tool for every possible request in the first
  release; unsupported work must use the active workflow.
- Creating a universal autonomous engine or nested model router.
- Wrapping `rg`, `sed`, or test commands merely to create more tools.
- Shipping language-specific semantic engines for every language in the first
  release.
- Shipping LSP or AST engines in Phase 1; their adapter boundary is included.
- Replacing Smart, Execute, Surgery, Fast, or XFast.

## Functional requirements

1. UFast activates only when explicitly invoked.
2. It inherits the resolved endpoint, scope, authorization, and proof contract.
3. A registry maps a resolved intent to one installed operation backend.
4. `ufast_project_index` maintains a reusable bounded project map instead of
   returning every file body to the model.
5. `ufast_fast_search` searches one or a batch of independent indexed queries
   and returns bounded matches, context, and exact file hashes.
6. `ufast_safe_edit` applies complete contents or deterministic exact-text
   replacements only against returned hashes.
7. `ufast_test_runner` selects repository-aware allowlisted verification,
   executes independent checks concurrently, and accepts no arbitrary command.
8. Independent tool inputs must be batched through the host's native interface;
   adaptive dependencies remain sequential.
8. Multi-file edits must be atomic or fully recoverable.
9. Every edit must validate expected file versions or hashes before writing.
10. Files outside the authorized workspace or scope must be rejected.
11. Invalid, stale, excessive, or ambiguous batches must produce zero writes.
12. Missing backends, unsupported file types, or unsupported intents must fall
    back to the active workflow without repeated discovery.
13. UFast must not install language servers or dependencies without explicit
    permission.
14. Verification remains owned by the active workflow, which chooses V0 or V1
    once and may accept exact structured proof instead of repeating it.
15. V1 runs safe local focused proof automatically and asks first for broad,
    slow, stateful, external, destructive, configuration-dependent, or
    authority-expanding proof.
15. Results must identify the selected route, backend, cache behavior, and
    whether the fast path applied, fell back, or failed.

## Resolved first capability slice

UFast is generic. It may be invoked for any request, resolves one intent, asks
the registry for a matching installed backend, and returns unsupported work to
the active workflow. Phase 1 exposes four namespaced operations through MCP:

- `ufast_project_index`: build or reuse an in-process project map containing
  paths, file types, sizes, line counts, and hashes without sending all content.
- `ufast_fast_search`: query indexed UTF-8 text with up to ten independent
  queries per call, bounded match context, and hashes for a following edit.
- `ufast_safe_edit`: perform an atomic hash-guarded batch using exact-text
  replacements or complete contents, with rollback on verification failure.
- `ufast_test_runner`: detect and run allowlisted repository verification using
  the same adapter registry available to safe edit.

The current workspace transaction becomes the safe-edit backend rather than
the UFast architecture. Plain UTF-8 indexing, search, and editing are language
neutral. Structural and verification adapters are registered separately;
Phase 1 includes Python, JSON, TOML, Node, Go, Rust, Maven, and Gradle detection
without installing their runtimes or dependencies.

The public edit shape is deliberately flat: each operation contains `path`, the
indexed `sha256`, and either `old_text`/`new_text` or complete `content`.
Repeated paths are grouped into one file transaction, and the tool defaults an
exact replacement to one expected occurrence. The MCP tool is write-capable but
marked non-destructive because it is hash-guarded, atomic, and recoverable;
`readOnlyHint` remains false.

The model owns what outcome is needed. Tools own how to map the project, retrieve
context, mutate files, select backends, and run deterministic checks. Search,
mutation, and proof accept batched inputs; the test runner parallelizes
independent checks. The registry is the stable extension boundary for LSP,
codemod, and AST operations.

## XFast and UFast execution discipline

- XFast batches the agent host's native read/search/text-edit/patch calls, uses
  one reasoning pass, and deliberately narrows accuracy, exploration, and proof.
- UFast uses the smallest registered high-level route, batches inputs inside
  that route, and preserves the active workflow's accuracy and proof contract.
- UFast calls search directly when a known query can build or reuse the index;
  it does not pay for project index plus search by default.
- Supported implementation and test changes share one safe-edit batch and one
  post-edit proof decision. UFast does not create an intermediate red mutation
  or proof round merely to follow a generic red-green ritual.
- This modifier-level sequencing rule overrides an active workflow's generic
  red-green process for supported safe-edit work, while preserving the same
  final behavioral proof outcome. Patch-based editing is not a fallback reason.
- A registered LSP, codemod, or AST route outranks text editing for its semantic
  intent. Missing semantic backends cause fallback, never lossy emulation.
- V0 reuses fresh structured proof or makes no verification claim for eligible
  non-mutating work. V1 runs proportionate local proof automatically or asks
  before proof that expands cost, side effects, or authority.

## Architecture

```text
User request
    |
Active Nerd workflow
    |
nerd-ufast intent policy
    |
UFast operation registry
    |
    +-- project index/cache
    +-- fast indexed search
    +-- hash-guarded safe edit
    +-- repository-aware test runner
    +-- future LSP / codemod / AST adapters
    |
Changed files
    |
Active workflow verification
```

| Component | Responsibility |
| --- | --- |
| `nerd-ufast` skill | Resolve one intent and choose a registered operation |
| Operation registry | Map public operations to installed deterministic backends |
| Project index | Cache a generic project map and content hashes in-process |
| Fast search | Return only bounded relevant context from the index |
| Safe edit | Validate, atomically mutate, verify, and roll back on failure |
| Test runner | Detect and execute allowlisted repository checks |
| STDIO server | Expose the namespaced registry without a runtime dependency |
| Active workflow | Handle authorization, fallback, residual proof, and reporting |

The server implements the narrow stable MCP surface required by Codex and keeps
the core operation contract transport-independent. Codex is the only verified
tool host in the first release. Other hosts fall back until their MCP
configuration is tested.

## Failure behavior

- **Stale index or file hash:** refresh or abort the complete edit; write nothing.
- **Invalid search expression:** reject the query without touching the index.
- **No verification adapter:** report unsupported; never invent a shell command.
- **Out-of-scope reference:** reject the workspace edit.
- **Unsupported workspace:** report unavailable and fall back.
- **MCP server unavailable:** report unavailable and fall back.
- **Partial filesystem failure:** roll back all affected files.
- **Verification failure:** restore all originals and return bounded check
  diagnostics for at most one exact correction.
- **Unsupported request:** skip the fast path rather than approximating it with
  text replacement.

## Later capabilities

After the Phase 1 registry is measured:

- Semantic reference lookup and rename through Language Servers.
- Additional Language Server adapters.
- Repository-aware focused-test selection.
- Import organization and structured dependency updates.
- Existing codemod integration.
- AST transformations for operations unsupported by Language Servers.
- On-disk project-map persistence when in-process cache evidence justifies it.
- Additional generic outcome tools and host integrations.

Generic AST mutation belongs last; mature Language Servers and existing
codemods should be preferred.

## Acceptance criteria

- The operation registry exposes project index, fast search, safe edit, and
  test runner as independent routes with one shared result envelope.
- Project index cache hits avoid rereading unchanged content.
- Fast search returns bounded, in-scope UTF-8 context and exact hashes.
- One fast-search call can carry multiple independent queries.
- Safe edit either leaves the complete verified batch or restores every
  original.
- Safe edit accepts the ergonomic flat hash/replacement shape, groups repeated
  paths, and does not require interactive approval for an already authorized,
  recoverable workspace mutation.
- Concurrent user edits cause a clean precondition failure rather than
  overwriting files.
- Unsupported requests continue through the active workflow.
- Supported operations preserve the active workflow’s verification contract.
- Independent verification checks run concurrently with deterministic output
  ordering; exact returned proof is not duplicated.
- Benchmarks compare UFast and XFast using identical models, effort,
  workspaces, and tasks.
- MCP cold-start and tool-operation timing are reported separately.
- The revised verification pilot uses one discovery/edit case, one repetition,
  Luna and Terra, both UFast and XFast arms, and deterministic correctness
  gates: four workloads and two matched pairs.
- No “10× faster” claim is published unless measured.

This measurement requirement matters: the earlier XFast pilot was approximately
68% slower than Fast, while the later five-case pilot measured approximately 55%
faster. The runtime and benchmark—not the skill name—must establish UFast’s
value.

## Resolved MVP boundaries

- Public scope: generic tool-backed routing for supported operations.
- Phase 1 routes: project index, fast search, safe edit, and test runner.
- First mutation backend: existing UTF-8 workspace files, independent of
  programming language.
- Included structural adapters: Python, JSON, and TOML.
- Included verification detection: Python, Node, Go, Rust, Maven, and Gradle;
  the verification pilot exercises the Python adapter only.
- Runtime: dependency-free STDIO MCP server bundled with nerd-ufast.
- Verified host: Codex.
- Verification corpus: the unchanged discovery/edit case selected from XFast
  v3, one repetition, Luna and Terra.
- Publication wording: report measured results, including slower or equal
  outcomes; do not require or imply a predetermined speed win.
