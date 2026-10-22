# Project Status Update

## Purpose and Boundary

Help stakeholders see the current state, what changed since the last update,
what needs a decision, and what happens next. Prefer a short current update to
a chronological activity log. A status label must agree with the evidence.

## Suggested Structure

- **Status and headline:** On track, at risk, blocked, or complete, using the
  organization's established vocabulary and an evidence-backed explanation.
- **Progress:** Completed outcomes since the previous checkpoint.
- **Risks / blockers:** Impact, current response, and owner if known.
- **Decisions needed:** Specific request, decision owner, and timing if supplied.
- **Next checkpoint:** Planned outcomes and dependencies.

Include a reporting period or “as of” date when known. Distinguish a target from
a commitment, an estimate from an observation, and an unassigned action from an
owned one. Do not invent percentages to make progress look measurable.

## Filled Example

Fictional project update:

```markdown
# Account Export — Project Update

As of: 2026-09-14 | Status: At risk

The request and download flows passed staging integration checks. The security
review is unassigned and blocks release approval.

## Completed Since the Last Checkpoint

- Implemented request, status, and download flows.
- Recorded passing staging results for administrator and viewer access cases.
- Drafted the support guide for expired links.

## Risks and Blockers

| Item | Consequence | Current response | Owner |
| --- | --- | --- | --- |
| Security review unassigned | Release cannot be approved | Request reviewer assignment | Engineering lead |
| File retention unresolved | Storage lifecycle and support guidance remain incomplete | Confirm the accepted policy | Unassigned |

## Decision Needed

Engineering lead: assign a security reviewer before the release checkpoint.
The checkpoint date is not yet established.

## Next Checkpoint

1. Complete security review and record its outcome.
2. Resolve retention behavior and update the design and support guide.
3. Reassess release readiness using the required test evidence.
```

In a real update, link the test results, issue records, and current release
criteria. Do not report the project complete because implementation is merged
while an accepted release condition remains unmet.

## Example: Replace an Activity Log

Weak:

> We had several meetings, worked on the export feature, and coordinated with
> other teams. Things are progressing.

Better:

> The export workflow passed staging checks. Release approval remains blocked
> by an unassigned security review; the engineering lead must assign a reviewer.

The second version names an outcome, its practical limitation, and an action.
Use the actual status supported by sources rather than manufacturing urgency.

## Writing Corrections

| Weak pattern | Better approach |
| --- | --- |
| Every work item listed | Select changes that affect stakeholder understanding or action |
| Green status with a release blocker | Explain the blocker and use the established status definition |
| “Almost done” | Name the remaining acceptance conditions |
| Long history repeated weekly | Link prior updates and summarize only material changes |

## Completion Check

Check status against evidence, dates and reporting period, completed versus
planned work, owner assignments, unresolved decisions, and the next checkpoint.
Keep a mandatory risk or decision visible near the top. Do not notify or send
the update merely because a draft is complete.
