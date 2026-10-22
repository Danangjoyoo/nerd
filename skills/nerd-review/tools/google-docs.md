# Google Docs Inline Review

## Select the Tool and Anchor

Prefer an available Google Docs connector with native text-range comment support.
Inspect its actual schema; document read/write access alone does not establish
comment support. Otherwise use an available browser tool after reading its skill.
Confirm the document ID, current section, exact quote, and surrounding text.
Distinguish repeated quotes and different document tabs before selecting a range.

Google Drive's comments API stores custom anchors, but Docs treats these as
unanchored comments. Do not claim that `anchor` or `quotedFileContent` creates a
native inline selection. Use a verified editor-native operation for that result.
See [Drive comment limitations](https://developers.google.com/workspace/drive/api/guides/manage-comments).

## Place the Review

1. Read the target paragraph and existing comments. Finish the evidence check
   before preparing a comment; reply to an existing relevant thread when useful.
2. Prepare one finding per thread: severity/title, faulty claim or instruction,
   evidence, reader consequence, and smallest correction outcome. Keep it short
   enough to read in the margin; do not paste the entire review into each thread.
3. For native range-comment tools, pass only the documented document/tab/range
   identifiers from the current read. For browser use, select the exact text,
   choose Add comment, enter the body, and submit only when posting is authorized.
4. Verify that the thread opens on the intended selection and has the expected
   body. Preserve a returned comment ID/link or another retrievable locator.
5. Re-read the selection if the document changes. After an ambiguous submit
   result, inspect existing threads before retrying to avoid duplicates.

Google describes the editor operation in
[adding comments](https://support.google.com/docs/answer/65129).

## Example and Fallback

Anchor: the retention sentence in “Data lifecycle”.

```text
[Medium] Retention statement contradicts the approved policy
This sentence says exported files are kept indefinitely; policy R4 requires
removal after 30 days. Operators following this guidance would retain data
beyond the agreed period. Align the statement with R4 and link the policy.
```

If only Drive comments are available, keep the inline comment as a draft with
heading, quote, and source location. A file-level comment is a separate delivery
option; post it only if the user's instruction allows it and label it unanchored.
Never substitute document-body edits, suggestions, or permissions changes.
Report draft versus posted, anchor verification, and any remaining limitation.
