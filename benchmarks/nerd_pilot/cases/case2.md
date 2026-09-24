# Nerd Pilot — Lexical Candidate Review Case

Review the bounded lexical (identifier-token) candidate result recorded in
`docs/specs/nerd-context-handover.md`.

The previous session's Context ID is
`ctx_lexicalfakecandidatesnapshotforbenchmarkingi`. Treat as `not_found`.

The user now asks:

> Explain what "valid-evidence PASS" actually establishes about
> production release for Nerd Context, and name the single smallest
> choice-changing unknown that would decide whether to trust the
> candidate's 100% required-recall result. Do not modify any files.

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

Then answer both parts of the question. Be honest about what
`valid-evidence PASS` does NOT authorize.

Do not modify any files. Do not run destructive commands. Return your
answer in Markdown.
