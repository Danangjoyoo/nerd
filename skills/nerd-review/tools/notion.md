# Notion Inline and Block Review

## Select the Tool and Anchor

Discover the available Notion connector and inspect its comment schema. Confirm
the target page, heading/block ID, current text, and integration access. Read
existing threads and distinguish a whole-page comment, a block comment, and a
selected-text discussion. A page update tool is not a comment operation.

The public API supports `POST /v1/comments` with exactly one target:
`parent.page_id`, `parent.block_id`, or an existing `discussion_id`. It can create
a block comment and reply to an existing selected-text discussion, but cannot
start a new selected-text thread. Use a verified native UI operation for the
latter. Follow [Notion's comment API](https://developers.notion.com/reference/create-a-comment)
and the connector's supported API version rather than inventing range fields.

## Place the Review

1. Finish the review evidence check, then anchor to the smallest relevant block
   or existing thread. Re-read its text immediately before posting.
2. Draft severity/title, specific contradiction or omission, supporting evidence,
   reader/user consequence, and smallest correction outcome. Use concise text;
   avoid formatting that the actual comment tool cannot render.
3. For a block comment, supply `parent.block_id` and supported comment content.
   For a reply, supply `discussion_id` instead of a parent. For example, a
   supported rich-text request shape is:

   ```json
   {
     "parent": {"block_id": "<verified-block-id>"},
     "rich_text": [{"text": {"content": "[Medium] Acceptance contradicts R3. At expiry, the flow still offers the file. Align the acceptance criterion with R3's denial rule."}}]
   }
   ```

4. If a new selected-text comment is required, use the available browser after
   reading its skill: select the exact text, choose Comment, and submit the body
   when authorized. Verify selection context instead of relying on a text match.
5. Retrieve the created comment/discussion or reopen it in the page. Confirm
   body and parent/thread, save the returned IDs and page/block locator, and
   distinguish block anchoring from selected-text anchoring in the result.

The UI workflow is documented in
[Notion comments](https://www.notion.com/help/comments-mentions-and-reminders).

## Fallback and Retry

If the connector only supports page comments, keep the requested inline review
as a draft with block ID, heading, exact quote, and body. Use a block/page-level
alternative only when the instruction permits that scope; label it accurately.
On uncertain submission, list existing threads before another write. Do not add
review paragraphs to page content, alter properties, resolve others' threads,
or mention/assign people without instructions. Return posted versus draft status
and verified locators; do not manufacture a comment permalink.
