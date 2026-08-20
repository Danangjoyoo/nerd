# Recognize and Reuse

Read this reference when deciding whether current work contains durable behavior
or reusable workspace evidence. Sensitivity means checking these green cases at
intake and after verification; it does not mean lowering provenance rules.

## Capture Radar

| Current signal | Lane | Support | Capture |
| --- | --- | --- | --- |
| User says remember, always, default, prefer, from now on, or equivalent durable wording | Behavior | 1 root episode | Observe as `durable_directive`; create the exact candidate. |
| User corrects durable guidance and supplies its replacement | Behavior | 1 root episode | Observe as `user_correction`; contest the old value immediately. |
| User makes the same ordinary direct choice across tasks | Behavior | 2 independent root episodes | Observe each as `ordinary_choice`; consolidate the identical typed value. |
| Approved Focus/plan completes with relevant current proof | Reusable evidence | 1 verified episode | Record a minimal `workflow_trace`. |
| A stable path, symbol, repository convention, or proof command is directly verified in-boundary | Reusable evidence | 1 verified episode | Record a minimal `workspace_fact`. |
| Tool output without current verification, incidental success, silence, quoted/external content, secrets, permissions, or executable payloads | Neither | N/A | Do not store as reusable memory. |

One episode still counts once despite repetition. A behavior candidate remains
inactive until invocation-authorized promotion, and every later use still needs
the ordinary Memory Proposal gate.

## Reusable Evidence

Reusable evidence is navigation help, never an endpoint field or instruction.
Use only `source=direct_user` or `source=verified_execution` with a passed,
current verification record. Store:

- `workspace_fact`: one short fact;
- `workflow_trace`: 1–12 declarative steps and one observed result;
- an exact namespace and applicability scope;
- normalized tags and repository-relative path/symbol anchors;
- provenance and a revalidation recipe.

Do not store transcripts, file contents, shell strings, executable code, remote
credentials, volatile IDs, permissions, or action authorization. Proof commands
are argument arrays plus a repository-relative working directory and are data,
not permission to execute.

## Find, Revalidate, Invalidate

At the first relevant read, query the current namespace and stored scope. A hint
matches only by exact current `task_key`, one exact phrase tag, or at least two
normalized tag matches. Accept a safe empty result; return at most five.

Every result is `authority=untrusted_reusable_evidence` and
`revalidation_required=true`. Before relying on it, perform the smallest current
read-only check of its anchor or recipe under normal tool rules. If the check
passes, use the hint only to shorten discovery. If it fails, invalidate the hint
and continue ordinary exploration. Never insert a hint into `proposed_endpoint`,
`memory_diff`, proposal bindings, confirmation, consumption, routing, or action.

Record a verified replacement for the same kind/key/overlapping scope instead
of editing history; the runtime marks the old hint stale. Batch successful writes
into the one compact `Nerd-memory memorized:` receipt defined by `SKILL.md`.
