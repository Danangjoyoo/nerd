# Root Cause Analysis Template

## Use When

Use this template for a retrospective incident or root-cause analysis that
connects impact, timeline, evidence, root cause, contributing factors, and
prevention work. Use `diagnosis-template.md` for a current investigation that
has not reached retrospective analysis.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown`; never invent chronology, causality, or
  accountability.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

```markdown
# [Required: Incident] Root Cause Analysis

## Summary

[Required: Summarize what happened, the impact, and the supported root cause.]

## Impact

- [Required: State affected users, systems, duration, and severity when known.]

## Timeline

| Time | Event | Evidence |
| --- | --- | --- |
| [Required: Timestamp or relative time] | [Required: Observed event] | [Required: Source] |

## Detection and Response

- **Detection:** [Required: Explain how the incident was detected.]
- **Response:** [Required: Describe containment and recovery actions already
  taken.]

## Evidence

- [Required: List the logs, metrics, traces, changes, or testimony supporting
  the analysis.]

## Root Cause

[Required: State the causal mechanism and connect it to the evidence.]

## Contributing Factors

- [Optional: Record conditions that increased likelihood, impact, or recovery
  time without mislabeling them as the root cause.]

## Corrective and Preventive Actions

| Action | Type | Owner | Due date | Status | Validation |
| --- | --- | --- | --- | --- | --- |
| [Required: Specific action] | [Required: Corrective or preventive] | [Optional: Confirmed owner] | [Optional: Confirmed due date] | [Optional: Confirmed status] | [Required: Completion proof] |

## Lessons

- [Optional: Record what should be retained, changed, or investigated further.]

## Follow-up Validation

- [Required: Define how completed actions and risk reduction will be verified.]

## Remaining Unknowns

- [Optional: Record unresolved facts and their consequence for confidence.]
```

Include owner, due date, and status only when supplied or confirmed.

## Completion Check

- Keep the analysis evidence-based and blameless.
- Separate the root cause from contributing factors and response gaps.
- Make each proposed action specific and independently verifiable.
- Do not execute corrective or preventive actions at the Diagnose endpoint.
