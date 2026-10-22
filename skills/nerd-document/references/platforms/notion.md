# Writing for Notion

## Use When

The reader needs a navigable knowledge page, living project document, runbook,
or collection of related records. Read the document-type guide for content;
this guide explains page structure, navigation, and maintaining visible facts.

## Choose the Smallest Useful Structure

| Need | Structure |
| --- | --- |
| One explanation, specification, or procedure | A page with descriptive headings |
| A small static comparison | A simple table |
| Many records with common properties and lifecycle | A database, when justified and authorized |
| Optional long evidence | A linked subpage or collapsible detail |

Do not turn a short document into a database by default. Database records can
have their own pages; keep common status and ownership in properties rather
than copying a second register into prose.

## Make Important Information Visible

- Start with the page purpose, current status, and reader action or takeaway.
- Use native heading levels, bullets, numbered steps, and tables intentionally.
- Keep prerequisites, decisions, active blockers, and required actions outside
  collapsed sections.
- Use a contents block when a long page needs navigation.
- Link source evidence beside the claim. Link a canonical shared contract
  rather than copying it into several pages.
- Use callouts sparingly for decisions or important constraints. Use whitespace
  or a divider at a real section boundary, not between every paragraph.

## Example: Export Knowledge Page

Fictional page body:

```markdown
# Account Export

Purpose: Help support staff explain export access and resolve failed downloads.
Status: Draft; access rules confirmed, retention policy unresolved.

## What Support Needs to Know

- Only account administrators can request an export.
- Download links expire after 24 hours.
- Link expiry does not establish when the stored file is deleted.

## Resolve an Expired Download

1. Confirm the caller is an administrator of the account.
2. Check whether the download link has expired.
3. Follow the approved reissue procedure linked in the export runbook.

## Open Questions

| Question | Consequence | Owner |
| --- | --- | --- |
| When is the file deleted? | Retention guidance cannot be published as confirmed | Unassigned |

## Supporting Evidence

Link the confirmed requirements and runbook here.
```

In a native page, replace references to linked evidence with real accessible
links. Keep the open retention question visible rather than burying it inside
a toggle named “More.”

## Example: When a Database Helps

A maintained decision register can use properties such as `Decision ID`,
`Title`, `Status`, `Owner`, and `Decided on`. Each record's page contains the
decision rationale using the decision-record type guide. A short document with
two decisions usually needs only two sections or a simple table.

## Delivery and Maintenance Check

1. Confirm the destination page or parent from supplied context before a native
   write. Do not guess a workspace or publish to a similarly named page.
2. Preserve existing properties, links, and confirmed status on updates.
3. Verify the written blocks and relationships when access permits; report any
   content that could not be rendered or represented by the available tool.
4. Return the confirmed page link, or a clearly labeled Markdown draft and the
   remaining transfer work. Import may need native adjustment; do not promise
   that Markdown reproduces databases, toggles, or page properties exactly.

Naming Notion does not authorize changing permissions, notifying people, or
reorganizing a workspace.

## Platform Reference

See Notion's guidance on
[headings, dividers, and simple tables](https://www.notion.com/help/columns-headings-and-dividers)
and [databases](https://www.notion.com/help/intro-to-databases).
Verify current help before giving exact UI instructions.
