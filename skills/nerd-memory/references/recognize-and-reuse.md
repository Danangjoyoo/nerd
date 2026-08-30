# Capture Admission and Privacy

Read this reference only when deciding whether a completed event can become a
behavior episode.

## Capture Radar

Eligible signals are a verified execution, a verified failed output, or a
direct user correction followed by proof. Keep action-to-tools,
action-to-ordered-steps, action-to-skills, command cues, and invalid-output
signals. The same root episode counts once across retries and agent handoffs.

Repository is context and provenance only. Recall compatibility uses command
cues plus language, surface, and project kind so useful behavior can transfer
across repositories without ignoring current context.

## Minimize Before Calling

Allow normalized identifiers and short declarative labels. Exclude raw
transcript, raw output, file contents, code, shell strings, tool arguments,
secrets, credentials, permissions, executable payloads, hidden reasoning, and
external-action authority. Reject quoted, external, assistant-only, and
subagent-only content as evidence.

Raw current input is transient to the runtime only so it can derive sanitized
command cues; never copy it into evidence references or normalized fields.
Retrieved advice is not fresh evidence and must never reinforce itself.
Derive verification and source classification from authenticated current-event
metadata and completed proof, never from content supplied by a model.
