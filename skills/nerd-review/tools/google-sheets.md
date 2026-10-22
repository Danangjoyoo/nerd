# Google Sheets Cell Review

## Select the Tool and Anchor

Use an available Sheets connector only if its schema supports native threaded
comments on cells/ranges. A note-writing operation is not a comment thread.
For a connected Codex document session, call `list_document_sessions`, select the
exact workbook, then `get_document_tool_schemas` for its advertised operations.
Use `execute_document_command` only with those schemas and a stable per-comment
`idempotency_key`; do not assume a Sheets session advertises comments.
Otherwise use an available browser tool after reading its skill.

Identify spreadsheet ID, sheet ID/tab name, A1 range, stable row/case ID, and
current cell value/formula. Sorting and inserted rows can move a record; refresh
its position before writing. Prefer the cell that contains the defective value
or expectation over a whole-sheet anchor.

## Place the Review

1. Read the range, relevant headers/formulas, and current threads. Check units,
   displayed versus stored values, and the evidence behind the finding.
2. Draft one comment per cause, naming the row ID and consequence so it remains
   intelligible if the register moves. Use severity/title, evidence, impact,
   and a correction outcome rather than replacement cell content.
3. With a native tool, supply its documented range and comment fields. In the
   editor, select the cell/range, choose Add comment, enter the body, then submit
   when authorized. Do not edit the cell or formula to place review text.
4. Reopen the thread and confirm the intended tab, range, record ID, and body.
   Save its returned ID/link or retrievable workbook/range locator.
5. If submission times out, inspect existing comments before retrying. Re-find
   the stable row ID after any concurrent sort or structural edit.

The editor supports commenting on selected cells; see
[Google's comment instructions](https://support.google.com/docs/answer/65129).
Drive custom anchors do not render as native Sheets cell anchors; see
[Drive comment limitations](https://developers.google.com/workspace/drive/api/guides/manage-comments).
Do not construct opaque editor anchor data or present a Drive comment as inline.

## Example and Fallback

Anchor: Cases!F18, case TC-17, “Expected result”.

```text
[Medium] TC-17 cannot detect an expiry boundary regression
R3 denies downloads at expiry, but this expectation checks only HTTP success.
An expired file can still pass the case. Assert the denied response and absence
of file content using the established expiry contract.
```

If native commenting is unavailable, return a draft containing tab, range,
record ID, value/formula snapshot, and body. Do not replace comments with notes,
extra columns, or a new review tab. Post an unanchored alternative only when the
user's instruction allows it. Report the actual delivery and verification state.
