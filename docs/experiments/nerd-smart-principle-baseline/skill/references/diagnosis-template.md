# Diagnosis Template

## Use When

Use this template to report the investigation of a current broken, unexpected,
or inconsistent behavior. Use `rca-template.md` for a retrospective incident
analysis with impact, timeline, and prevention work.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown`; never present a hypothesis as confirmed
  evidence.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

```markdown
# [Required: Issue] Diagnosis

## Problem

[Required: State the observed issue and why it is unexpected.]

## Expected Behavior

[Required: Describe the expected result and its source.]

## Actual Behavior

[Required: Describe the observed result, including stable reproduction facts.]

## Scope and Environment

- [Required: Record affected component, version, configuration, and conditions.]

## Evidence

- [Required: Record observations, commands, logs, traces, or comparisons.]

## Hypotheses and Experiments

| Hypothesis | Discriminating experiment | Result | Status |
| --- | --- | --- | --- |
| [Required: Possible cause] | [Required: Focused check] | [Required: Observed evidence] | [Required: Supported, weakened, or open] |

## Ruled-out Causes

- [Optional: Record rejected causes and the evidence that rejected them.]

## Cause

- **Classification:** [Required: Confirmed, Probable, or Unknown]
- **Cause:** [Required: State only what the evidence supports.]
- **Reasoning:** [Required: Connect the evidence to the classification.]

## Impact

- [Optional: State the known affected behavior, users, or systems.]

## Remaining Gaps

- [Optional: Record evidence still needed to raise confidence.]

## Recommended Next Authorized Action

- [Optional: Recommend the smallest repair, experiment, or decision without
  performing it.]
```

## Completion Check

- Separate observations, hypotheses, and conclusions.
- Use Confirmed, Probable, or Unknown consistently with the evidence.
- State the smallest missing experiment when the cause remains uncertain.
- Do not repair the issue at the Diagnose endpoint.
