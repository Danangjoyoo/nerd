# Nerd UFast Specification and Design

## Decision

UFast will be an explicitly invoked, tool-backed execution modifier.

- The skill chooses when to use the fast path.
- A bundled UFast runtime performs bounded generic workspace operations.
- The active workflow retains scope, authorization, reasoning, and verification.
- Unsupported operations return immediately to the active workflow.
- UFast does not weaken correctness or proof to gain speed.

This differs from XFast, which intentionally trades exploration and proof breadth
for latency.

## Position in the Nerd family

| Skill | Primary speed mechanism | Accuracy contract |
| --- | --- | --- |
| `nerd-fast` | Better operation selection, batching, reuse, and narrow proof | No deliberate accuracy reduction |
| `nerd-xfast` | Minimal exploration, immediate output, bounded proof | Explicitly lossy |
| `nerd-ufast` | Replace repeated context, editing, and proof rounds with deterministic tools | Preserve correctness for supported operations |

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
- Building a generic AST transformation framework initially.
- Replacing Smart, Execute, Surgery, Fast, or XFast.

## Functional requirements

1. UFast activates only when explicitly invoked.
2. It inherits the resolved endpoint, scope, authorization, and proof contract.
3. It asks the runtime whether the requested operation is supported.
4. A supported change uses one bounded prepare call and one atomic apply call.
5. The runtime accepts complete file replacements only for files and hashes
   returned by the prepare call.
6. Multi-file edits must be atomic or fully recoverable.
7. Every edit must validate expected file versions or hashes before writing.
8. Files outside the authorized workspace or scope must be rejected.
9. Invalid, stale, excessive, or ambiguous file batches must produce zero
   writes.
10. Missing tools, unsupported file types, or unsupported intents must fall
    back to the active workflow without repeated discovery.
11. UFast must not install language servers or dependencies without explicit
    permission.
12. Verification remains owned by the active workflow and uses its existing
    proof requirements.
13. The result must state whether the UFast path was used and what operation it
    performed.

## Resolved first capability slice

UFast is generic. It may be invoked for any request, selects a matching
installed `nerd_ufast` tool route once, and immediately returns unsupported
work to the active workflow. The first bundled route is a language-neutral,
bounded UTF-8 workspace transaction:

- `ufast_prepare_workspace_change` snapshots existing editable text files,
  their SHA-256 hashes, limits, and available verification adapters.
- `ufast_apply_workspace_change` validates a complete replacement batch,
  applies it atomically, runs the applicable fixed adapters, and rolls the
  batch back when verification fails.

The transaction handles plain UTF-8 text generically and performs structural
validation for Python, JSON, and TOML. Its first benchmark happens to use five
Python feature-implementation cases, so that corpus additionally exercises the
Python syntax, fixture-lint, focused-test, and behavior adapters. Those cases
measure one adapter; they do not define UFast's public scope.

The model still owns intent and domain logic. Tools own bounded context
collection, stale-write prevention, recoverable multi-file mutation, and any
deterministic checks they advertise. Existing files and a small size/file-count
ceiling keep the first route deterministic.

## Architecture

```text
User request
    |
Active Nerd workflow
    |
nerd-ufast policy
    |
UFast STDIO MCP server
    |
    +-- bounded UTF-8 workspace snapshot
    +-- hash-guarded atomic replacement
    +-- applicable verification adapters
    |
Changed files
    |
Active workflow verification
```

| Component | Responsibility |
| --- | --- |
| `nerd-ufast` skill | Decide whether the deterministic fast path applies |
| Prepare tool | Return bounded text context, hashes, and adapter capabilities |
| Apply tool | Validate, atomically replace, verify, and roll back on failure |
| STDIO server | Expose the two namespaced tools without a runtime dependency |
| Active workflow | Handle authorization, fallback, verification, and reporting |

The server implements the narrow stable MCP surface required by Codex and keeps
the core operation contract transport-independent. Codex is the only verified
tool host in the first release. Other hosts fall back until their MCP
configuration is tested.

## Failure behavior

- **Stale file hash:** abort the complete edit; write nothing.
- **Out-of-scope reference:** reject the workspace edit.
- **Unsupported workspace:** report unavailable and fall back.
- **MCP server unavailable:** report unavailable and fall back.
- **Partial filesystem failure:** roll back all affected files.
- **Verification failure:** restore all originals and return bounded check
  diagnostics for at most one exact correction.
- **Unsupported request:** skip the fast path rather than approximating it with
  text replacement.

## Later capabilities

After the generic workspace transaction is measured:

- Semantic reference lookup and rename through Language Servers.
- Additional Language Server adapters.
- Repository-aware focused-test selection.
- Import organization and structured dependency updates.
- Existing codemod integration.
- AST transformations for operations unsupported by Language Servers.
- A richer persistent project map.
- Additional generic outcome tools and host integrations.

Generic AST mutation belongs last; mature Language Servers and existing
codemods should be preferred.

## Acceptance criteria

- Every selected benchmark case uses the UFast fast path rather than fallback.
- Prepare returns only bounded, in-scope UTF-8 context and exact hashes.
- Apply either leaves the complete verified batch or restores every original.
- Concurrent user edits cause a clean precondition failure rather than
  overwriting files.
- Unsupported requests continue through the active workflow.
- Supported operations preserve the active workflow’s verification contract.
- Benchmarks compare UFast and XFast using identical models, effort,
  workspaces, and tasks.
- MCP cold-start and tool-operation timing are reported separately.
- The approved directional pilot uses five cases, one repetition, three
  models, and deterministic correctness gates.
- No “10× faster” claim is published unless measured.

This measurement requirement matters: the earlier XFast pilot was approximately
68% slower than Fast, while the later five-case pilot measured approximately 55%
faster. The runtime and benchmark—not the skill name—must establish UFast’s
value.

## Resolved MVP boundaries

- Public scope: generic tool-backed routing for supported operations.
- First bundled route: existing UTF-8 workspace files, independent of
  programming language.
- Included structural adapters: Python, JSON, and TOML; the published pilot
  exercises the Python adapter only.
- Runtime: dependency-free STDIO MCP server bundled with nerd-ufast.
- Verified host: Codex.
- Published corpus: the unchanged five-case XFast v3 corpus.
- Publication wording: report measured results, including slower or equal
  outcomes; do not require or imply a predetermined speed win.
