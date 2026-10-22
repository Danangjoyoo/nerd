# Writing for Google Docs

## Use When

The reader needs a narrative document: a PRD, technical design, test plan,
proposal, or reviewable report. Read the matching type guide for content; this
guide changes presentation and delivery, not the underlying requirements.

## Shape the Document

- Open with a descriptive title, purpose, and the key decision or outcome.
- Use native heading styles in a consistent hierarchy. They support the
  document outline; bold body text is not a substitute for a heading.
- Use bullets for peer facts and native numbering for ordered steps.
- Use tables for requirements, comparisons, owners, and repeated test fields.
  Keep long reasoning outside table cells.
- Place supporting detail after the main argument. Add a table of contents when
  the length makes navigation useful.
- Use intentional page breaks at major boundaries in paged output; do not add
  repeated blank lines to force layout. Keep headings with the text they introduce.

## Example: Reviewable PRD Opening

Fictional content to demonstrate layout:

```markdown
# Account CSV Export — Product Requirements

Status: Draft | Owner: Product team | Review request: Confirm release scope

Administrators need a downloadable account report for monthly reconciliation.
The first release provides a one-time CSV export with an expiring download link.

## Scope to Confirm

| Included | Excluded |
| --- | --- |
| One-time account CSV | Scheduled exports |
| Administrator access | Viewer access |
| 24-hour download link | PDF output |

## Acceptance Criteria

1. An administrator can request an export for their account.
2. A viewer cannot request or download an export.
3. An expired download link does not return file content.

## Open Questions

- File retention is unknown; confirm it before approving the storage lifecycle.
```

When creating a native Doc, render the title, headings, lists, and table as native
structures. A Markdown fallback remains a draft until transferred and checked.

## Review and Delivery

1. Preserve supplied review status, owner, and source links. Do not invent
   approval, reviewers, or due dates.
2. Keep unresolved decisions visible in the body. Comments may support review,
   but a required action must remain findable without opening every comment.
3. Verify hierarchy, table readability, links, and page breaks in the delivered
   form when access permits. Check an export separately if it is the deliverable.
4. Return the native document link after a confirmed write, or the prepared file
   path and explicit transfer/verification gap.

Do not publish, change access, or send review notifications merely because a
Google Docs destination was named. If a native connector is unavailable, provide
a structured Markdown or requested document-file draft without claiming upload.

## Pitfalls

| Problem | Better approach |
| --- | --- |
| Every paragraph is a bullet | Keep reasoning in short paragraphs |
| Requirements buried in meeting notes | Put confirmed requirements in a visible table or numbered list |
| Wide table breaks the page | Reduce columns or split by reader task |
| Large bold lines imitate sections | Apply native headings when creating the Doc |

## Platform Reference

Google documents heading-based navigation in
[document outlines](https://support.google.com/docs/answer/6367684?hl=en) and
[tables of contents](https://blog.google/products-and-platforms/products/workspace/how-to-google-docs-table-of-contents/).
Check current platform help before giving UI-specific menu instructions.
