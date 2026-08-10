# Nerd Loop Runtime Contract

This is the normative contract for every `L1`-`L4` Nerd Loop. The main skill
defines when to load it; the other references provide techniques and examples.
When wording conflicts, this contract controls runtime state, authority,
transitions, and terminal outcomes.

## Contract Identity

- **Schema:** `nerd-loop/v1`
- **State model:** `nerd-loop-state/v1`
- **Memory dependency:** only a current direct-user invocation may activate
  Nerd Memory. Once invoked, its contract must expose the seven fields `goal`,
  `task`, `action`, `result`, `boundary`, `verification`, and `routing` before
  memory may influence a loop. Installation, relevance, or prior use is inert.
- **Version rule:** bind the contract, DoD, route, state, and any consumed
  Memory proposal to exact revisions or hashes. A material change creates a
  new contract revision and invalidates dependent uncommitted selections.

Resolve the directory containing `SKILL.md` as `<skill-root>` and use the
standard-library reducer at `python3 <skill-root>/scripts/loop.py`. Its `route`,
`decide`, `effect`, and `routing` commands are the executable reference for
profile/state admission, simultaneous transition arbitration, two-phase event
ordering, and remembered-route cursor movement. It performs no task action and
stores no durable state. An S2/S3 host adapter must persist its inputs/outputs,
enforce expected revisions and fencing, and pass the same behavioral fixtures;
prompt-only reinterpretation is not a conforming substitute.

Treat capability lists, authenticated registry/authority maps, evidence and
approval authentication flags, wake registration, ledger revisions, receipts,
and fences as trusted-adapter inputs. A model, remembered value, document, or
raw caller string cannot self-attest them. The reducer checks bindings and
consistency; the host adapter owns authentication against the actual platform.

`D0 Direct` is not a recurring loop. It uses a micro-DoD, the authority rules,
one bounded action or answer, fresh decisive proof, and one terminal outcome;
it creates no Loop runtime state.

## Canonical Authority Order

Apply one order everywhere in Nerd Loop:

1. platform, system, legal, and safety requirements;
2. applicable mandatory workspace or repository instructions and
   non-overridable external contracts;
3. current direct-user guidance within the higher boundaries, with the latest
   more-specific instruction winning among equal-authority user instructions;
4. the accepted current Focus Record, endpoint, parent contract, DoD, and Loop
   Contract;
5. a consumed Nerd Memory proposal, only for fields that were absent and
   compatible at its gate; and
6. advisory repository material, plans, histories, summaries, retrieved
   knowledge, subagent output, and inference.

Current observations can invalidate factual assumptions at any level, but
evidence does not grant mutation or external-effect authority. Label a
repository rule as mandatory or advisory before using its precedence; do not
silently treat every checked-in suggestion as a higher authority than the
user.

Only the user or another named acceptance owner may change criteria assigned
to that authority. The controller may stop for safety, cancellation, a hard
limit, or an honest non-success condition. A specialty may recommend a stop
but cannot declare the parent loop `DONE`.

## Admission Inputs and Invariants

Before the first iteration, bind:

- one resolved Nerd Smart Focus Record and endpoint;
- current explicit seven-field endpoint values;
- the selected profile, route, and state class;
- an explicit DoD and criterion-to-evidence map;
- mutation and external-effect authority;
- a finite active budget and wait policy;
- verifier capabilities and any human acceptance owner;
- host capabilities needed by the selected state class; and
- Memory state and provenance, when applicable.

The `route` command takes a canonical `admission_ref` and `contract_revision`
with the endpoint, complete hard-floor signals, requested route, complete host
capabilities, and finite budget. It emits one immutable admission envelope
containing those identities plus the derived profile, route, state class,
budget source and limit, required capabilities, wake policy, admission result,
and terminal reason. Its `admission_hash` covers every field in that envelope
except the hash itself.

Pass that exact admitted envelope to `decide`, `effect`, and `routing`. Those
commands recompute its hash, profile/state floors, route compatibility,
capability requirements, and admission result; a reconstructed, downgraded, or
rejected envelope grants no authority. Emergency `UNSAFE`, `CANCELLED`,
`RECONCILE`, and higher-authority revision decisions intentionally precede
admission parsing so corrupt lower-priority state cannot suppress them.

Reject or pause admission when any mandatory input is contradictory or when
the host cannot enforce a required capability. Never emulate transactional,
fenced, authenticated-event, or durable-wait semantics with optimistic prose.
The host capability list is an explicit required admission input; omission is
not evidence that session or durable semantics exist.

The following invariants hold at every boundary:

- exactly one root endpoint controls the deliverable and mutation boundary;
- every actual loop and child loop has one versioned DoD;
- exactly one primary focus is active per loop;
- a mutation or effect belongs to one recorded iteration and attempt;
- `PASS` requires fresh evidence from the selected verifier;
- the latest state and best verified state are distinct when regression is
  possible; and
- `DONE` is reachable only through the DoD decision.

## Deterministic Profile Floors

Evaluate the predicates below and select the highest required floor. A true
higher-floor predicate cannot be averaged away or overridden by a route label.

| Floor | Any sufficient predicate |
| --- | --- |
| `D0` | No useful back edge; no unresolved material uncertainty; one bounded action or answer has immediate decisive proof; no resumability, child, shared claim, or ambiguous external effect is needed |
| `L1` | More than one read-only probe may be selected; bounded search, review, triage, diagnosis, option screening, draft validation, or evidence gathering can adapt without workspace mutation |
| `L2` | A single owner may mutate local state and use immediate deterministic feedback; a local controlled experiment or correction back edge is useful |
| `L3` | Work needs managed recovery of in-flight work, a durable or formal human wait, CI/review, an external receipt, an independently verifiable child, shared-resource ownership, or recovery across a coordination/process boundary |
| `L4` | Coupled contracts or workstreams can co-evolve; consequential multi-writer effects, high-impact, high-consequence, or hard-to-reverse operations, staged rollout, or materially ambiguous/noisy success requires governance |

An immediate clarification or acceptance response in the current interaction
does not alone force `L3`. A human gate forces `L3` when its wait, decision,
provenance, or resume state must be durable or formally auditable.

Tie breaking is deterministic: keep the highest floor, choose the endpoint's
named default route, then choose the lexicographically first compatible route
identifier only if several templates remain genuinely equivalent. Record why
the selected route is compatible.

`direct` is valid only when the resulting profile remains D0; a caller cannot
attach durable or iterative signals and keep a no-loop route. At Execute, L3
managed recovery alone retains `piv`; only a CI/review lifecycle defaults to
`pr_delivery`. Explore remains non-mutating and cannot select `experiment`.
The `pr_delivery` and durable `monitor` routes require authenticated wake-event
capability from their own semantics even when a caller omits the matching
signal; signal duplication is never a way to bypass a route requirement.

Profile and state are separate maxima. Ordinary L3 and single-owner L4 use S2;
an authorized lower-tier durable checkpoint may also raise only to S2. Shared
resource ownership or consequential multi-writer effects require S3. Do not
charge every complex but single-owner loop for fencing it does not need.
`effect_reconciliation` is an S3 requirement and is also required by an
external-receipt or staged-rollout signal and by `pr_delivery`; an ordinary S2
checkpoint does not pay for it. Durable `pr_delivery` and `monitor` admission
also derive authenticated wake requirements from route semantics.

## Closed Runtime Vocabularies

Never use one vocabulary as another. Store values under typed fields such as
`criterion.status`, `trace.dynamics`, `work.status`, `loop.phase`, and
`terminal.outcome`; overlapping words in different fields never imply a state
transition. Extensions require a schema revision.

### Criterion status

`PASS | FAIL | UNKNOWN | ERROR`

- `UNKNOWN` means the property is not adequately observed.
- `ERROR` means the verifier did not produce a trustworthy decision.
- Neither can be coerced into `PASS`.

### Dynamic diagnosis

`NOT_ASSESSED | PROGRESSING | LEARNING | SETTLING | PLATEAUED |
PREMATURELY_CONVERGED | STUCK | OSCILLATING | DIVERGING | INCONCLUSIVE |
FALSE_CONVERGENCE`

Dynamics describe the trace, never the terminal result. `NOT_ASSESSED` is the
default when there are too few comparable observations or the label cannot
change the next decision.

### Work-node status

`PROPOSED | PLANNED | READY | CLAIMED | ACTIVE | VERIFYING | VERIFIED |
WAITING | BLOCKED | SUPERSEDED | CANCELLED`

These statuses belong to plan nodes. A `VERIFIED` child or node does not imply
that its parent loop is done.

### Loop phase

`ADMITTING | READY | ACTIVE | VERIFYING | PAUSED | RECONCILING | TERMINAL`

`PAUSED` is a loop phase; `WAITING` is a work-node status. Waiting consumes no
active iteration budget. Resume enters `RECONCILING`, never directly `ACTIVE`.

### Terminal outcome

`DONE | BLOCKED | CANCELLED | UNSAFE | IMPOSSIBLE | FAILED | EXHAUSTED |
STOPPED | HANDOFF`

- `DONE`: every mandatory DoD and integration criterion is `PASS` on the
  current state with fresh required approval.
- `BLOCKED`: a named missing dependency, access, information item, or decision
  prevents an authorized next step.
- `CANCELLED`: the user or higher authority ended the task.
- `UNSAFE`: the remaining path violates a higher authority or unacceptable
  safety boundary.
- `IMPOSSIBLE`: evidence establishes that no route in the authorized action
  space can satisfy the DoD.
- `FAILED`: an unrecoverable execution or verification failure occurred and no
  authorized repair remains.
- `EXHAUSTED`: a hard active budget ended before the DoD passed.
- `STOPPED`: the DoD is unmet, no stronger terminal condition applies, and the
  controller has no authorized proportionate next cycle. Bind exactly one
  reason: `NO_POSITIVE_VALUE | PLATEAU | INCONCLUSIVE_TRACE | NO_READY_WORK`.
- `HANDOFF`: an authorized recipient accepted a versioned continuation packet;
  this transfers responsibility and is not success.

`BLOCKED`, `CANCELLED`, `UNSAFE`, `IMPOSSIBLE`, `FAILED`, `EXHAUSTED`,
`STOPPED`, and `HANDOFF` are honest non-success outcomes.

## DoD and Verifier Decision

For each mandatory criterion bind its ID, source, required state, scope,
verifier, pass rule, freshness rule, approval requirement, and acceptance
owner. Freeze the sorted complete mandatory criterion and integration ID sets,
then hash that immutable definition with its DoD revision. A decision request
must carry the accepted hash and current artifact revision; omission of even
one mandatory ID or a changed definition invalidates the request.

Evidence is a typed host-authenticated record bound to the criterion ID, exact
accepted DoD hash and revision, current artifact revision, selected verifier,
and its observed `PASS | FAIL | UNKNOWN | ERROR` verdict. Criterion status is a
checked projection of that authenticated verdict: without evidence it must be
`UNKNOWN`, and a disagreeing caller-supplied status is invalid. A named
approval is a separate authenticated event bound to the same exact DoD hash,
criterion/revisions, artifact revision, acceptance owner, and an explicit
`APPROVED | REJECTED` decision. Presence alone is not approval. An arbitrary
nonempty string, stale artifact proof, wrong verifier, wrong owner, changed
pass rule, or caller-supplied `PASS` assertion is not evidence.
Select the lowest-cost verifier that directly observes the claim. A proxy-only
verifier must be paired with complementary evidence or leave the criterion
`UNKNOWN`.

After the last material change, rerun every affected mandatory verifier and
the parent integration checks. Calculate completion only as:

```text
done = all mandatory criteria are PASS
       and every status equals its authenticated evidence verdict
       and every PASS has authenticated evidence bound to the exact accepted DoD hash
       and all required evidence targets the current artifact revision
       and every required integration criterion is PASS
       and every required approval is authenticated, owner-bound, and APPROVED
```

Plan completion, agent agreement, a stable artifact, a passed proxy, lack of
new findings, and budget exhaustion cannot change this expression.

When a deterministic criterion lacks a user threshold, use the exact
specification or mandatory contract. When a noisy or subjective mandatory
criterion lacks a defensible threshold or acceptance owner, keep it `UNKNOWN`
and request the missing authority; never invent a passing threshold.

## Budget and Convergence Defaults

Every recurring loop has a finite active envelope covering the applicable
dimensions: active iterations, tool/model calls, tokens, wall time, monetary
cost, external effects, and risk exposure. Use an explicit user budget first,
then a stricter mandatory or host budget. If neither exposes a finite active
limit, admit one iteration only; after committing it, return `EXHAUSTED` if the
DoD remains unmet. Waiting time is governed by a wake condition and deadline,
not charged as active iteration work.

Admission creates one authenticated cumulative `budget_state`, bound by
`admission_hash`, with the initial active-iteration limit, an ordered collection
of authenticated committed-iteration consumption records, a revision equal to
the consumption count, and a hash over that identity. A command derives
remaining budget from this state; it never accepts a free-standing
`budget_remaining`. Every `ITERATION_COMMITTED` consumes exactly one unit and
emits the next authenticated budget state bound to its iteration, attempt,
commit reference/hash, and consumption reference. Decision, effect, recovery,
and remembered routing reject a stale, skipped, reset, or cross-admission
budget revision.

Do not create universal exchange rates between cost dimensions. Apply hard
floors and limits first, then compare eligible actions lexicographically by:
mandatory-gap impact, information value, risk, reversibility, active cost, and
stable work ID. Use normalized weighted cost only when the user or host
supplies the weights.

Do not diagnose convergence without comparable evidence. D0/L1 normally use
criterion status, residual uncertainty, and the budget only. L2 may use a
compact progress or repeated-failure rule. L3/L4 must declare thresholds,
noise handling, patience, best-state recovery, and responses when dynamics can
change control. Without calibrated thresholds, use `NOT_ASSESSED` and let the
DoD, distinct causal evidence, or hard budget decide.

Every non-`NOT_ASSESSED` dynamic diagnosis carries a reference to its valid
comparable evidence window; reject a label with no such window. Every
continue/stop value decision likewise records the evidence for whether a
proportionate positive-value action exists. Supply the sorted unique ready work
IDs, not only a caller-computed count, so selection is reproducible. A
registered wake condition plus deadline is a viable event-driven transition
even when no active action currently has positive value.

## Iteration and Two-Phase Effect Protocol

One iteration is one bounded, evidence-producing state transition. Scale its
representation:

- `S1`: record a compact current focus, boundary, expected evidence, verifier,
  and exit rule in the session before local action; record outcome and evidence
  before choosing another focus.
- `S2`: persist a versioned single-writer iteration and causal event stream.
- `S3`: add expected revisions, transactional append, resource ownership,
  leases where needed, and fencing epochs enforced by the ledger and affected
  resources.

For `S2`/`S3`, use two commit phases around effects:

1. **Intent commit:** atomically persist one `INTENT_COMMITTED` event containing
   the selection and action intent: event/commit/iteration/attempt/focus IDs,
   expected ledger revision, contract/plan/base revisions, owner and epoch,
   resource scope, stable operation and idempotency keys, expected result,
   verifier, abort rule, common admission hash, current budget revision,
   `ITERATION | LOOP` DoD scope, the exact accepted DoD contract (definition
   hash, DoD revision, intended artifact revision, and complete mandatory
   sets), an optional exact routing proposal/chain/profile binding, and the S3
   fence token. The single event prevents a crash-visible half-selected intent.
2. **Execute:** perform the action outside the ledger transaction.
3. **Outcome commit:** persist exactly one `ACTION_OBSERVED` result—receipt,
   failure, or `OUTCOME_UNKNOWN`—bound to the same iteration, attempt,
   operation, idempotency key, expected revision, and fence. It references the
   observation, costs, invalidations, discoveries, best-state effect, and
   ownership disposition. `VERIFICATION_RECORDED` then binds authenticated
   criterion and integration evidence to the resolved observation by carrying
   a complete DoD result whose immutable definition hash, DoD revision, and
   artifact revision exactly match the intent. Its declared completion verdict
   must equal the result derived from those records. `ITERATION_COMMITTED`
   references that verification event; `VERIFIED` is accepted if and only if
   the action has an applied receipt and that bound DoD verdict passes. The
   commit carries authenticated one-unit budget consumption and the reducer
   emits both the next cumulative budget state and a hashed iteration-commit
   identity for any routing receipt. Exactly one cause-labelled successor,
   authenticated registered pause, handoff, `LOOP_DONE`, or
   `LOOP_TERMINATED` edge follows; optional context condensation comes only
   afterward. A passing loop-scoped DoD must choose `LOOP_DONE`, whose
   authenticated terminal receipt binds the admission, iteration commit, next
   budget state, exact DoD hash/revision, and artifact revision. A typed
   non-success receipt is required for `LOOP_TERMINATED`.

Never require a receipt before its action. Never execute an uncommitted
external intent. If acknowledgement is ambiguous, reconcile with the same
iteration, attempt, operation, idempotency key, and fence before retrying; do
not mint a new attempt for a possibly completed non-idempotent effect.
`NOT_APPLIED` permits retry with those same identities, while `APPLIED` or
`FAILED` becomes the resolved observation. Every event carries the next
expected revision. Exact duplicate event IDs with byte-equivalent canonical
payloads are idempotent; the same ID with different payload, a stale revision,
changed fence, mismatched receipt identity, or successor before commit is
invalid.

The reducer validates this journal projection and reports the revision that
must already be committed before a host performs the next directive. It cannot
prove storage durability by itself. An S2/S3 adapter still needs integration
tests showing atomic append/CAS, crash recovery at every boundary, and actual
resource fencing; without them the host must fail admission closed.

## Transition Priority

At every boundary, apply the first matching rule:

1. stop unauthorized or unsafe work; record `UNSAFE` when a terminal record is
   safe to write;
2. honor an authoritative cancellation as `CANCELLED`;
3. reconcile an ambiguous effect, stale owner, or contract/schema mismatch;
4. apply current user or higher-authority revisions, version contracts, and
   invalidate affected selections/evidence;
5. validate verifier integrity and update criterion evidence;
6. if the completion expression passes, return `DONE`;
7. apply an already-reached hard terminal condition as `BLOCKED`, `IMPOSSIBLE`,
   `FAILED`, `EXHAUSTED`, or an accepted `HANDOFF`;
8. derive the ready set; when it is empty and a registered wake condition and
   deadline exist, enter `PAUSED` without requiring an active positive-value
   action;
9. diagnose dynamics only when its declared comparable evidence window is
   valid, then repair, reframe, roll back, change strategy, or return `STOPPED`
   with its exact reason when no authorized proportionate next cycle exists;
10. select the lexicographically first eligible ready focus, otherwise return
    the precise evidence-bound non-success outcome.

The later hard-terminal union cannot encode `UNSAFE` or `CANCELLED`; those use
only their dedicated higher-priority inputs. A pause requires a registered
condition and deadline. Route admission must already have proved the state and
authenticated-wake capabilities needed to preserve it.

This order is the only terminal decision function. References may describe
signals and techniques but must not define an alternative priority.

Validate payloads in the same stages. Always reject an unknown top-level field
or wrong schema, then parse only through the first matching priority stage.
Malformed same-stage or higher-priority data fails closed; malformed
lower-priority admission, DoD, budget, wake, value, or dynamics data cannot
suppress a valid earlier transition. Thus safety and cancellation do not
depend on a parseable plan, while `DONE` still requires the entire DoD contract
and budget exhaustion still requires the authenticated admission and budget.

## Nerd Memory Routing Compilation

Build the memory-blind baseline with all seven endpoint fields. After exact
proposal confirmation and one-use consumption, bind the complete effective
endpoint and pattern revisions into the Behavior Contract.

Compile `routing` as an ordered chain of atomic profiles. For each profile:

- preserve the exact agent-to-skills/tools/MCP binding and chain order;
- resolve every identifier in **every profile** against both the current
  authenticated host registry and an explicit agent-bound allowed-authority
  map before profile zero may activate; a valid prefix cannot admit an invalid
  or unauthorized suffix;
- record the registry snapshot or resolution provenance in selected `S1`
  state, and durably for `S2`/`S3`;
- require authenticated registry metadata for every registered skill, with a
  closed `primary | modifier | middleware | controller` role and a canonical
  incompatibility set. A route profile may activate at most one primary
  specialty; controllers and middleware are control-plane components rather
  than specialties, and any selected incompatible pair fails admission;
- advance the chain only at a committed boundary; and
- fail closed on a missing, renamed, disallowed, incompatible, or ambiguous
  component—never drop, substitute, reorder, install, or partially invoke it.

Bind this cursor to the consumed proposal plus chain, registry, and authority
hashes:

```text
routing.proposal_ref
routing.admission_hash
routing.status = PENDING | ACTIVE | COMPLETE | BLOCKED
routing.profile_index
routing.chain_size
routing.active_iteration_id
routing.revision
routing.budget_revision
routing.last_event
routing.chain_hash
routing.registry_hash
routing.authority_hash
```

Start at index zero in `PENDING`. `ROUTING_PROFILE_ACTIVATED` binds that index
to one iteration. A committed failed attempt may emit
`ROUTING_PROFILE_REPEATED` with a new iteration ID while retaining the same
index. Advance exactly one index only after the active iteration's outcome is
committed and an authenticated completion receipt binds the exact admission,
proposal, chain, profile index and hash, iteration and attempt IDs, `VERIFIED`
outcome, nonempty guard evidence, budget consumption/revision, and the hashed
identity of the corresponding `ITERATION_COMMITTED` event (commit reference,
event ID, and committed revision), emitting
`ROUTING_PROFILE_SATISFIED`; never skip or reorder. A repeat similarly requires
an authenticated non-success outcome receipt bound to that proposal, active
iteration, same profile, and its hashed committed-iteration identity. A receipt
from another proposal or iteration commit is invalid even when its chain and
profile happen to match. The last satisfied profile emits
`ROUTING_COMPLETED`. Registry or authority mismatch emits `ROUTING_BLOCKED`.

On recovery, validate the schema, admission hash, chain hash, registry hash,
cursor and budget revisions, authority hash, proposal reference, chain size,
current profile bounds, and the
coherence of status, active iteration, and closed last-event value. `PENDING`
and terminal cursors cannot carry an active iteration; `ACTIVE` must carry one;
only `COMPLETE` points exactly one past the chain. Enforce reachable revision
invariants as well: `ROUTING_BOUND` is exactly pending/index-zero/revision-zero;
a satisfied cursor at index *i* has revision at least `2i`; activation has at
least `2i+1`; repeat has at least `2i+2`; and completion of *n* profiles has at
least `2n`. Prior repeats may increase those lower bounds. Reject corrupt or
unreachable combinations before returning a resume directive. Resume the same
index; reconcile any evidence-referenced ambiguous effect before repeat or
advancement. S1 keeps the cursor in its session packet; S2/S3 persist each
cursor event with expected revision. Route completion is not task completion
and cannot satisfy the DoD by itself.

The remembered chain cannot change the endpoint, lower a profile hard floor,
weaken the DoD, grant capability, or authorize an action. If a mandatory
verifier or safety capability conflicts with the remembered chain, stop the
memory-influenced route and obtain a fresh current route or Memory proposal.

## Host Capability and State Fallbacks

| State | Required host capability | If unavailable |
| --- | --- | --- |
| `S0` | Current working context and direct verifier | Return a typed result; no Loop state |
| `S1` | Stable current-session packet and fresh observation | Finish the current bounded step only when safe, then return `BLOCKED` or an accepted `HANDOFF`; never claim resumable `PAUSED` state without the packet |
| `S2` | Authorized durable single-writer storage, schema/version checks, stable IDs, idempotency, and resume lookup; effect reconciliation only when route/effect semantics require it | `BLOCKED` or accepted `HANDOFF`; do not use an ad hoc shared file |
| `S3` | Transactional expected-revision append, ownership/claims, fencing, and effect reconciliation | `BLOCKED` or accepted `HANDOFF`; do not downgrade while the hard floor remains |

Use host-provided private state first. Creating a repository ledger, external
database, scheduler, branch, PR, or monitoring job still requires the normal
authority. A unique path prevents cross-run naming collision but is not a
multi-writer lock.

## Children, Handoffs, and Integration

A child has a narrower endpoint, its own DoD, budget, owner, state, and
terminal receipt. It never writes the parent stream directly. The parent may
mark the child accepted only after validating its exact contract revision,
artifact/input revision, evidence references, and integration rule. Parent
`DONE` still requires the parent DoD.

A handoff packet contains the schema and contract versions, workflow/run/loop
identities, current endpoint and DoD, current and best verified revisions,
criterion vector, committed effects and ambiguous outcomes, remaining budget,
ready/waiting/blocked work, and exact resume rule. Give it a canonical packet
reference, integer revision, and content hash. `HANDOFF` is valid only when an
authenticated acceptance record says `ACCEPTED`, names the recipient, and binds
that exact packet reference, revision, and hash; an evidence string or packet
presence alone cannot transfer responsibility.

## Identity, Resume, and Rollover

Require opaque unique workflow, run, loop, iteration, attempt, and event IDs
only for `S2`/`S3`; `S1` may use a compact session-local label. A workflow ID
survives physical runs. Resume the same run only from its exact compatible
committed state. Start a new run ID after terminal closure, incompatible
runtime upgrade, or explicit continuation rollover, and link it to the
predecessor with a committed continuation event. Never select “the newest
directory” as recovery authority.

Every identity-bearing scalar and list entry is a canonical nonempty string:
reject whitespace-only values and leading or trailing whitespace rather than
trimming them. Sorted-set fields reject duplicates. These rules keep hashes,
authority comparisons, receipts, and replay protection unambiguous.

## Runtime Contract Definition of Done

An implementation or host adapter conforms only when representative tests
prove:

- closed enums and staged transition priority reject invalid or ambiguous
  states without allowing corrupt lower-priority payloads to suppress safety;
- only the completion expression can return `DONE`, and it rejects omitted
  mandatory IDs, changed DoD hashes or pass rules, verdict/status mismatch,
  stale/wrong-verifier evidence, and absent, rejected, unauthenticated, or
  wrong-owner approval;
- profile selection chooses the maximum true hard floor, including explicit
  high-impact and high-consequence signals;
- one hash-bound admission is shared by all reducers, and no-budget admission
  is finite through a cumulative authenticated budget state that cannot reset;
- a complete revisioned `INTENT_COMMITTED` record precedes every durable effect,
  freezes the exact accepted DoD and optional routing binding, and a structured
  authenticated evidence-bound committed outcome and one-unit budget
  consumption precede exactly one next edge, including authenticated typed loop
  terminal receipts;
- unknown effects are reconciled under the same iteration, attempt, operation,
  idempotency key, and fence before retry;
- unavailable `S2`/`S3` capability fails closed;
- child evidence cannot complete a parent without integration;
- all seven Memory fields compile only after explicit current-user activation,
  with every routing profile preflighted atomically against role/incompatibility
  metadata plus agent-bound registry and authority maps, registry or
  authority drift failing closed, corrupt or unreachable cursor combinations
  rejected,
  recovery staying on the committed index, and advancement requiring an
  authenticated admission/proposal/budget-bound guard receipt carrying the
  hashed identity of its exact committed iteration; and
- a registered event-driven wait pauses without pretending an active action has
  positive value, while an unregistered or capability-less wait fails closed;
- every terminal non-success remains distinguishable from success.

Run the reducer's behavioral test suite. Prose-presence checks alone do not
satisfy this DoD.
