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
- Start with the outcome, then prerequisites and numbered actions. Put the
  expected observation beside a step when it selects the next action. Use
  bullets for independent prerequisites and a table for troubleshooting.

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

## Filled Example

Fictional interface and confirmed behavior for illustration:

```markdown
# Download an Account CSV Export

Use this guide to request and download a one-time account report.

## Before You Start

- You must be an administrator of the account.
- The account must have access to the export feature.

## Request and Download

1. Open the account's **Exports** page.
2. Select **Request CSV**. A new export job appears with status **Pending**.
3. Wait for status **Ready** before selecting **Download**.
4. Open the CSV and confirm its account ID matches the selected account.

## Resolve a Problem

| Observation | What to do |
| --- | --- |
| Export status is Failed | Record the error code and follow the linked error reference |
| Download link expired | Follow the approved link-reissue procedure |
| Account ID does not match | Stop using the file and follow the established incident procedure |
```

Real documentation must use actual interface labels and replace referenced
procedures with verified links. If reissue or incident handling is unknown,
surface that gap rather than guessing a recovery action. This guide does not
itself authorize requesting a real export.
