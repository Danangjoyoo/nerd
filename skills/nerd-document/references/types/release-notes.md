# Release Notes and Change Announcements

## Purpose and Boundary

Tell the intended audience what changed, why it matters to them, whether they
must act, and what limitations remain. Write from confirmed released behavior
or label the notes as a draft for an unreleased version. A merged change alone
does not prove availability to every user.

## Inputs to Preserve

- Version or release identity, availability, and release date when known.
- User-visible behavior changes and affected audience.
- Compatibility changes, migrations, deprecations, and required actions.
- Known issues and verified workarounds, where relevant.

## Suggested Structure

| Section | Include when |
| --- | --- |
| Release summary | Always; identify the release and its main benefit |
| Action required | Users must migrate, change settings, or meet a prerequisite |
| Added / changed / fixed | There are relevant user-visible changes |
| Compatibility | Behavior or contracts affect existing usage |
| Known limitations | A material limitation changes user expectations |
| Further reading | A task guide, migration procedure, or detailed reference helps |

Put required action before promotional detail. Use bullets for changes and
numbered points for migration steps. Use a compatibility table when different
versions or audiences require different action.

## Filled Example

Fictional release facts:

```markdown
# Export Release 1.0 — Draft Release Notes

Account administrators can request a one-time CSV report for reconciliation.
Release date and production availability are not yet confirmed.

## Added

- Request an account CSV from the Exports page.
- Check generation status before downloading.
- Download the completed file through a link that expires after 24 hours.

## Access and Compatibility

| Audience | Behavior | Required action |
| --- | --- | --- |
| Account administrators | Can request and download account exports | Use the new Exports page when the release is available |
| Account viewers | Export access is unavailable | Ask an account administrator for the approved workflow |

## Limitations

- Scheduled exports and PDF output are not included.
- Link expiry describes access duration; file-retention timing remains
  unresolved and must not be published as a confirmed deletion guarantee.
```

This example is draft-only because production availability is unknown. In final
release notes, include confirmed availability and resolve or accurately describe
questions that affect user-facing claims.

## Example: Required Migration Notice

When supplied release facts include a breaking field rename, use a focused table:

| Old field | New field | Required consumer action |
| --- | --- | --- |
| `download_url` | `downloadUrl` | Update response parsing for the stated API version |

Only include such a rename when established. State the affected version and
deadline if known, and link a verified migration guide. Never invent a deadline
or imply that the fictional export release includes this change.

## Writing Corrections

- Replace commit-level notes such as “refactor export service” with the
  observable benefit or omit the change if it has no relevance to the audience.
- Replace “many improvements” with named behavior changes.
- Distinguish available, gradually rolling out, deprecated, and removed using
  the actual release state.
- Never call a breaking change a small improvement or bury action in an appendix.

## Completion Check

Verify release identity, availability, audience, required actions, compatibility,
and limitations against sources. Check links to migration/how-to material.
Publishing or sending the announcement requires the user's authorization;
writing release notes alone does not provide it.
