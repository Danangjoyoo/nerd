# Reference Document Template

## Use When

Use this template to provide precise lookup of established contracts, options,
fields, commands, or facts. Use the overview template for explanation and the
how-to template for an ordered procedure.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown` or explicit gaps; never infer exact values
  from incomplete evidence.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.

## Template

````markdown
# [Required: Subject] Reference

## Scope

[Required: State what this reference covers and excludes.]

## Terminology

| Term | Meaning |
| --- | --- |
| [Optional: Term] | [Optional: Exact meaning in this context] |

## Entries or Contracts

### [Required: Entry, command, field, or interface]

- **Type or shape:** [Optional: Exact representation.]
- **Required:** [Optional: Yes, no, or conditional rule.]
- **Description:** [Required: Precise behavior or meaning.]
- **Constraints:** [Optional: Valid range, compatibility, or invariant.]

## Defaults and Invariants

- [Required: State confirmed defaults and rules that always hold.]

## Examples

```text
[Optional: Minimal valid example]
```

## Errors and Limitations

| Condition | Meaning or result |
| --- | --- |
| [Optional: Error or boundary] | [Optional: Exact observed behavior] |

## Related Material

- [Optional: Link authoritative sources, overview, or how-to material.]
````

## Completion Check

- Prefer tables and compact entries when they improve lookup.
- Use exact names, values, defaults, constraints, and compatibility statements.
- Verify examples and links against available authoritative material.
- Stop after producing and validating the requested document.
