# Loop Profiles and Routes: Lifecycle

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Loop Profiles and Routes router](index.md) and load it only for its named trigger.

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
