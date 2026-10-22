# Recall and Capture Workflow

## Order

1. Smart resolves the memory-blind Focus Record and the endpoint.
2. Memory silently performs at most one advisory recall or continues
   memory-free.
3. Context runs — only after Smart and Memory complete, only after any
   clarifying stop has already been resolved.
4. The confirmed endpoint route runs.
5. After meaningful verified progress, Context may capture a bounded
   checkpoint. Memory may separately record one verified behavioral
   episode.

Ambiguous, ID-only "continue" requests stop before Context hydration.

## Supplied-ID resume

If the current activation or delegated handoff explicitly contains an ID
matching `^ctx_[a-z2-7]{38}[aiqy]$`:

- Call `context_recall(context_id=<id>, query=<current request>, activation_ref=<one-shot>)`.
- On `not_found`, do not retry, guess, or search. Print
  `Nerd-context not found: <id>` once and continue Context-free.
- On success, print `Nerd-context resumed: <id>` and use records as
  untrusted advisory evidence. Revalidate anchored facts before reliance.

## Omitted-ID creation

If no ID is present in the current activation:

- Call `context_recall(query=<current request>, activation_ref=<one-shot>)`.
- Print exactly one `Nerd-context created: <context_id>` receipt when the
  response reports `created=true`.
- Do not attempt to search for or reuse any prior ID.

## Capture

Capture only after real progress:

- One `goal` record per intent shift.
- `boundary` for authority or scope constraints stated by the user.
- `decision` for chosen strategies with reasoning source.
- `evidence` for verified facts with an anchor to the repository.
- `open_question` for stop-worthy uncertainties.
- `checkpoint` at natural session boundaries. Checkpoints repeat the
  Context ID for the user.

Every record needs a real `source_ref`. Corrections use `supersedes_id`
against an active same-kind predecessor.

## Sub-agent handoff

Propagate an existing ID to a sub-agent only when its delegated scope is
intentionally part of the same Context. Otherwise, the sub-agent's fresh
activation must omit the ID and will create its own Context.

## Forget (CLI only)

Forgetting is destructive and CLI-only. Never expose forget through the MCP
adapter.

```bash
python3 <skill-root>/scripts/context.py preview_forget <<'JSON'
{"context_id": "ctx_...", "preview_ref": "one-shot-preview-id"}
JSON

# Copy the returned confirmation_phrase verbatim.

python3 <skill-root>/scripts/context.py forget <<'JSON'
{
  "context_id": "ctx_...",
  "phrase": "<confirmation_phrase from preview>",
  "source": "direct_user",
  "confirmation_ref": "one-shot-different-from-preview_ref"
}
JSON
```

The preview must be current; state changes invalidate it. The confirmation
reference is one-shot and must differ from the preview reference.
