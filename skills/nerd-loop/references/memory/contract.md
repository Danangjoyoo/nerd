# Behavioral Memory: Contract

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Behavioral Memory router](index.md) and load it only for its named trigger.

## Behavior Contract

After admission, compile the effective endpoint into a versioned Behavior
Contract associated with exactly one independent root task episode. For a
memory-tainted endpoint, do this only after its proposal is consumed; for
disabled, incompatible, or memory-free states, compile the unchanged
memory-blind endpoint. The contract makes accepted behavior deterministic and
inspectable during later iterations.

Use this record:

> **Behavior Contract — [Root loop / revision]**
> - **Root episode:** [Stable independent task episode ID]
> - **Memory state:** [disabled | memory_incompatible | memory_free | consumed]
> - **Current guidance:** [Explicit fields and source references]
> - **Effective behavior:** [Canonical seven-field endpoint]
> - **Compilation:** [Where each field affects profile, route, DoD, optional Loop Map, stopping, or verification]
> - **Routing resolution:** [Proposal reference; chain, authenticated-registry,
>   skill-role/incompatibility metadata, and explicit authority hashes; ordered
>   atomic profiles; full-chain preflight result; common admission hash,
>   cumulative budget revision, and initial reducer cursor, or none]
> - **Applicability:** [Stable namespace, scope, and context hashes]
> - **Memory provenance:** [Proposal ID/hash and pattern IDs/revisions, or none]
> - **Loop contract revision:** [Revision/hash]
> - **Invalidation triggers:** [Material input, scope, field, or authority changes]

Store material endpoint values in the selected Loop state so execution never
depends on replaying memory. For S2/S3, persist only memory provenance
references with the contract and ledger. Never persist the plaintext grant
token, raw prompt or transcript, copied evidence text, hidden reasoning, or a
reusable trusted confirmation reference.

Tag each effective field by source:

- `current_explicit`;
- `mandatory_checked_in_contract` or `advisory_checked_in_contract`;
- `confirmed_memory:<pattern-id>@<revision>`; or
- `derived_mandatory_constraint`.

Source tags make later corrections precise. A direct correction can replace
one affected field and invalidate its dependent plan nodes without discarding
unrelated verified work.
## Mapping the Seven Pattern Types

Compile the seven Nerd Memory fields as follows:

| Memory type | Loop destination | Allowed influence | Never infer |
| --- | --- | --- | --- |
| `goal` | Working Objective and route/Loop Map priority when present | Desired outcome or priority absent from current input | Hidden motive, permission, or completion |
| `task` | Route hints and decomposition only when the selected profile needs them | Reusable subtasks or ordering patterns | An already-approved executable queue |
| `action` | Iteration policy, workflow, tool order, replan or stop strategy | Declarative route inside current authority | Capability, external-effect approval, or success |
| `result` | DoD outcome and deliverable shape | Expected completion form | Evidence that this run already passed |
| `boundary` | Scope, exclusions, authority, safety, and budget constraints | Equal or narrower constraints | Broader permission or a safety override |
| `verification` | DoD evidence plan and automatic verifier selection | Expected checks and human-evidence points | Fabricated proof or universal correctness |
| `routing` | Ordered host handoff chain in the Behavior Contract | Atomic agent profiles with their bound skills, tools, and MCP servers | Installation, capability, action authority, reordering, substitution, partial invocation, or a lower Loop profile floor |

Treat remembered values as inputs to contract construction, not as the whole
contract. Add mandatory criteria from current specifications, repository
contracts, affected integrations, and risk. If those additions materially
change the requested endpoint, follow the normal authority process.

Examples:

- A remembered `action` pattern such as “write the failing test first” may
  select a TDD route after proposal confirmation. It cannot authorize edits
  when the current endpoint is Review.
- A remembered `verification` pattern such as “run unit, integration, and
  static checks” can populate required evidence. The checks must still be run
  freshly against the current state.
- A remembered BDD `action` pattern may require user-visible scenarios before
  implementation. The route is remembered; the current task's scenarios,
  expected outcomes, and evidence are not.
- A remembered `result` pattern such as “deliver the patch plus a concise risk
  note” defines output shape. It does not prove the patch works.
- A remembered `boundary` excluding schema changes remains useful, but a stored
  permission to deploy or delete would be invalid and unusable.
- A remembered `routing` chain is resolved in full against the authenticated
  host registry, authenticated skill-role/incompatibility metadata, and
  explicit agent-bound authority map after consumption.
  Every profile must pass before profile zero can activate. Loop preserves
  order and each atomic profile, activates at most one `primary` specialty per
  iteration, never treats a `controller` or `middleware` as that specialty,
  rejects incompatible pairs, and advances only at a committed boundary. One
  unavailable, incompatible, or disallowed component makes the remembered
  chain unusable; Loop never clips or repairs it silently. Bind the reducer
  cursor's admission hash, proposal reference,
  `PENDING | ACTIVE | COMPLETE | BLOCKED` status, profile index, active
  iteration, cursor and cumulative-budget revisions,
  chain/registry/authority hashes, and closed last event.
  Repeat only the active index after an authenticated committed non-success
  receipt; advance one index only after an authenticated `VERIFIED` completion
  and guard receipt bound to that exact admission, proposal, iteration,
  attempt, profile, commit identity, and budget consumption.
