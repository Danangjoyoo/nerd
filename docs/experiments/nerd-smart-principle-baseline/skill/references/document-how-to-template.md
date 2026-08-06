# How-to Document Template

## Use When

Use this template to guide a reader to one concrete outcome. Use the overview
template for conceptual understanding and the reference template for exhaustive
lookup information.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown` or explicit prerequisites; never invent
  commands, paths, or results.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

```markdown
# How to [Required: Complete One Outcome]

## Outcome

[Required: State what the reader will have when finished.]

## Audience

[Optional: State assumed experience or role.]

## Prerequisites

- [Required: List access, inputs, tools, and starting state.]

## Steps

1. **[Required: Action]**
   - [Required: Give the exact instruction.]
   - [Optional: Explain a non-obvious reason or choice.]

## Verification

- [Required: Show how the reader confirms the outcome.]

## Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| [Optional: Observable symptom] | [Optional: Evidence-backed cause] | [Optional: Corrective step] |

## Rollback or Recovery

- [Optional: Explain a safe recovery path when the procedure changes state.]

## Related Material

- [Optional: Link only directly useful overview or reference material.]
```

## Completion Check

- Keep one primary outcome and place steps in executable order.
- Make prerequisites, commands, expected results, and verification explicit.
- Include rollback or troubleshooting only when the procedure needs them.
- Stop after producing and validating the requested document; do not perform
  the procedure unless execution is separately authorized.
