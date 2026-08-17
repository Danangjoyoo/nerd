# Diagnosis Template

## Use and Rules

- Use for current broken, unexpected, or inconsistent behavior.
- Use `rca-template.md` for a retrospective incident.
- Preserve confirmed facts and the requested format.
- Mark material unknowns `Unknown`; do not promote hypotheses to facts.
- Cite each material observation's source, command, artifact, or timestamp.
- Omit unused optional fields; remove all bracketed guidance.

## Fillable Template

```markdown
# [Required: Issue] Diagnosis

- **Problem:** [Required: What is wrong and why it is unexpected.]
- **Expected:** [Required: Expected result and its source.]
- **Actual:** [Required: Observed result.]
- **Reproduction:** [Required: Smallest stable trigger or evidence gap.]

## Scope and Environment

- **Affected:** [Required: Component, users, or systems.]
- **Conditions:** [Required: Version, configuration, environment, and bounds.]

## Evidence

| Observation | Source / command | Time / environment | Meaning |
| --- | --- | --- | --- |
| [Required] | [Required: Provenance] | [Required] | [Required] |

## Hypotheses and Checks

| Hypothesis | Discriminating check | Result | Status |
| --- | --- | --- | --- |
| [Required] | [Required] | [Required] | [Supported / Weakened / Open] |

- **Ruled out:** [Optional: Cause — rejecting evidence.]

## Cause, Impact, and Gaps

- **Classification:** [Confirmed / Probable / Unknown]
- **Cause:** [Required: Smallest evidence-supported claim.]
- **Evidence chain:** [Required: Observation → mechanism → behavior.]
- **Missing confirmation:** [Required for Probable or Unknown.]
- **Impact:** [Optional: Known affected behavior, users, or systems.]
- **Unknowns:** [Optional: Unresolved facts and confidence consequence.]

## Next Authorized Action

- [Optional: Smallest repair, diagnostic check, or decision; do not perform it.]
```

## Completion Check

- Separate observations, hypotheses, and conclusions.
- Match classification to evidence; name the smallest missing confirmation.
- Stop before repair or durable mutation.
