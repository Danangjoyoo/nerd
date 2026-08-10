# Behavioral Memory in Task-Completion Loops

Use this reference only when the current user explicitly invokes Nerd Memory
for the current request. Installation, relevance, prior use, remembered
preferences, or another skill's mention never activates it. Without that
direct invocation, Nerd Loop remains memory-free and does not load or query
Nerd Memory. Once explicitly invoked, load Nerd Memory's own `SKILL.md` and
runtime contract before performing a memory operation; this reference defines
only the composition boundary.

Use [the Nerd Loop Runtime Contract](runtime-contract.md) as the normative
source for authority precedence, selected state, routing compilation, and
terminal behavior. Nerd Memory's own runtime contract remains authoritative
for proposal, confirmation, consumption, observation, and memory lifecycle.

## Contents

1. [Purpose](#purpose)
2. [Memory Planes](#memory-planes)
3. [Safety and Authority](#safety-and-authority)
4. [Admission Sequence](#admission-sequence)
5. [Behavior Contract](#behavior-contract)
6. [Mapping the Seven Pattern Types](#mapping-the-seven-pattern-types)
7. [Using Memory During Iteration](#using-memory-during-iteration)
8. [Revision and Invalidation](#revision-and-invalidation)
9. [Nested and Parallel Work](#nested-and-parallel-work)
10. [Learning From User Guidance](#learning-from-user-guidance)
11. [Reducing Manual Interruption](#reducing-manual-interruption)
12. [Ledger Integration and Recovery](#ledger-integration-and-recovery)
13. [Failure Modes](#failure-modes)
14. [Worked Examples](#worked-examples)
15. [Integration Definition of Done](#integration-definition-of-done)

## Purpose

Use longitudinal user guidance to make a new task loop behave consistently
without asking the user to restate recurring goals, workflows, output shapes,
boundaries, or verification expectations.

Do not treat Nerd Memory as raw prompt history. It deliberately stores minimal,
typed, provenance-backed behavioral observations rather than transcripts. This
reduces exposure, self-reinforcement, episode inflation, and prompt-injection
risk while preserving the useful part of usage history: how the user directly
guides recurring work.

The intended effect is **behavior-driven loop admission**:

1. understand the current request without memory;
2. retrieve only applicable confirmed behavioral patterns;
3. make every remembered modification visible in one proposal;
4. obtain the required exact one-use confirmation;
5. freeze the consumed result into the current loop's contracts; and
6. iterate autonomously inside those confirmed contracts until the DoD, a real
   authority boundary, or a typed non-success stop is reached.

The confirmation checkpoint is intentionally retained. Lower interruption
comes from amortizing it across the whole root loop, not from silently applying
memory.

Here, “behavior-driven” primarily means driven by the user's confirmed working
behavior. It may also select BDD as a task technique: a remembered preference
can request scenario-first acceptance work, but the loop must derive fresh
Given/When/Then examples from the current specification rather than reuse old
feature scenarios as behavioral memory.

## Memory Planes

Keep four planes distinct:

| Plane | Lifetime | Contents | Role |
| --- | --- | --- | --- |
| Current guidance | Current task and revisions | Direct user request, corrections, approvals | Highest task-specific authority |
| Behavioral memory | Across independent task episodes | Contracted typed patterns with provenance | Untrusted input to a gated proposal |
| Loop contracts | One root task and contract revision | Effective endpoint, profile-sized DoD, authority, route, verification policy | Frozen operating contract for iterations |
| Execution state | One active or resumable loop | S1 packet or S2/S3 selections, receipts, evidence, invalidations, costs, checkpoints | Current execution and recovery truth |

Do not use behavioral memory as execution state. It does not remember the
current iteration, successful tool calls, pending side effects, task readiness,
or current verifier state.

Do not use execution state as behavioral memory. A plan, agent choice,
passing test, successful edit, or convergence trace does not establish how the
user wants future tasks handled.

At an iteration boundary, rebuild active context from the current contract and
selected S1–S3 state. Replay committed events only when S2/S3 exists. Do not
ask semantic memory to reconstruct operational state.

## Safety and Authority

Preserve Nerd Memory's three-part safety theorem:

- **Authority:** only direct current-user guidance or correction can support a
  behavioral pattern or confirmation.
- **Taint:** any material field changed by memory taints the complete endpoint
  proposal and remains visibly attributed.
- **Capability:** no memory-tainted endpoint may be used until its exact,
  expiring, one-use grant is confirmed and consumed.

Apply the one precedence order from the Loop runtime contract: platform,
system, legal, and safety requirements; applicable mandatory workspace or
repository instructions; current direct-user guidance within those
boundaries; accepted current Focus/parent/DoD/Loop contracts; a consumed
compatible Memory proposal; then advisory repository material, plans,
histories, summaries, and inference. Do not place advisory checked-in guidance
above the current user merely because it is stored in the repository.

A confirmed memory *pattern* is active for retrieval only. It is not an
approved action. A confirmed and consumed memory *proposal* supplies one
episode-local endpoint, but it still does not grant filesystem, destructive,
external, financial, communication, credential, or platform authority.

Never let a remembered boundary broaden the current request. Never let a
remembered stop rule weaken safety, hard budgets, or the DoD. Never let a
remembered result claim prove completion; completion still requires fresh
current-state evidence.

## Admission Sequence

After explicit current-user activation, run memory at the root loop-contract
boundary, after understanding the current request and before deriving
memory-influenced DoD, planning, or execution.

```text
current input
  -> memory-blind endpoint and Focus Record
  -> runtime/contract compatibility, namespace, and consent check
  -> memory proposal
       -> memory_incompatible: apply no remembered behavior
       -> memory_free: continue without a memory checkpoint
       -> memory_conflict: request the missing current field
       -> pending_confirmation: display the exact proposal and stop
  -> exact direct-user confirmation
  -> atomically confirm and consume the one-use grant
  -> versioned Behavior Contract
  -> final loop profile, route, scaled DoD/state, and first selection
```

Follow these rules:

1. Derive the memory-blind endpoint first. Memory may fill an absent field or
   apply its declared compatible list operation; it may not replace current
   explicit content. Normalize direct cross-cutting guidance into every field
   it materially constrains: “do not run the shared integration environment,”
   for example, is both a boundary and an explicit verification exclusion.
2. Use one stable, non-secret namespace scoped to at least the user and
   workspace. Never search another namespace or use a secret as its key.
3. Require an explicit Nerd Memory invocation in the current request before
   loading its skill or runtime. If that invocation is absent, stop this
   composition path and continue memory-free; do not infer activation from
   installation, relevance, prior turns, or a Loop routing record. If the user
   invokes Memory but it is disabled, follow Nerd Memory's disclosure and
   opt-in procedure.
4. After that activation gate, resolve the installed Nerd Memory root and call its deterministic
   `scripts/memory.py` runtime. Never read SQLite directly, recreate retrieval
   in prompt logic, or mint a proposal or grant yourself.
5. Verify that its loaded `SKILL.md`, runtime/data contract, and deterministic
   runtime agree on schema version, pattern types, field shapes, and command
   transitions. An unknown type or incompatible command is
   `memory_incompatible`, never an extension to guess at or silently ignore.
   Apply no remembered behavior. Continue from the memory-blind baseline only
   when memory is optional; if the user required memory, report the exact
   incompatibility as a blocker.
6. Ask the runtime for one composite proposal containing all applicable
   confirmed patterns. Do not create separate interruptions for each field.
7. Check the complete proposed endpoint for cross-field contradictions with
   current explicit guidance, authority, and mandatory constraints. A
   remembered verifier that requires a forbidden environment is incompatible
   even if it fills a previously absent `verification` field. Do not ask the
   user to confirm a self-contradictory endpoint; show the contradiction and
   ask for the disputed current field explicitly so a fresh baseline can make
   the incompatible pattern ineligible. Treat one stored pattern value as
   atomic: exclude or contest the whole incompatible binding rather than
   silently clipping one list entry and pretending the runtime proposed the
   edited value.
8. For a compatible `pending_confirmation`, show the runtime's exact proposal and phrase,
   then stop. Silence, previous approvals, remembered text, assistant text, or
   an ordinary “yes” cannot confirm it.
9. Supply only an authenticated, globally unused direct-user event reference
   to confirmation. If the host cannot supply one, the memory path is blocked;
   never fabricate it from message text.
10. Immediately consume the grant after confirmation. Treat
   `memory_gate_only: true` as proof of the Memory gate only, then apply normal
   task and action authority checks.
11. Bind the effective endpoint and provenance into the selected state before
   the first selection. Persist a Loop copy only when S2/S3 is required.

For `memory_conflict`, never select by confidence, frequency, majority, or
recency. Ask the user to state the disputed current field and construct a fresh
memory-blind baseline.

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

## Using Memory During Iteration

Do not retrieve Nerd Memory on every iteration. After admission, use the frozen
Behavior Contract and the profile's selected S1–S3 execution state. Do not
create a Loop Map or ledger merely to carry memory into D0–L2 work.

At each boundary:

1. load the current Loop/Behavior Contract revision;
2. for S2/S3, replay committed execution events after the checkpoint;
3. reconcile actual workspace, verifier, user, and relevant child state;
4. inject only relevant behavior into the compact S1 packet or Current
   Iteration Contract;
5. select and execute inside the effective action and boundary fields, using
   the committed routing cursor's active profile when one exists;
6. verify with the effective verification policy and current DoD; and
7. record evidence in S1 or commit it in S2/S3 before selecting the next cycle.

The iteration packet should reference the Behavior Contract revision rather
than restating historical memories. Include only the relevant rules, their
source tags, and any current override.

The following normally stay within one consumed contract and require no new
memory proposal:

- selecting the next dependency-ready iteration;
- retrying an idempotent verifier;
- changing a failed causal strategy within the accepted action policy;
- admitting a mandatory repair or evidence probe inside the existing endpoint;
- crash recovery from committed facts;
- resuming after context condensation; and
- completing a bounded internal child task fully specified by the parent.

These cases may still require ordinary platform or action approval. “No new
memory proposal” does not mean “unconditionally authorized.”

## Revision and Invalidation

Rebuild the memory-blind baseline when a material field changes. A material
change includes the goal, task endpoint, action policy, result shape, boundary,
verification contract, ordered routing chain, stable applicability scope, or
independent root task.

Use this decision rule:

- If the user explicitly supplies the changed field, use it directly and
  record its source as `current_explicit`; memory may not override it.
- If the changed field remains absent and memory could fill it, create a fresh
  proposal and require a fresh confirmation before using the remembered value.
- If the change is only execution state inside the accepted contract, update
  the Loop Map or ledger without querying memory.

On direct correction:

1. stop before another affected mutation;
2. version the Loop/Behavior Contract;
3. mark contradicted confirmed patterns contested through Nerd Memory;
4. invalidate uncommitted decisions and stale evidence derived from the old
   field;
5. preserve independent verified evidence; and
6. replan from the corrected contract.

A task-local difference is not automatically a durable correction. Record
`user_correction` only when the user explicitly changes or retracts recurring
guidance.

If a linked pattern is forgotten, superseded, or contested during a live task,
never use it to form new uncommitted behavior. Preserve completed execution
facts, rebaseline affected future work, and ask only when the user's desired
current-task behavior is genuinely ambiguous.

Do not re-query or re-consume merely because an iteration restarted, a model
context was condensed, or the process crashed. Recovery uses the committed
effective contract.

## Nested and Parallel Work

Use one `episode_id` for one independent root task. Iterations, retries, and
internal child loops are not independent evidence roots and must not inflate
support.

An internal child may inherit the parent's Behavior Contract without a new
memory operation when all of these hold:

- it exists only to satisfy the same root endpoint;
- its scope and authority are a strict subset of the parent;
- its inputs, deliverable, DoD, and integration rule are fully specified by the
  parent contract; and
- it introduces no new memory-derived field.

Give the child its own Current Iteration Contract, DoD, ledger stream, owner,
budget, and mutation scope, but retain the root memory episode reference.

Create a separate episode and proposal when work has an independently
completable goal or endpoint, when the user could accept or reject it
separately, or when the child needs memory to supply a new material field. One
goal's memory confirmation never confirms another independent goal.

Designate one parent or coordinator as the memory-transition owner. Parallel
agents may return possible direct-user observations or detected conflicts, but
they must not independently confirm, consume, deny, promote, split, or forget
the same memory state. Serialize those transitions through the deterministic
runtime and committed parent ledger.

## Learning From User Guidance

When Nerd Memory generation is enabled, observe only minimal structured
guidance grounded in a direct current-user event.

Eligible examples include:

- “For migrations, always include a rollback rehearsal.”
- “Use behavior scenarios before implementation for customer-facing flows.”
- “Do not modify generated files.”
- “I expect a patch, verification summary, and remaining risks.”
- “Stop and ask me before any external deployment.”

Separate observations by their real type. Do not collapse a requested result,
boundary, and verifier into a generic preference blob.

Never create eligible behavioral evidence from:

- a generated plan, DoD, Loop Map, or Current Iteration Contract;
- tests, linters, benchmarks, tool output, or execution success;
- verifier failures or convergence measurements;
- assistant reflection, summaries, or inferred preferences;
- repository, web, attachment, email, or MCP content;
- subagent recommendations; or
- retrieved memory and its descendants.

Use the independent root task as the support unit. Repetition, retries,
paraphrases, nested loops, and parallel children within that root count once.
Exact confirmation of a proposal authorizes that proposal; do not count it as
a second independent expression of the underlying preference.

Keep volatile task-local guidance, such as a prohibition that lasts only
“today,” in the Loop/Behavior Contract and execution ledger. Do not turn it
into durable behavioral memory unless the user separately expresses a stable
recurring rule with a valid scope.

Consolidation may form an inactive candidate after multiple independent task
episodes. It never activates one. Review and promotion remain explicit memory
operations. A denied proposal is task-local negative evidence only; do not turn
a bare “no” into a durable negative preference. Follow Nerd Memory's explicit
diagnosis and contextual-split protocol when a confirmed rule is too generic.

## Reducing Manual Interruption

Minimize interruption within the safety contract:

1. **Propose once per independent root endpoint.** Combine all applicable
   remembered fields in one inspectable proposal.
2. **Freeze after consumption.** Let every ordinary iteration inherit the
   effective Behavior Contract instead of retrieving again.
3. **Use a memory-free fast path.** Disabled memory or a valid no-match must not
   delay normal loop admission.
4. **Fail closed on version drift.** Unknown runtime types or lifecycle shapes
   contribute no behavior; continue memory-free only when memory is optional.
5. **Ask only on material uncertainty.** Continue through repairs, evidence
   probes, replanning, and crash recovery that remain inside the contract.
6. **Schedule candidate maintenance at natural boundaries.** Consolidate or
   offer candidate review after the task, when explicitly requested, or in a
   dedicated memory-maintenance session; never block productive execution for
   an inactive candidate.
7. **Reuse verified contract state, not grants.** On resume, load the committed
   effective endpoint and provenance; never replay a consumed token.
8. **Surface conflicts together.** Present the disputed fields and evidence in
   one checkpoint instead of asking serial vague questions.

Unavoidable checkpoints remain:

- first use or enablement when explicit opt-in is missing;
- every material memory-influenced proposal;
- an unresolved memory conflict;
- a material endpoint, DoD, boundary, verifier, or authority change;
- candidate promotion, contextual split, correction, or forgetting;
- human-only DoD evidence; and
- ordinary external, destructive, financial, communication, credential, or
  platform approval.

There is no standing-confirmation bypass in Nerd Memory. Removing the initial
per-task memory proposal would be a different memory architecture and threat
model, not a Loop optimization.

## Ledger Integration and Recovery

Apply this section only when the selected profile requires S2/S3. S0/S1 keeps
no duplicate durable Loop ledger; Nerd Memory still persists its own proposal
state under its independent contract.

Record memory-to-loop transitions as factual events, for example:

```text
MEMORY_BASELINE_COMMITTED
MEMORY_PROPOSAL_PENDING
MEMORY_CONFLICT_OBSERVED
MEMORY_PROPOSAL_CONSUMED
BEHAVIOR_CONTRACT_BOUND
BEHAVIOR_CONTRACT_REVISED
USER_GUIDANCE_OBSERVED
MEMORY_BINDING_STALE
ROUTING_BOUND
ROUTING_PROFILE_ACTIVATED
ROUTING_PROFILE_REPEATED
ROUTING_PROFILE_SATISFIED
ROUTING_COMPLETED
ROUTING_BLOCKED
```

Recommended event payloads contain stable IDs and hashes, never secrets:

```yaml
event_type: BEHAVIOR_CONTRACT_BOUND
root_episode_id: episode-...
loop_id: loop-...
loop_contract_revision: 3
proposal_id: proposal-...
proposal_hash: sha256:...
endpoint_hash: sha256:...
pattern_revisions:
  - pattern_id: pattern-...
    revision: 4
context_hash: sha256:...
consumed_at: 2026-08-10T00:00:00Z
```

Do not record:

- plaintext grant tokens;
- reusable confirmation or denial references;
- raw prompts or transcripts;
- pattern evidence text copied from Nerd Memory;
- secrets or sensitive values; or
- a false `memory_confirmed` event before atomic consumption succeeds.

Crash recovery rules:

- A committed `BEHAVIOR_CONTRACT_BOUND` plus its canonical effective endpoint
  is sufficient to resume the task contract.
- A committed routing cursor resumes the same chain/profile index after its
  proposal reference, chain/registry/authority hashes, expected revision,
  bounds, status/active-iteration/last-event coherence, and full remaining
  chain preflight pass. Validate that the event/index/revision tuple is
  reachable from the initial bound cursor; a syntactically valid cursor cannot
  skip earlier profiles. Never infer advancement from an agent message or
  uncommitted attempt; reconcile an ambiguous effect before repeat. Advance
  only from an authenticated receipt bound to the exact proposal, active
  iteration, profile/index/hash, `VERIFIED` outcome, declared guard evidence,
  and hash of the matching committed iteration reference/event/revision.
- A pending proposal remains a human checkpoint; do not synthesize its phrase
  or assume it was accepted.
- A confirmed-but-unconsumed proposal must be reconciled through Nerd Memory;
  never guess whether its grant was used.
- A consumed grant is not reusable. Resume from the loop contract rather than
  calling `consume` again.
- If the loop ledger and memory runtime disagree, stop the affected path,
  inspect both committed records, and prefer no memory influence until the
  inconsistency is resolved.

## Failure Modes

Avoid these designs:

- **Retrieve every iteration:** creates repeated interruptions, context drift,
  and false independent evidence.
- **Transcript memory:** stores excess sensitive and adversarial content while
  blurring direct guidance with external text.
- **Memory as permission:** turns a prior preference into present action
  authority.
- **Memory as proof:** treats a remembered result or passing historical test as
  evidence that the current DoD passed.
- **Self-reinforcement:** converts the loop's own plan, success, or reflection
  into a stronger user preference.
- **Episode inflation:** counts retries, child loops, summaries, or parallel
  agents as independent user support.
- **Silent nearest match:** forces a behavioral route despite scope mismatch or
  no exact trigger.
- **Auto-promotion:** lets frequency activate an inert candidate.
- **Grant persistence:** stores or replays the one-use token during recovery.
- **Cross-workspace fallback:** leaks one project's behavior into another.
- **Agent-majority conflict resolution:** lets several agents vote away an
  authoritative disagreement.
- **Valid-prefix routing:** activates profile zero before proving every later
  profile exists and is allowed, causing a partial remembered route.
- **Boolean route completion:** advances a routing cursor from caller assertions
  instead of an authenticated proposal/profile/iteration/guard receipt whose
  hashed commit identity comes from the bound effect journal.
- **Blind cross-field composition:** accepts a remembered action or verifier
  that contradicts a current boundary merely because it populates another
  endpoint field.
- **Schema guessing:** silently maps or drops a runtime pattern type that is
  absent from the loaded Nerd Memory contract.
- **Memory-maintenance detour:** interrupts an active task to review candidates
  that have no bearing on its current endpoint.

## Worked Examples

### Recalled TDD and verification behavior

The current request says “repair this parser” and does not specify a workflow
or evidence. Confirmed patterns propose:

- `action`: reproduce the failure, write a failing regression test, repair,
  then refactor;
- `result`: a minimal patch with a concise risk note; and
- `verification`: focused test, affected suite, and static checks.

Nerd Loop displays one composite proposal. After exact confirmation and
consumption, it compiles the fields into the DoD, Loop Map, and iteration
policy. Subsequent reproduce, test, repair, and verification iterations do not
query memory again. Passing tests enter the execution ledger as current-task
evidence; they do not reinforce the remembered preferences.

### Current guidance overrides history

The current request says “review only; do not edit or run the integration
environment.” A stored action pattern prefers test-first repair. The explicit
Review endpoint and boundaries win. Memory cannot transform the task into
Execute, append mutation steps, or broaden verification authority. It may
propose only compatible absent fields.

### Crash after memory consumption

The loop committed a Behavior Contract, selected an iteration, and then the
process crashed. On resume, the agent loads the effective endpoint and memory
provenance from the loop contract and ledger. It reconciles the in-flight
action and continues without another memory proposal. It does not consume the
grant again.

### Independent second goal

A request contains “repair the parser” and “design a new deployment policy.”
These are independently completable endpoints. Create separate root episodes
and memory proposals. Confirmation for the parser workflow cannot establish
the policy-design behavior.

## Integration Definition of Done

Nerd Loop and Nerd Memory are correctly composed only when all of these hold:

- a memory-blind endpoint exists before retrieval;
- the runtime and loaded memory contract agree before any pattern influences
  the loop;
- disabled and no-match memory take a non-blocking fast path;
- every memory-derived material field stops at one exact proposal gate;
- incompatible cross-field effects are resolved before proposal confirmation;
- the runtime contract's canonical authority order is preserved, including the
  distinction between mandatory and advisory checked-in material;
- one consumed proposal initializes one versioned root Behavior Contract;
- ordinary iterations and crash recovery do not re-query or re-consume memory;
- independent goals have separate episodes, while retries and internal child
  loops do not inflate support;
- all seven pattern types compile to the correct loop concerns without becoming
  authority or completion proof;
- routing profiles remain ordered and atomic, every profile passes full-chain
  preflight against the current authenticated registry and explicit
  agent-bound authority map before activation, cursor state is coherent, and
  advancement requires an authenticated guard receipt without lowering a
  profile floor;
- automatic verification always uses fresh current-state evidence;
- only minimal direct-user guidance or correction becomes eligible memory
  evidence;
- plans, results, tests, summaries, and agent output cannot self-reinforce;
- memory provenance, not tokens or transcripts, is bound to selected Loop
  state and committed only for S2/S3;
- concurrent memory transitions have one coordinator and deterministic runtime
  serialization; and
- material contract changes, conflicts, promotion, splitting, and forgetting
  retain their required human checkpoints.
