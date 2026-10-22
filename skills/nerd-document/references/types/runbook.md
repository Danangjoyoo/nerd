# Operational Runbook

## Purpose and Boundary

Help an operator recognize a known condition, choose the correct response,
verify recovery, and stop or escalate safely. Describe established operational
procedures. Do not invent production commands, thresholds, permissions, or
destructive recovery actions. Writing a runbook does not execute it.

## Inputs to Preserve

- Observable symptoms and discriminating checks.
- Scope, required access, environment, and tools.
- Approved actions, expected effects, recovery criteria, and escalation path.
- Known failure modes and any rollback or data-integrity constraints.

## Suggested Structure

| Section | Reader question |
| --- | --- |
| Trigger and impact | Is this the right runbook, and what is affected? |
| Prerequisites | What access, evidence, and starting state are required? |
| Triage | Which observation selects the correct branch? |
| Recovery steps | What exact approved action should I take next? |
| Verify | What proves recovery beyond a quiet alert? |
| Stop / escalate | When should I stop, and who owns the next decision? |
| Recovery from the procedure | What if this procedure causes a known problem? |

Use numbered steps for action order. Put expected results beside each check,
and use a decision table for branches. Keep important stop conditions visible.

## Filled Example

Fictional runbook based on an assumed approved response:

```markdown
# Export Jobs Remain Pending

Use this runbook when queued export jobs are not being picked up by a worker.
It does not cover processing failures or failed downloads.

## Prerequisites

- Read access to export-job state and worker health information.
- Approved access to resume a paused export consumer.
- Job IDs and observation timestamps for the affected account.

## Triage

| Observation | Next action |
| --- | --- |
| No pending jobs | Verify the reported symptom; do not resume anything |
| Consumer is paused and no active incident requires it paused | Follow the approved resume procedure |
| Consumer is running but jobs are not progressing | Escalate with job IDs and worker evidence |
| Pause reason is unknown | Stop and confirm the reason before resuming |

## Recovery for a Confirmed Unintended Pause

1. Record affected job IDs, timestamps, and the observed consumer state.
2. Confirm the pause is not an intentional incident response or maintenance step.
3. Use the approved worker-console procedure to resume the export consumer.
4. Observe whether the recorded jobs leave pending state.
5. Confirm at least one affected job completes with the expected account output.

## Stop and Escalate

- Stop if ownership, pause reason, or authorization is uncertain.
- Stop if jobs duplicate, account association changes, or new failures appear.
- Escalate to the documented service owner with observations and actions taken.
```

The example is not an executable production runbook until the exact console
procedure, escalation destination, observation window, and recovery criteria
are supplied. Mark those as publication blockers rather than inventing commands.

## Command Documentation

When sources provide a command, include its environment, required inputs,
expected output, and relevant stop condition. Distinguish read-only checks from
state-changing actions. Never put a sample production secret in a document.

Use explicit placeholders only for values the operator must supply, explain each
one, and preserve shell correctness. A placeholder is not a substitute for an
unknown recovery procedure.

## Writing Corrections

- Weak: “Restart everything.” Better: name the affected component and the
  approved condition under which its restart is appropriate.
- Weak: “Check logs.” Better: specify the signal, time window, and branch it selects.
- Weak: “The alert cleared, so recovery is complete.” Better: confirm the
  user-facing behavior and integrity checks defined by the service.

## Completion Check

Check applicability, prerequisites, branch conditions, exact approved actions,
expected observations, stop conditions, recovery proof, and escalation. Mark a
runbook with missing operational steps as incomplete rather than ready to use.
