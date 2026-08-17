# Root Cause Analysis Template

## Use and Rules

- Use for retrospective incidents with impact, chronology, cause, and prevention.
- Use `diagnosis-template.md` for an active investigation.
- Preserve confirmed facts and the requested format.
- Mark material unknowns `Unknown`; never invent chronology or accountability.
- Cite sources for timeline events, causal claims, and impact.
- Omit unused optional fields; remove all bracketed guidance.

## Fillable Template

```markdown
# [Required: Incident] Root Cause Analysis

## Summary and Impact

- **Event:** [Required: What happened.]
- **Impact:** [Required: Affected users/systems, duration, severity, and bounds.]
- **Root cause:** [Required: Supported cause or Unknown.]

## Timeline

| Time | Event | Evidence / source |
| --- | --- | --- |
| [Required: Timestamp or relative time] | [Required] | [Required] |

## Detection and Response

- **Detection:** [Required: Signal and source.]
- **Containment:** [Required: Actions already taken.]
- **Recovery:** [Required: Restoration evidence and time.]

## Evidence and Causality

- **Evidence:** [Required: Observation — source, timestamp, and context.]
1. [Required: Trigger or precondition — evidence.]
2. [Required: Failure mechanism — evidence.]
3. [Required: Resulting behavior and impact — evidence.]
- **Classification:** [Confirmed / Probable / Unknown]
- **Root cause:** [Required: Smallest evidence-supported causal mechanism.]
- **Missing confirmation:** [Required for Probable or Unknown.]
- **Contributing factors:** [Optional: Conditions increasing likelihood, impact, or recovery time; not root cause.]

## Corrective and Preventive Actions

| Action | Type | Owner | Due | Status | Completion proof |
| --- | --- | --- | --- | --- | --- |
| [Required] | [Corrective / Preventive] | [Optional: Confirmed] | [Optional: Confirmed] | [Optional: Confirmed] | [Required] |

## Verification, Lessons, and Unknowns

- **Follow-up check:** [Required: Test action completion and risk reduction.]
- **Success signal:** [Required: Observable pass condition.]
- **When / owner:** [Optional: Confirmed schedule and owner.]
- **Lessons:** [Optional: Retain, change, or investigate.]
- **Unknowns:** [Optional: Unresolved facts and confidence consequence.]
```

## Completion Check

- Keep the analysis evidence-based and blameless.
- Separate causal chain, root cause, contributing factors, and response gaps.
- Make actions independently verifiable; stop before execution.
