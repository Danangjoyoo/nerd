# Nerd Pilot — Handover Continuation Case

Continue the Nerd Context work described in
`docs/specs/nerd-context-handover.md`.

The previous session's Context ID is
`ctx_223twgnc7h5wvublifm2hexampledoesntmatteri`. This ID is **not** present
in the local Context store — treat it as `not_found`.

The user now asks:

> Resume where we left off and pick the smallest choice-changing unknown
> from the handover. Do not modify any files.

Follow these mandatory skills in this order and surface each step as a
labelled block in the final response:

1. `/nerd-smart` — output your **Focus Record** as the first block, as a
   Markdown block-quote with all four labelled fields exactly like this:

   > **Focus Record**
   > - **Intention:** ...
   > - **Expectation:** ... (one endpoint from the Endpoint Mapping:
   >   Discuss / Ideate / Explore / Diagnose / Review / Specify /
   >   Document / Plan / Execute / Monitor)
   > - **Scope:** ...
   > - **Role:** ...

2. `/nerd-memory` — perform the memory-blind Focus Record step first,
   then note Memory as advisory only.
3. `/nerd-context` — recognize the given `ctx_` as unknown, refuse to
   search or substitute, treat as `not_found`, then create a fresh
   Context by omitting the ID and print the receipt
   `Nerd-context created: <new-context-id>` using the runtime-generated
   ID from `context_recall`.

Then identify the single smallest choice-changing unknown from the
handover.

Do not modify any files. Do not run destructive commands. Return your
answer in Markdown.
