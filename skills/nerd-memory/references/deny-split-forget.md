# Deny, Split, and Forget

Read this reference only after a denial or for denial resolution, contextual
splitting, or forgetting.

## Deny a Recommendation

Pass only a new direct-user event to `deny` for a pending or confirmed but
unconsumed proposal. Denial atomically kills the proposal and grant. It is
evidence only that this exact recommendation was rejected; it is not a
correction, negative preference, confidence update, or memory-write authority.

In one compact paragraph, show the matched patterns, evidence, and memory-blind
baseline, then ask for one explanation: `agent_mistake` when the current route
was built incorrectly; `human_forgot` when the memory remains valid; or
`route_too_generic` when the pattern needs a durable contextual exception.

Do not infer the third explanation from frequency, confidence, or a bare no.
The first two require their generated exact resolution phrase from a fresh
direct-user event, leave patterns unchanged, and require a fresh proposal for
later action. A denial without durable scope guidance causes no memory change.

## Split a Generic Route

For `route_too_generic`, create an inert split draft targeting only patterns
with the `applied` role in the denied proposal. Retain each parent as the
recorded fallback and propose a child exception that:

- strictly specializes the parent scope;
- uses a stable, non-secret discriminator already present in trusted context;
- matches the denied case; and
- inherits the parent's operation and triggers.

Never split on episode, message, proposal, request, session, thread, timestamp,
or turn identifiers. If no stable discriminator exists, abstain and ask for
one. Show unselected applied bindings so a partial endpoint split is visible.

`Nerd-memory proposes a split: <denied proposal ID/digest; recorded parent
fallbacks, scopes, values, and evidence; strict child exceptions; unselected
bindings; exception wins by specificity while the parent remains the fallback
elsewhere; current action stays dead; memory write only; requires a fresh
endpoint proposal afterward>.
Confirm: <generated exact split-confirmation phrase>`

Apply the split only from a new direct-user event exactly matching the phrase.
Split confirmation may create explicitly confirmed children because the user
reviewed the durable rule, but it returns no endpoint, never revives the denied
proposal, and never bypasses the ordinary proposal gate. Apply all children
atomically or none.

## Forget a Lineage

Use `preview-forget` and show the exact root, descendant cascade, evidence
counts, dependent proposal/split/denial summaries, effect, backup limitation,
and generated phrase in one compact paragraph. Forget only from a new
direct-user event exactly repeating the current phrase.

Then atomically tombstone the lineage, remove its unshared direct evidence,
destroy bound proposals and grants, and redact dependent denial/split records.
Forgetting a parent includes descendants; forgetting one child preserves its
parent and siblings. Do not claim erasure from backups or external systems the
runtime cannot control.

Any intervening evidence, consent, lineage, or proposal change invalidates the
preview. Preserve global trusted-event replay tombstones so deletion cannot
make an old event reusable.

After a successful denial resolution, split, or forget operation, output only
the one-paragraph `Nerd-memory memorized:` receipt defined in `SKILL.md`.
