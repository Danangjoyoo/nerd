# GitHub Pull Request Inline Review

## Select the Tool and Diff

Prefer the connected GitHub tool whose schema supports inline review comments.
For example, when available, `add_review_to_pr` takes `repo_full_name`,
`pr_number`, `commit_id`, `action`, `review`, and `file_comments`. Inspect the
current schema rather than assuming these capabilities exist in every session.
A top-level issue/PR comment operation does not place inline diff feedback.
Use an authenticated API/CLI or browser only when the connector is insufficient.

Read the PR metadata, current head SHA, base-to-head diff, changed paths, and
existing reviews/threads. Anchor each surviving finding to the smallest relevant
changed range. The old and new file line numbers are different coordinate systems.

## Prepare and Submit

1. Finish Review's evidence and severity checks. Draft a compact body per cause:
   `[Severity] title`, triggering condition, observable impact, and correction
   outcome. Include source proof when the surrounding hunk is insufficient.
2. Map `path`, `line`, and `side`: RIGHT for the new side, LEFT for the old side.
   For supported ranges add `start_line` and `start_side`. When a tool instead
   requires `position`, derive it from that file's actual diff; it is not the
   source-file line number. Do not pass incompatible coordinate alternatives.
3. Pin the reviewed `commit_id`. Re-fetch the PR head before writing; if it
   changed, re-evaluate affected findings and recompute anchors.
4. When posting is authorized, submit supported inline comments together in a
   COMMENT review with a short summary. Use APPROVE or REQUEST_CHANGES only when
   the user requested that review action; severity alone does not authorize it.
   A REST pending review requires a later submission; an API creation response
   alone does not establish a published review.
5. Read back the review and its inline comments. Check commit, path, side/range,
   body, and submission state. Return actual review/comment links and counts.

Use the current [review API](https://docs.github.com/en/rest/pulls/reviews)
and [review-comment API](https://docs.github.com/en/rest/pulls/comments).

## Example and Fallback

Example connector payload fragment; identifiers must come from the current PR:

```json
{
  "action": "COMMENT",
  "commit_id": "<reviewed-head-sha>",
  "review": "One expiry-contract finding.",
  "file_comments": [{
    "path": "src/download.ts", "line": 42, "side": "RIGHT",
    "body": "[High] Expired downloads remain accessible. At now == expiresAt this branch still returns the file, violating R3. Enforce denial at the boundary."
  }]
}
```

Inspect existing threads before retrying an ambiguous submit. Reply to a relevant
thread rather than duplicating a cause when that reply is authorized. If a valid
diff anchor is unavailable, retain a draft with path/range and reviewed SHA;
use a clearly labeled summary comment only if allowed. Never attach to an
unrelated changed line just to make posting succeed. Do not resolve threads,
merge, edit source, or request reviewers as a side effect of posting findings.
