# Iteration Control: Templates

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

## Contents

- [Loop Map Template](#loop-map-template)
- [Current Iteration Contract Template](#current-iteration-contract-template)
- [Ledger Event Template](#ledger-event-template)

## Loop Map Template

~~~markdown
## Loop Map — [workflow / loop]

- **Workflow ID / run ID / loop ID:** [...]
- **Focus Record / DoD / convergence versions:** [...]
- **Root outcome:** [...]
- **Workspace or environment revision:** [...]
- **Plan version:** [...]
- **Best verified checkpoint:** [...]
- **Global budget remaining:** [...]
- **Admission / budget:** [Admission hash; initial limit; current budget hash,
  revision, authenticated consumption records, and derived remaining units]
- **Routing cursor:** [Admission/proposal; chain/registry/authority hashes;
  status, profile index, active iteration, last event, cursor revision, and
  budget revision; or none]

### DoD Coverage

| Criterion | Current status | Fresh evidence | Remaining gap | Work nodes |
| --- | --- | --- | --- | --- |

### Task Network

| Work ID | Parent | Outcome / kind | Preconditions / trigger | Scope / owner | Local verifier | State |
| --- | --- | --- | --- | --- | --- | --- |

### Dependency Edges

| From | To | Type | Current support / threat |
| --- | --- | --- | --- |

### Current Control View

- **Active focus:** [...]
- **Ready set:** [...]
- **Waiting / wake-up conditions:** [...]
- **Blocked and exact unblockers:** [...]
- **Open children:** [...]
- **Ambiguous external effects:** [...]
- **Plan assumptions and threats:** [...]
~~~
## Current Iteration Contract Template

~~~markdown
## Current Iteration — [iteration ID]

- **Run / loop / ordinal / attempt:** [...]
- **Admission hash / budget revision:** [...]
- **Plan version / base revision / ownership epoch:** [...]
- **Routing profile / cursor revision:** [Active atomic profile and expected revision, or none]
- **Root DoD trace:** [...]
- **Parent outcome and integration target:** [...]
- **Primary focus:** [...]
- **Why now:** [...]
- **Hypothesis or expected information:** [...]

### Entry

- **Freshly verified preconditions:** [...]
- **Inputs and revisions:** [...]
- **Relevant latest failure / uncertainty:** [...]

### Boundary

- **Allowed mutation and tools:** [...]
- **Forbidden or preserved state:** [...]
- **Artifact / resource claim:** [...]
- **Time, cost, token, and risk budget:** [...]

### Proof and Exit

- **Expected observable result:** [...]
- **Local DoD and verifier:** [...]
- **Affected regressions / parent checks:** [...]
- **Verified exit:** [...]
- **Abort, pause, inconclusive, and handoff rules:** [...]
- **Commit payload:** [facts, receipts, evidence, new work, invalidations]
~~~
## Ledger Event Template

~~~yaml
event:
  schema_version:
  event_id:
  stream_id:
  expected_revision:
  recorded_revision:
  workflow_id:
  run_id:
  loop_id:
  iteration_id:
  attempt_id:
  ordinal:
  event_type:
  actor_id:
  owner_epoch:
  command_or_operation_id:
  causation_event_id:
  correlation_id:
  contract_versions:
  admission_hash:
  budget_revision:
  budget_consumption_ref:
  routing_proposal_ref:
  routing_chain_hash:
  routing_registry_hash:
  routing_authority_hash:
  routing_profile_index:
  routing_cursor_revision:
  plan_version:
  workspace_or_input_revision:
  recorded_at:
  observed_at:
  payload_or_artifact_reference:
  payload_hash:
  evidence_event_ids:
  decision_reason:
~~~

For terminal success, reference the exact admission, iteration commit, next
budget hash, accepted loop-scoped DoD hash/revision, fresh verifier events, and
artifact revision in an authenticated receipt. A terminal label without those
bindings is not a completion receipt.
