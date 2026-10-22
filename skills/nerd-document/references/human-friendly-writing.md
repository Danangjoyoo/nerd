# Human-Friendly Writing

## Start with the Reader's Job

Identify what the reader must understand, decide, find, or do. Write the opening
to serve that job. Reuse supplied audience and purpose; ask only when the answer
would materially change the document. Never demand a questionnaire for a clear
request.

Put information in this order when it fits:

1. The result, decision, request, or current state.
2. The few facts that explain it.
3. The required action, owner, and timing, when established.
4. Supporting details and evidence.

Keep a useful exception beside the rule it qualifies. A shorter document that
omits a release blocker or recovery step is less useful than a longer clear one.
Illustrative examples below are fictional; never copy their facts into a real
artifact unless the user's sources establish them.

## Choose a Structure That Carries Meaning

| Structure | Good use | Avoid |
| --- | --- | --- |
| Bullets | Independent requirements, benefits, constraints, or findings | A paragraph split at arbitrary sentence boundaries |
| Numbered points | Steps, priorities, ranked choices, or stable numbered requirements | Implying order among unrelated facts |
| Tables | Repeated fields, comparisons, status registers, or lookup | Paragraphs squeezed into cells; one-row decorative tables |
| Headings | Topics the reader will seek or questions they need answered | Vague labels such as “Other” or a heading for every sentence |
| Paragraphs | Explanation, cause, consequence, and trade-offs | Several unrelated ideas in one block |
| Breaks | Whitespace between ideas; page/slide breaks at a real boundary | Empty pages, repeated horizontal rules, or manual spacing hacks |

Keep list items parallel: start each step with a verb and each requirement with
the same kind of subject. Prefer shallow lists. Promote a deeply nested topic to
a heading when it needs its own explanation. Use consistent terms throughout.

In Markdown, leave blank lines before lists and around headings and tables.
Use a fenced block for code, commands, or exact output. In native platforms,
use real heading, list, and table structures rather than simulating them with
spaces or bold text. Do not rely on color alone for status.

## Example: Put the Decision First

Weak:

> Over the last several weeks, the team has been working on several parts of
> the export project, and after multiple discussions there are some things
> that need to be addressed before we can move forward with the launch.

Better:

> The export launch is blocked by a tenant-isolation defect. Engineering must
> fix the defect and QA must rerun the isolation tests before release approval.

The revision names the state, reason, and required action. Add dates or owners
only when known; otherwise label that gap where it affects the decision.

## Example: Use Bullets for Scope

Weak:

> The feature will support CSV files and account administrators, and it will
> also include expiring download links but not scheduled or PDF exports.

Better:

```markdown
## Release Scope

- Account administrators can request a CSV export.
- Download links expire after 24 hours.
- Scheduled exports and PDF output are out of scope.
```

These are peer facts, so bullets help readers scan them without implying order.

## Example: Use Numbers for a Procedure

Weak:

> You can obtain a file from Exports after selecting an account and asking
> the service to generate the report, then check that the output is right.

Better:

```markdown
## Download an Account Export

1. Open the account's **Exports** page.
2. Select **Request CSV**.
3. Wait until the export status is **Ready**.
4. Download the file and confirm its account ID matches the selected account.

If the status is **Failed**, use the error code in the export reference before
requesting another export.
```

Use the real interface labels and recovery behavior from supplied evidence.

## Example: Use a Table for Repeated Attributes

Weak:

> CSV is supported for administrators. PDF is not available. Scheduled exports
> are also unavailable, but one-time exports are supported for administrators.

Better:

| Capability | Available in this release | Who can use it |
| --- | --- | --- |
| One-time CSV export | Yes | Account administrators |
| PDF export | No | Not applicable |
| Scheduled export | No | Not applicable |

Columns expose the comparison. Do not add more columns than the decision needs.

## Example: Make Headings Useful

Weak outline: “Introduction,” “Details,” “More Details,” “Conclusion.”

Better outline for an export guide:

1. Who Can Export Data
2. Request and Download an Export
3. Resolve Failed or Expired Downloads
4. Export Fields and Limits

Keep heading levels consistent and avoid skipping levels for visual effect.
Add a contents list when readers need to jump through a long document. Use
section breaks for real topic changes; use short paragraphs within a topic.

## Example: Separate a Fact from an Open Question

Weak:

> Exports should probably finish quickly and old files will be cleaned up.

Better:

| Item | Confirmed information | Gap and consequence |
| --- | --- | --- |
| Completion time | No target supplied | Unknown; performance acceptance cannot be assessed |
| Download expiry | Link expires after 24 hours | Confirmed requirement R3 |
| File deletion | No retention policy supplied | Unknown; storage lifecycle cannot be finalized |

Expiry and deletion are different behaviors. Do not silently infer one from the
other. Link actual source requirements in a real artifact.

## Example: Turn a Vague Update into an Actionable One

Weak: “We are making good progress, but there are a few dependencies.”

Better:

```markdown
## Status: At Risk

The export workflow is implemented. Security review is still pending and blocks
release approval.

- **Completed:** Request, status, and download flows passed integration tests.
- **Blocked:** Tenant-isolation review has no assigned reviewer.
- **Decision needed:** Engineering lead to assign a reviewer before scheduling release.
```

## Editing Pass

1. Read only the opening and headings. Can the reader identify the point and
   find the part they need?
2. Remove repeated background, filler, and facts that do not change an action,
   decision, understanding, or necessary record.
3. Check whether bullets, numbers, or a table make dense prose easier to scan.
   Keep prose when the explanation depends on connected reasoning.
4. Replace vague qualifiers with established evidence or an explicit unknown.
5. Check examples against the document's rules, units, names, and status.
6. Verify links, remove unused template instructions, and inspect the delivered
   format when possible. Never claim render verification from source inspection.
