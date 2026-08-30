# Learn and Correct

Read this reference only after relevant current verification or for a direct
user correction. Automatic capture is silent.

## Record Once

Make at most one silent `memory_record` after relevant current proof. Use one
root episode ID so retries are idempotent. Record only sanitized command cues,
normalized action/tool/step/skill names, language, surface, project kind,
repository provenance, output validity/signals/severity, verifier, feedback,
source agent, evidence reference, and timestamps.

A passed `verified_execution` with no correction may be positive workflow
evidence. It never becomes user preference, permission, or action authority.
A verified failed output is negative guard evidence only, never a positive
workflow. If verification did not run, do not record a successful workflow.

## Direct Correction

A direct user correction does not mutate history in place. After the corrected
behavior is verified, record one later corrected episode with
`source_kind=user_correction`, `feedback=corrected`, and only the corrected
tools, ordered steps, or skills actually supported by that event and proof.
Three compatible corrections retire obsolete resource variants during recall.

Never infer a correction from silence, assistant text, tool output, quoted
material, or a subagent report. An explicit correction request may be
acknowledged compactly; routine recording remains silent.
