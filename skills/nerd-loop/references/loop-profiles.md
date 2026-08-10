# Cost-Proportional Loop Profiles and Route Mapping

Use this reference to decide whether a task needs Nerd Loop and, if so, the
cheapest control profile and route capable of reaching its Definition of Done
(DoD). Profile selection reduces orchestration cost; it never weakens the
endpoint, authority, DoD, or required proof.

Use [the Nerd Loop Runtime Contract](runtime-contract.md) as the normative
source for hard-floor precedence, state capability requirements, status
vocabularies, budgets, and terminal decisions. This reference owns route
selection and examples, not an alternative state machine.

## Contents

1. [Core Model](#core-model)
2. [Loop Value Gate](#loop-value-gate)
3. [Routing Record](#routing-record)
4. [Selection Dimensions and Hard Floors](#selection-dimensions-and-hard-floors)
5. [Profile Catalog](#profile-catalog)
6. [State and Persistence Classes](#state-and-persistence-classes)
7. [Nerd Endpoint Mapping](#nerd-endpoint-mapping)
8. [Route Templates](#route-templates)
9. [Escalation and De-escalation](#escalation-and-de-escalation)
10. [Cost Discipline](#cost-discipline)
11. [Nerd Family and Memory Composition](#nerd-family-and-memory-composition)
12. [Failure Modes](#failure-modes)
13. [Routing Examples](#routing-examples)
14. [Profile-Router Definition of Done](#profile-router-definition-of-done)

## Core Model

Keep four decisions separate:

| Decision | Owner | Meaning |
| --- | --- | --- |
| **Task endpoint** | Nerd Smart / current user | What may be delivered, mutation authority, and endpoint stop condition |
| **Loop profile** | Nerd Loop | How much recurrence, state, coordination, and governance are justified |
| **Route template** | Nerd Loop plus active specialty | Which evidence-producing stages and cause-labelled back edges apply |
| **Verifier** | DoD and task risk | What fresh evidence can support the completion claim |

Do not call a loop profile a new endpoint. A `Diagnose` endpoint remains
diagnosis-only even when its loop is complex. An `Execute` endpoint may contain
supporting specification, planning, diagnosis, or monitoring stages without
changing the requested deliverable.

Compile a loop as:

```text
resolved Focus endpoint
  + cheapest adequate profile
  + one route template
  + only required persistence/authority overlays
  + proportionate verifier
  = executable Loop Contract
```

Use these profiles:

```text
D0 Direct -> L1 Minimal -> L2 Simple -> L3 Managed -> L4 Complex
```

This ordering describes control-plane overhead, not task prestige, code size,
or how sophisticated the agent appears. One child inside an L4 migration may
use D0 or L1. A short PR route may require L3 because it crosses external and
human wait boundaries.

## Loop Value Gate

Before creating loop artifacts, ask:

> Will another evidence-driven cycle materially reduce a DoD gap, uncertainty,
> expected rework, or consequential risk beyond its orchestration cost?

Use `D0 Direct` when the answer is no. Do not create a loop merely because Nerd
Loop was available, a task has several mechanical steps, or a verifier exists.

Count benefits as:

- a mandatory DoD criterion credibly closed;
- a material unknown resolved;
- a risky assumption tested before expensive work;
- rework avoided through an early feedback edge; or
- an external or human state safely reconciled.

Count costs as a vector, not an invented universal score:

- active input and output tokens;
- active wall-clock time;
- tool, model, compute, and verifier cost;
- expected rework;
- coordination and merge overhead;
- persistent-state overhead;
- external effects; and
- user interruptions.

Track waiting wall time separately. CI, review, deployment observation, or a
scheduled condition should be `PAUSED` or `WAITING`, not an active iteration
that spends tokens polling.

## Routing Record

For L1 and above, create one compact routing record before the first mutation
or evidence cycle. Keep it internal for clear L1/L2 work. Persist it for L3/L4,
or show it when selection changes cost, authority, persistence, or a user
decision.

> **Loop Routing Record — [Root goal]**
> - **Endpoint:** [Discuss | Ideate | Explore | Diagnose | Review | Specify | Document | Plan | Execute | Monitor]
> - **Profile:** [D0 | L1 | L2 | L3 | L4]
> - **Route:** [Named template or smallest explicit graph]
> - **Selection reasons:** [Observed hard floors, not adjectives]
> - **State class:** [S0 | S1 | S2 | S3]
> - **Admission identity:** [Canonical admission reference/revision and hash]
> - **DoD form:** [Micro | Compact | Full]
> - **Verifier:** [Lowest-cost fresh proof sufficient for the claim]
> - **Active budget:** [Initial limit plus authenticated cumulative budget
>   hash/revision; remaining units are derived]
> - **Wait policy:** [Event, condition, or none]
> - **Escalate when:** [Concrete triggers]
> - **De-escalate when:** [Concrete conditions]

D0 needs no routing artifact. Apply its micro-DoD and direct proof in working
context, then stop.

## Selection Dimensions and Hard Floors

Choose the minimum profile that provides every capability the task requires:

```text
selected profile = max(
  route floor,
  adaptivity floor,
  mutation and reversibility floor,
  evidence floor,
  durability floor,
  coordination floor,
  authority and consequence floor
)
```

This is a constraint maximum, not a weighted complexity score. A low average
cannot cancel one hard safety, durability, or evidence requirement.

Inspect these observable dimensions:

| Dimension | Lower-cost signal | Higher-cost signal |
| --- | --- | --- |
| **Back edges** | No result can change the route | Repeated or branching evidence-driven cycles |
| **Scope** | One known target or bounded surface | Multiple coupled modules, services, data stores, or repositories |
| **Uncertainty** | Known transformation and decisive verifier | Unknown cause, unstable requirements, or ambiguous success |
| **Mutation** | Read-only or tiny reversible local change | Durable contract, migration, destructive, or hard-to-reverse effect |
| **Feedback** | Immediate deterministic local check | Flaky, delayed, proxy, live, or human judgment |
| **Duration** | Completes in the current active session | Must survive pause, crash, handoff, or scheduled recurrence |
| **Coordination** | One owner and mutation scope | Independent children, shared resources, or multiple writers |
| **External state** | No external effects | PR, CI, deployment, remote service, approval, or ambiguous receipt |
| **Consequence** | Local and contained | Security, privacy, production, compliance, money, or data-loss risk |

Apply these hard floors:

- No back edge, immediate decisive proof, and no persistence need: `D0`.
- Multiple read-only probes, search coverage, or candidate validation: at least
  `L1`.
- Workspace mutation with a possible correction cycle: at least `L2`.
- Delayed feedback, managed recovery of in-flight work across a coordination
  boundary, CI/review, a durable or formally auditable human gate, external
  receipt, shared resource, or independent child loop: at least `L3`. A simple
  authorized single-writer checkpoint may raise L1/L2 to S2 without adding the
  rest of L3. An immediate clarification or acceptance in the current
  interaction does not alone force L3.
- Coupled workstreams, evolving contracts during execution, irreversible,
  high-impact, or high-consequence effects, staged rollout, or materially
  ambiguous success: `L4`. The explicit `high_impact` and `high_consequence`
  route signals each independently impose that floor.

Keywords such as “simple,” “small,” “quick,” or “routine” do not lower a hard
floor. Likewise, many files do not by themselves force L4 if one deterministic
operation and verifier safely cover them.

## Profile Catalog

### D0 — Direct Completion

Use when there is no useful back edge: answer, transform, make one tiny
reversible change, run a decisive check, and stop.

```text
micro-DoD -> direct action -> fresh proof -> typed result
```

Minimum mechanics:

- one resolved endpoint and authority boundary;
- one-sentence observable micro-DoD;
- the smallest sufficient action;
- fresh proof when making a completion claim; and
- `DONE` or a typed non-success result.

Do not create a Loop Map, convergence history, TODO list, child loop, or durable
ledger. Persist an effect receipt only if recovery or ambiguity requires it.

Examples: correct a typo and run its direct check; answer from current evidence;
change one static value with a parser validation.

### L1 — Minimal Loop

Use for bounded inspection, bug finding, triage, fact search, review, diagnosis,
or a sandbox probe where one focus and a small number of adaptive evidence
steps suffice.

```text
scope -> probe -> validate evidence -> report or select next probe
```

Minimum mechanics:

- compact DoD with scope and evidence standard;
- exactly one current focus;
- an in-session evidence record;
- one cost/coverage boundary; and
- residual uncertainty or risk in the result.

Do not create child loops or durable project state by default. A repeated probe
must target a named evidence gap; do not broaden aimlessly.

For “find bugs,” `DONE` means the declared evidence-coverage criteria pass,
every candidate has a validated disposition, every reported finding meets its
evidence rule, and the required residual-risk statement is complete. Finishing
a probe plan is activity, not proof. “No findings” means no validated findings
within the declared scope, coverage, and budget, never proof that no defects
exist.

### L2 — Simple Loop

Use for single-owner local delivery with a known or mostly stable route and
deterministic feedback: normal code changes, TDD/BDD slices, focused repair,
small spec-to-code work, or routine maintenance.

```text
smallest route slice -> act -> targeted verify -> integrate -> done or replan
```

Minimum mechanics:

- compact DoD;
- small route graph or lightweight plan;
- one Current Iteration Contract;
- targeted verification after each behavior-affecting cycle;
- compact failure, progress, and replan record; and
- an in-session checkpoint, raised to durable state only when needed.

Do not build a full dependency graph, durable ledger, convergence window, or
subagent organization merely because the task has several sequential steps.
Replan only when evidence invalidates the current route.

### L3 — Managed Loop

Use when simple work must survive or coordinate across process boundaries: PR
and CI cycles, review waits, external integrations, resumable delivery, shared
resources, human gates, or independently verifiable child work.

```text
map -> act -> persist receipt -> pause/reconcile -> verify/integrate -> replan
```

Minimum mechanics:

- complete DoD and integration criteria;
- versioned Loop Map and current focus;
- durable single-writer ledger or checkpoint;
- semantic scheduling and event-driven pause/resume;
- ownership and resource claims where relevant;
- stable idempotency keys for ambiguous external retries;
- explicit child contracts when work is delegated; and
- compact convergence and stall responses.

A route may begin at L2 and escalate immediately before its first external
push, long wait, handoff, or parallel child. Earlier local work remains valid.

### L4 — Complex Loop

Use for adaptive, governed programs: coupled subsystems, architecture or
contracts evolving during delivery, high-impact migrations and releases,
security remediation across boundaries, staged rollout, or success measured by
noisy and interacting signals.

```text
contract and risk model
  -> architecture and rollback
  -> partially ordered child loops
  -> integrate interfaces and artifacts
  -> verifier portfolio
  -> staged release and observation
  -> advance, repair, reframe, or roll back
```

Minimum mechanics:

- full DoD, Convergence Contract, authority, budget, and stop policy;
- hierarchical Loop Maps and dependency/interface governance;
- transactional or otherwise race-safe ledger and fenced ownership;
- isolated child loops, each using its own cheapest adequate profile;
- best verified checkpoints and rollback or compensation plans;
- multi-layer and, when justified, independent verification;
- explicit human and external-effect gates; and
- staged observation with cause-labelled repair, reframe, and rollback paths.

An L4 parent must not force every child to pay L4 overhead.

## State and Persistence Classes

Select state separately so one needed receipt does not force an otherwise tiny
task into a heavyweight program.

| Class | State | Typical profiles | Requirement |
| --- | --- | --- | --- |
| `S0` | No loop state | D0 | Working context and final proof only |
| `S1` | Compact in-session state | L1–L2 | DoD, focus, evidence, and next discriminating step |
| `S2` | Durable single-writer state | L3, single-owner L4, or durable lower-tier route | Checkpoint, causal events, resume cursor, effect receipts |
| `S3` | Transactional/fenced state | Shared-resource ownership or consequential multi-writer effects at L3/L4 | Expected revision, ownership epoch, idempotency, recovery protocol |

Raise the state class without raising the full profile when only persistence is
needed. Raise the profile when persistence interacts with coordination,
uncertainty, risk, or multiple back edges.

Likewise, L4 does not automatically force S3: coupled contracts, noisy success,
or a hard-to-reverse single-owner program may remain S2. Raise to S3 when
shared ownership or consequential writers actually require transactional
claims and resource fencing.

Do not make `effect_reconciliation` a universal S2 tax. Require it for S3, an
external-receipt or staged-rollout signal, or a route such as `pr_delivery`
whose remote effect can become ambiguous. A plain durable single-writer
checkpoint remains valid without it.

Creating an unrequested persistent artifact may cross the user's authority
boundary. Prefer a host-provided private state store; ask before adding
repository files or durable infrastructure that the endpoint did not imply.

## Nerd Endpoint Mapping

Use this as a starting map after Nerd Smart resolves exactly one endpoint. Task
facts and hard floors override defaults.

| Endpoint | Lowest common route/profile | Escalate when |
| --- | --- | --- |
| **Discuss** | `direct/D0` | Evidence gathering or iterative decision testing becomes necessary |
| **Ideate** | `options/L1`: generate -> screen -> recommend | Prototypes, experiments, or several stakeholder constraints must be reconciled |
| **Explore** | `inspect/L1`: question -> evidence -> synthesis | Broad coverage or durable research state raises the profile but remains non-mutating |
| **Diagnose** | `inspect/L1` or `experiment/L2` | Reproduction is iterative, boundaries interact, or the runtime must be observed over time |
| **Review** | `inspect/L1` | Several coupled surfaces, independent reviewers, or integration reasoning is necessary |
| **Specify** | `draft_validate/L1`; raise the profile to L2 for an authorized persisted revision cycle without changing the route | Multiple interfaces or stakeholder gates make the specification adaptive; a durable approval wait raises it to L3 |
| **Document** | `direct/D0` or `draft_validate/L1` | Rendering, examples, cross-document consistency, or review feedback creates back edges |
| **Plan** | `plan_validate/L1` | Dependencies, unknowns, or experiments are required to make the plan actionable |
| **Execute** | `direct/D0`, `piv/L2`, or `tdd/L2` | Persistence/external gates require L3; coupled high-risk work requires L4 |
| **Monitor** | `inspect/L1` for one immediate recheck or `monitor/L3` for durable waiting | Waiting must survive turns, conditions interact, or action/incident recovery is authorized |

Endpoint boundaries always win:

- `Specify` stops before planning or implementation unless the user requested a
  broader Execute outcome.
- `Plan` stops before mutation.
- `Diagnose` stops before repair.
- `Review` reports findings without edits.
- `Monitor` observes without mutation unless the endpoint is explicitly changed
  or Execute already authorizes a larger lifecycle.

## Route Templates

Use one closest route. Do not combine templates into ceremony; add a stage only
when it consumes evidence or produces a required artifact, decision, effect, or
proof.

### Direct Completion — `direct`, base D0

```text
micro-DoD -> one bounded action or answer -> decisive fresh proof -> stop
```

There is no back edge and no Loop state. If proof exposes a material gap that
needs another adaptive cycle, stop D0 admission and select the new minimum
profile before acting again. Never retain `direct` while raising it above D0.

### Options and Recommendation — `options`, base L1

```text
decision frame and constraints
  -> generate materially distinct options
  -> screen infeasible or dominated choices
  -> compare survivors against declared criteria
  -> recommend one with trade-offs and uncertainty
  -> stop at the Ideate endpoint
```

Return to the frame only when evidence exposes a missing decision criterion.
Do not prototype, mutate, or execute an option unless the endpoint changes.

### Draft and Validate — `draft_validate`, base L1

```text
content contract and audience
  -> smallest complete draft
  -> factual, structural, link/schema, or render checks that apply
  -> revise one evidenced gap
  -> deliver when the artifact DoD passes
```

Use for Specify or Document when one bounded validation back edge is useful.
Raise to L2 only if authorized local implementation-style mutation and repeated
deterministic feedback become part of the requested outcome; raise to L3 for a
durable approval/review wait.

### Plan and Validate — `plan_validate`, base L1

```text
confirmed outcome and DoD
  -> dependencies, risks, and proof map
  -> actionable ordered or partial-order plan
  -> coverage, feasibility, and authority review
  -> revise a concrete planning gap
  -> stop before implementation
```

A Plan endpoint never mutates the target system. An implementation discovery
is recorded as an assumption, probe requirement, or blocker unless the user
changes the endpoint.

### Bug Finding — `inspect`, base L1

```text
scope and risk areas
  -> cheapest static/search probes
  -> targeted dynamic probes when needed
  -> reproduce and validate candidates
  -> deduplicate and prioritize
  -> coverage and residual-risk statement
  -> report
```

Back edges:

- unexamined high-risk surface -> next targeted probe;
- disputed candidate -> reproduce or corroborate;
- repair requested -> new Execute contract using `piv` or `tdd`, normally L2.

Use Review for a bounded artifact bug hunt. Use Diagnose and Nerd Surgery for a
known broken behavior whose cause is requested. Use Execute only when repair is
authorized.

### Plan–Implement–Verify — `piv`, base L2

```text
smallest useful plan
  -> bounded implementation
  -> targeted verification
  -> integration/DoD check
  -> done or cause-labelled back edge
```

Route failures by cause:

- implementation defect -> implementation;
- false assumption or missing dependency -> plan;
- broken or insufficient verifier -> verifier repair;
- endpoint or acceptance ambiguity -> user/spec authority.

Do not return to planning after every failure when the plan was not disproved.

### TDD or BDD Delivery — `tdd`, base L2

```text
select one behavior criterion
  -> write the smallest test or scenario
  -> prove RED for the intended reason
  -> minimal GREEN implementation
  -> refactor while green
  -> affected integration/regression evidence
  -> next criterion or done
```

An invalid RED returns to test or behavior definition. A regression returns to
implementation. Requirement ambiguity returns to specification authority.

Nerd Execute owns the test-first micro-workflow. Nerd Loop owns the root DoD,
current criterion, history, budget, and decision to continue or reframe; do not
duplicate Execute's mechanics.

### Specification to Delivery — `spec_delivery`, base L2

```text
baseline specification and criterion traceability
  -> plan one vertical slice
  -> implement
  -> verify against mapped criteria
  -> integrate
  -> next slice or cause-labelled revision
```

Back edges:

- code misses a clear criterion -> plan or implementation;
- specification is contradictory or materially ambiguous -> clarification;
- proposed specification change alters endpoint or DoD -> user confirmation.

Use L3 for several independently delivered components or approval handoffs. Use
L4 when interfaces, data, and architecture materially co-evolve.

### PR, CI, and Review Lifecycle — `pr_delivery`, base L3

```text
plan
  -> code
  -> local verification
  -> authorized push/open PR
  -> PAUSE for CI or review event
  -> classify feedback
  -> update plan or code when relevant
  -> reverify
  -> merge-readiness result or next wait
```

The graph is simple; the profile is managed because the task crosses external
effects, durable waits, and human feedback. Begin local work at L2 if useful,
then commit an L3 checkpoint before the first push or wait.

This route itself requires authenticated event-driven wake and effect
reconciliation capabilities; the caller cannot omit a CI/review or
external-receipt signal to bypass those admission requirements.

Classify feedback:

- related code or CI failure -> plan/implementation;
- flaky or infrastructure failure -> diagnose, policy-governed retry, or wait;
- unrelated failure -> record a blocker instead of changing product code;
- review request changing endpoint or acceptance -> authority checkpoint.

Push, PR creation, review response, merge, and deployment remain separate
external-effect authorities. The route does not grant them.

### Routine Maintenance — `routine`, base L2

```text
load last accepted contract and fresh current state
  -> compute bounded delta
  -> apply authorized routine action
  -> focused verification
  -> record outcome and next semantic trigger
  -> stop
```

Use for recurring dependency updates, queue triage, generated reports, or other
stable daily work. Reuse the route and confirmed behavioral guidance, but use a
fresh root execution episode and verifier evidence. Do not treat yesterday's
success as today's proof.

Raise to L3 when a run crosses PR/CI, human review, remote mutation, or delayed
conditions. A scheduler or recurring monitor is a separate authorized runtime
capability; the route does not create one.

### Monitor — `monitor`, base L3 for durable waiting

```text
observe -> compare with stop/wake conditions -> report change or PAUSE -> observe
```

Use the platform's wait or monitoring mechanism. Persist the condition and last
observation, then consume no active loop budget while waiting. A one-time
immediate recheck may remain L1. Selecting durable `monitor` itself requires an
authenticated wake-event capability.

### Experiment or Optimization — `experiment`, base L2

```text
baseline -> hypothesis -> controlled change -> compare with best checkpoint
  -> accept or revert -> update hypothesis
```

At L2 the experiment is single-owner, local, immediately observed,
deterministic enough for its declared comparison, and reversible to the best
checkpoint. Raise to L3 when it needs managed recovery beyond a simple
single-writer checkpoint, delayed/noisy observation, an external receipt, or
formal human judgment. Use L4 for coupled
SLOs, production experiments, high-consequence interventions, or proxy-only
success. Declare the comparison, noise treatment, improvement-per-cost,
plateau, rollback, and hard-budget rules at the profile that actually needs
them.

Use this route only at Diagnose for a bounded non-repair diagnostic experiment,
or at Execute for authorized mutation. Explore remains `inspect` and
non-mutating.

### Adaptive Complex Program — `adaptive_program`, base L4

```text
contract, DoD, authority, and budget
  -> architecture, threat/data risks, and rollback
  -> partially ordered child-loop map
  -> execute ready children at their cheapest profiles
  -> integrate contracts and artifacts
  -> system, adversarial, and operational verification
  -> staged/canary release when authorized
  -> observe
  -> advance, repair, reframe, or roll back
```

Examples: zero-downtime multi-service/database migration, cross-system security
remediation, staged platform replacement, or regulated release.

Cause-labelled back edges:

- child-local defect -> that child's route;
- interface mismatch -> affected children plus integration contract;
- architecture contradiction -> architecture decision gate;
- rollout regression -> rollback or stabilization;
- endpoint change -> user authority.

## Escalation and De-escalation

Escalate at a committed boundary before the next affected action when evidence
reveals a higher hard floor:

- a new back edge or branch is necessary;
- a supposedly decisive verifier becomes `UNKNOWN`, flaky, or proxy-only;
- scope crosses a module, service, contract, data, or repository boundary;
- work must survive pause, crash, handoff, CI, or human review;
- an external action may have an ambiguous outcome;
- independent children, shared resources, or parallel writers become useful;
- rollback, compensation, stage gates, or higher assurance become necessary;
- repeated causal failure, regression, divergence, or oscillation shows the
  current control mechanics are insufficient; or
- forecast remaining cost exceeds the active profile budget.

Change strategy before escalating merely because progress is flat. Raising a
profile without adding a required capability only makes failure more expensive.

De-escalate at a committed boundary when every remaining ready action satisfies
a lower profile's assumptions:

- no ambiguous in-flight external effect;
- no active coupled child or shared-resource claim;
- no pending human or approval gate;
- remaining checks are immediate and deterministic;
- a stable checkpoint and recovery route exist; and
- the lower profile remains above every evidence and consequence floor.

Preserve earlier durable state and evidence; reduce only future overhead. Do
not delete required gates, narrow the DoD, or downgrade proof to obtain a lower
profile.

Profile change is normally a route decision inside the accepted endpoint.
Obtain user confirmation when it materially expands cost, persistence,
external effects, risk, mutation scope, or hard budget. An endpoint change
always follows Nerd Smart's authority process.

## Cost Discipline

Use these rules at every profile:

- Start at the minimum hard floor; do not prepay for possible complexity.
- Keep an operation only when it advances a DoD criterion, resolves a material
  unknown, enables an authorized action, or produces required proof.
- Reuse evidence until mutation, staleness, contradiction, or dependency change
  invalidates it.
- Choose the lowest-cost fresh verifier that observes the exact claim; broaden
  only on a risk, authority, repository, or evidence trigger.
- Do not create a plan when the next safe action and verifier are already clear.
- Do not compute multi-iteration convergence metrics before comparable
  iterations exist or dynamics can change a decision.
- Do not create a durable ledger when S1 state can safely finish the task.
- Do not dispatch a subagent unless independence and expected critical-path or
  confidence benefit exceed setup, context, integration, and review cost.
- Batch known independent reads and verifiers; keep evidence-dependent actions
  sequential.
- Bundle human questions at real decision gates without combining independent
  goal approvals.
- Stop immediately when the DoD passes, the endpoint stop condition is reached,
  or no next cycle has positive justified value.

Record efficiency telemetry only when it has a consumer:

- active versus waiting wall time;
- tokens and model calls;
- tool and expensive verifier calls;
- external mutations;
- planned and unplanned human interruptions;
- mandatory criteria closed, reopened, or remaining unknown;
- repeated failure signatures and rework; and
- terminal state.

Compare routes using normalized costs or a vector whose weights come from the
user, host, or runtime. Never add raw tokens, seconds, money, and interruptions
as if they had universal exchange rates. A useful host-calibrated measure is:

```text
verified mandatory-gap closure / normalized active cost
```

Use telemetry to improve future route defaults, never to infer authority or
weaken acceptance criteria.

## Nerd Family and Memory Composition

Nerd Loop is a controller, not a second primary specialty.

- Consume Nerd Smart's one resolved Focus Record and endpoint; do not create a
  competing authority record.
- Select at most one primary specialty for the current iteration.
- Give Nerd Execute one bounded mutation/evidence contract. Execute owns the
  implementation mechanics and should not create a duplicate Loop Map.
- Let Nerd Surgery own its causal diagnostic micro-loop. Consume its Case Record
  and experiment evidence; never bypass Surgery's approval or architecture
  gates with remaining Loop budget.
- Treat Nerd Fast as an optional operational modifier only when explicitly
  invoked or a concrete latency requirement triggers it. Fast may optimize an
  iteration but may not shrink the Loop DoD or proof.
- Treat Nerd XFast as mutually exclusive. XFast forbids the plans, ledgers,
  subagents, and workflow composition Nerd Loop requires; ask the user to choose
  one if both are invoked.

Only when the current user explicitly invokes Nerd Memory may its confirmed
contracted `action` field propose a familiar workflow such as TDD or routine PR delivery, while its
`routing` field may propose one complete ordered chain of atomic
agent/skill/tool/MCP profiles. Current task facts still establish the minimum
Loop profile. Preserve the remembered chain exactly, resolve it against the
current authenticated registry, role/incompatibility metadata, and authority
after consumption, admit at most one primary specialty, and fail closed on any
mismatch. Installation or prior use never activates Memory. Every memory
influence retains the Behavioral Memory confirmation gate. Do not interpret an
uncontracted runtime field or learn the agent-selected profile from execution
success.

## Failure Modes

Avoid:

- **Universal heavyweight loop:** every task gets a full plan, ledger,
  convergence window, subagents, and broad verification.
- **Keyword routing:** “small” forces L1 despite production or external risk.
- **Route-length routing:** a short PR graph is called simple despite durable
  waits and external effects.
- **File-count scoring:** many mechanical files force L4 without coupled risk.
- **Verification discount:** lower profile means weaker evidence than the DoD
  requires.
- **Busy waiting:** CI, review, or scheduled work consumes active iterations.
- **Plan reflex:** every failure returns to planning without classifying cause.
- **Escalation theater:** more artifacts are added without a missing capability.
- **Profile thrashing:** state changes without committed new evidence.
- **Complexity inheritance:** every child pays the parent's highest profile.
- **Persistent-state leakage:** repository files are created for private loop
  state without authority.
- **Telemetry theater:** cost is measured but never changes a route decision.

## Routing Examples

| Task | Endpoint | Route/profile | Why |
| --- | --- | --- | --- |
| Correct one typo and run its exact check | Execute | `direct/D0` | No useful back edge |
| Find bugs in one module | Review | `inspect/L1` | Bounded probes and validated findings |
| Establish why a named crash occurs | Diagnose | `inspect/L1`, then `experiment/L2` if needed | Cause sought; no repair authority |
| Fix a null crash with a regression test | Execute | `tdd/L2` | Local mutation and deterministic correction cycle |
| Implement a stable OpenAPI endpoint | Execute | `spec_delivery/L2` | Fixed criteria and local integration proof |
| Specify, plan, and implement one feature | Execute | `spec_delivery/L2` or L3 if components/handoffs emerge | Root endpoint includes the whole lifecycle |
| Code, push a PR, triage CI, and wait for review | Execute | `pr_delivery/L3` | External effects, durable waits, human feedback |
| Perform the same bounded dependency-update task daily | Execute | `routine/L2`, L3 when PR/CI applies | Reusable route; fresh episode and proof |
| Observe a deployment until healthy | Monitor | `monitor/L3` | Durable event-driven wait; no busy polling |
| Zero-downtime migration across services and databases | Execute | `adaptive_program/L4` | Coupled contracts, rollback, staged operational evidence |

## Profile-Router Definition of Done

The router is correct only when:

- exactly one user endpoint controls deliverable, authority, and stop;
- D0 bypasses loop artifacts when iteration adds no value;
- every actual loop has an observable DoD and one current focus;
- the selected profile is the minimum satisfying every observed hard floor;
- all reducer commands share one hash-bound admission and cumulative budget,
  so no later phase can downgrade the route/state or reset the active limit;
- route templates contain only useful stages and cause-labelled back edges;
- every route named by the endpoint mapping has one defined template and one
  unambiguous base profile;
- state persistence is proportionate and authorized;
- waiting consumes no active iteration budget;
- lower profiles compress representation rather than weaken rigor;
- higher profiles add a required capability rather than ceremonial artifacts;
- escalation and de-escalation preserve contracts and verified evidence;
- each child uses its own cheapest adequate profile;
- memory, specialties, and speed modifiers retain their authority boundaries;
- endpoint, cost, risk, persistence, external-effect, and hard-budget changes
  receive required user confirmation; and
- the task stops immediately at verified DoD completion or an honest typed
  non-success state.
