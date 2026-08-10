# Loop Profiles and Routes: Selection

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Loop Profiles and Routes router](index.md) and load it only for its named trigger.

## Contents

- [Core Model](#core-model)
- [Loop Value Gate](#loop-value-gate)
- [Routing Record](#routing-record)
- [Selection Dimensions and Hard Floors](#selection-dimensions-and-hard-floors)

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
