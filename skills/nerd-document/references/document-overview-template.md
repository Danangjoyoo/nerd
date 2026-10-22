# Overview Document Template

## Use When

Use this template to explain what the subject is, why it matters, and how its
parts relate. Use the how-to template for a concrete procedure and the reference
template for precise lookup.

## Adaptation Rules

- Preserve confirmed facts and the user's requested format.
- Mark material unknowns as `Unknown` or explicit open questions; never fill
  gaps with plausible-sounding detail.
- Omit irrelevant optional sections instead of leaving empty headings.
- Remove bracketed instructions and unused placeholders from the final
  artifact.
- Lead with the central idea; use headings for concepts, bullets for peer facts,
  and a table when comparing roles or relationships. Keep causal explanations
  in short paragraphs. Read the shared writing guide for before/after examples.

## Template

```markdown
# [Required: Subject]

## Summary

[Required: Explain the subject, why it matters, and the key takeaway.]

## Audience and Purpose

[Optional: Identify assumed knowledge or a reader goal not clear from the title.]

## Key Concepts

- **[Required: Concept]:** [Required: Concise explanation.]

## How the Parts Relate

[Required: Explain the important relationships, sequence, or hierarchy.]

## Detailed Explanation

[Required: Present the established information in a logical order.]

## Examples

- [Optional: Add a minimal example that improves understanding.]

## Limitations

- [Optional: State boundaries, caveats, and known unknowns.]

## Related Material

- [Optional: Link directly relevant sources or next reading.]
```

## Completion Check

- Optimize for understanding rather than step execution or exhaustive lookup.
- Define unfamiliar terms and connect details to the central idea.
- Verify factual claims and links that can be checked.
- Stop after producing and validating the requested document.

## Filled Example

Fictional system overview:

```markdown
# How Account Exports Work

An export turns an account's records into a downloadable CSV. An administrator
requests it, a worker generates the file, and a download handler checks access
and expiry before returning the content.

## Three Parts of the Workflow

| Part | Responsibility | Output |
| --- | --- | --- |
| Request API | Check administrator access and record the request | Job ID |
| Worker | Generate a CSV for that account | Ready or failed job |
| Download handler | Check account access and link expiry | File content or denial |

## Why Generation Runs Separately

Generation can outlast the request window. A job ID lets the administrator
check progress while the worker builds the file.

## Important Boundaries

- A job belongs to one account.
- An expired download link cannot return file content.
- Link expiry does not describe when the stored file is deleted.
```

This overview explains relationships. Link a how-to for operating the workflow
and a reference for exact API fields instead of including both documents here.
