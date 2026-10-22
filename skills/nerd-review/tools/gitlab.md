# GitLab Merge Request Inline Review

## Select the Tool and Diff Version

Prefer a connected GitLab tool that supports positioned MR discussions; inspect
its schema and the GitLab instance/version. Otherwise use an already-authenticated
API/CLI or available browser. Confirm host, project ID or encoded project path,
and merge request IID. The project-local IID is not the global merge request ID.

Read the latest MR diff version and existing discussions. Use its
`base_commit_sha`, `start_commit_sha`, and `head_commit_sha` together; do not mix
SHAs from different diff versions. Read the old/new file paths and hunk lines.

## Prepare and Submit

1. Review the delta and prepare one severity-ranked finding per cause, including
   the trigger, concrete impact, and smallest correction outcome.
2. Map the latest version's SHAs to `position.base_sha`, `position.start_sha`,
   and `position.head_sha`. For text, set `position.position_type` to `text`
   and include `old_path` and `new_path`. For added lines set `new_line`; for
   removed lines set `old_line`; unchanged context uses both matching numbers.
3. When posting is authorized, create a positioned discussion through
   `POST /projects/:id/merge_requests/:merge_request_iid/discussions`, or the
   connector equivalent. Keep the finding in `body`. Use the documented
   `line_range` structure only when a multi-line anchor is actually needed.
4. Re-check the diff version before writing. If new commits arrive, re-evaluate
   the finding and remap its position rather than reusing stale coordinates.
5. Retrieve the discussion, verify its position and body, and preserve returned
   discussion/note IDs plus an actual link or host/project/MR locator.

GitLab documents positioned discussions and their coordinates in the
[Discussions API](https://docs.gitlab.com/api/discussions/) and diff versions in
[the Merge requests API](https://docs.gitlab.com/api/merge_requests/).

## Example

Illustrative request body for a verified added line; substitute observed values:

```json
{
  "body": "[High] Expiry equality still permits download. When now equals expiresAt the added branch returns file content, contrary to R3. Deny access at the expiry boundary.",
  "position": {
    "position_type": "text",
    "base_sha": "<base-commit-sha>",
    "start_sha": "<start-commit-sha>",
    "head_sha": "<head-commit-sha>",
    "old_path": "src/download.ts",
    "new_path": "src/download.ts",
    "new_line": 42
  }
}
```

## Fallback and Retry

A generic MR note or unpositioned discussion is not an inline diff comment.
If the available tool cannot position comments, prepare a draft with exact diff
version, path, side/line, and body. Use a general note only when the instruction
allows that delivery. If a write result is ambiguous, inspect discussions before
retrying; after partial success, retry only confirmed missing comments. Do not
approve, merge, resolve discussions, or change the MR state through a review
comment operation. Report verified posted comments and any unposted findings.
