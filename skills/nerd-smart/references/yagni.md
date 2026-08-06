# YAGNI Principle Knowledge

Use this reference when the selection table resolves to YAGNI.

## Use When

- The work is scripting: a one-off script, throwaway automation, or glue code
  with no durable contract and no downstream consumer. Outside scripting work,
  select KISS or Comprehensive instead.
- That scripting task carries speculative features, configuration, extension
  points, or backends the confirmed outcome does not require.
- The justification for extra surface is a possible future need rather than a
  stated requirement or observed evidence.
- Removing the speculative surface leaves a complete, correct answer to the
  confirmed outcome.

## Field Meaning

- **Required outcome:** the behavior the confirmed outcome actually requires,
  stated without the speculative surface.
- **Smallest change:** the direct implementation of that behavior only.
- **Proof:** a focused check on the required behavior; deferred surface has
  nothing to prove.
- **Not needed:** the primary field. List each deferred feature, option, hook,
  or abstraction explicitly, so the decision is visible rather than silent.

## Guardrails

YAGNI is temporal, not structural. It answers whether to build something now,
while KISS answers what shape to build.

YAGNI never removes work required by an approved architectural outcome, an
explicit requirement, an established repository convention, or a correctness,
security, or measured performance constraint. Reserve it for scripting work. A
change that crosses a module or service boundary, or alters a durable contract
or data shape, selects Comprehensive instead, however small it looks.

Deferral is a recommendation, not a silent deletion. When the user asked for the
speculative surface directly, state the mismatch and the recommended reduction
and ask once before dropping it.

Asking never replaces the deliverable. Produce the breakdown and the endpoint's
output for the required behavior in the same response, list every deferred item
under **Not needed**, and put the question after them. A response that only
raises the objection has skipped the endpoint.

## Endpoint

YAGNI shapes the change; it does not advance the endpoint. Stop when **Proof**
passes and treat **Not needed** as out of scope.
