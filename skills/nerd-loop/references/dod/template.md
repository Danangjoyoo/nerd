# Definition of Done: Template

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Definition of Done router](index.md) and load it only for its named trigger.

## DoD Template

Adapt this template to the task. Omit irrelevant optional fields; never omit the outcome, mandatory criteria, evidence, integration, completion rule, or non-success stops.

```markdown
## Definition of Done — [Loop ID and name]

- **Version:** [Number or timestamp]
- **Authority:** [User/spec/policy/parent sources and named approver]
- **Outcome:** [Observable value or state]
- **Scope:** [Included surface]
- **Non-goals:** [Explicit exclusions]
- **Inherited quality floor:** [Applicable mandatory standards]

### Criteria and Evidence

| ID | Source | Required state | Conditions / threshold | Verification and evidence | Status |
| --- | --- | --- | --- | --- | --- |
| DOD-1 | [Source] | [Atomic target state] | [Scope and pass rule] | [Method, artifact, freshness, authority] | pending |

### Integration

- [Required parent, consumer, or real-environment proof]

### Completion Rule

- Declare **done** only when the submitted ID sets exactly match the accepted
  DoD hash, every mandatory criterion and integration check has an
  authenticated `PASS` verdict bound to that exact hash and the current
  artifact revision, each displayed status equals its verdict, and every
  required approval is authenticated, bound to the exact hash/artifact/named
  owner, and explicitly `APPROVED`.

### Non-success Stops

- **Blocked:** [Missing authority, dependency, access, or information]
- **Unsafe / out of scope:** [Boundary requiring escalation]
- **Impossible:** [Evidence that the target cannot be reached in the action space]
- **Failed:** [Unrecoverable execution or verification failure]
- **Budget exhausted:** [Time, token, attempt, or money ceiling]
- **Stopped:** [No positive-value, plateau, inconclusive-trace, or no-ready-work reason]
- **Cancelled:** [Authorized cancellation source]
- **Handoff:** [Named recipient and accepted continuation packet]
```
## Final Challenge

Before baselining the DoD, answer:

- Does passing this DoD prove the user's intended outcome, or only an easy proxy?
- Can the loop game, memorize, disable, skip, or repeatedly expose the verifier?
- Is every criterion source-traced and necessary?
- Are relevant failure, boundary, integration, and recovery states covered?
- Is subjective judgment anchored to a rubric and named acceptance owner?
- Is the evidence feasible, repeatable, fresh, and proportionate to risk and cost?
- Are the action space and verifier capable of moving the task toward the target?
- Could all child loops pass while the parent still fails?
- Are mandatory standards and residual risks explicit?
- Are non-success stops reported without weakening the DoD?

If a material answer is unknown, keep the DoD in draft and resolve the uncertainty before starting irreversible or expensive work.
