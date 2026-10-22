# Incident Report and Postmortem

## Purpose and Boundary

Explain what users experienced, when it happened, how service recovered, what
the evidence supports about causes, and which follow-ups reduce recurrence or
impact. Use established incident records; do not infer certainty from a plausible
story or assign blame to individuals.

## Suggested Structure

1. **Summary:** Impact, current recovery state, and confirmed incident window.
2. **Impact:** Affected users, functions, counts, and measurement limitations.
3. **Timeline:** Timestamped observations, decisions, and actions with evidence.
4. **Causes and contributing factors:** Separate confirmed from suspected causes.
5. **Response:** Detection, mitigation, recovery, and what limited the response.
6. **Follow-up actions:** Concrete outcomes, owners, and verification when known.
7. **Unknowns:** Remaining investigation gaps and the conclusions they limit.

State the timezone. Distinguish event time from the time a responder noticed
it. Use a timeline table rather than mixing chronology into every section.

## Filled Example

Fictional incident data:

```markdown
# Export Delay — Incident Report

Status: Service recovered; follow-up work open
Incident window: 10:02–10:31 UTC on 2026-09-14

Export jobs stopped progressing while the export consumer was paused. Service
recovered after the consumer resumed and the queued jobs completed.

## Impact

- Twelve export jobs were delayed in the observed queue.
- The longest observed delay was 29 minutes.
- Whether all affected users retried is unknown.
- This report does not establish a data-exposure conclusion; review evidence
  separately before making one.

## Timeline

| Time (UTC) | Event / observation | Evidence |
| --- | --- | --- |
| 10:02 | Consumer entered paused state | Demo worker event W1 |
| 10:12 | Support reported delayed exports | Demo support record S1 |
| 10:20 | Responder confirmed pending jobs and paused consumer | Demo observations O1 |
| 10:24 | Consumer resumed | Demo worker event W2 |
| 10:31 | All twelve observed queued jobs completed | Demo job records J1 |

## Cause and Confidence

- Confirmed mechanism: the paused consumer did not pick up queued jobs.
- Unknown initiating cause: the evidence does not yet show why it was paused.
- Detection gap: the first recorded report came from support, not an automated
  queue-delay alert.

## Follow-Up

| Action | Owner | Completion evidence |
| --- | --- | --- |
| Establish why the consumer paused | Unassigned | Source-linked initiating-cause finding |
| Evaluate a queue-delay detection improvement | Service owner | Recorded decision and, if approved, validation |
| Document the approved pause/resume procedure | Operations | Reviewed runbook with recovery checks |
```

Replace demo evidence labels with real retrievable sources. Do not report the
29-minute observation as an average or claim all users were affected from twelve
observed jobs.

## Writing Corrections

| Weak statement | Better approach |
| --- | --- |
| Human error caused the outage | Describe the mechanism and supporting evidence |
| No data was lost | State the actual integrity checks or mark this unknown |
| Monitoring was bad | Identify the missed signal and response consequence |
| Improve reliability | Name the outcome, owner, and completion evidence |

## Completion Check

Verify timestamps and timezone, measured impact, timeline ordering, evidence
links, cause confidence, recovery proof, and action ownership. Preserve unresolved
causes as unknown. Separate service restoration from completion of follow-up work.
