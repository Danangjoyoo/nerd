# Comprehensive Principle Knowledge

Use this reference when the selection table resolves to Comprehensive.

## Use When

- The change crosses a module or service boundary rather than staying inside one
  implementation.
- It alters a durable contract: an API shape, a persisted data shape, a message
  schema, or a migration other systems depend on.
- Partial delivery would leave callers, stored data, or downstream consumers in
  an inconsistent state.
- KISS and YAGNI would under-build the outcome, not simplify it.

## Field Meaning

- **Required outcome:** the whole behavior the boundary must guarantee,
  including the failure paths, not only the success path.
- **Smallest change:** the complete set of surfaces the contract touches —
  producer, consumer, stored shape, and migration — kept minimal per surface but
  never left partial.
- **Proof:** coverage proportionate to blast radius: the success path, the
  relevant failure and rollback paths, and compatibility for existing callers or
  stored data.
- **Not needed:** surfaces outside the contract, and depth beyond what the
  boundary requires.

## Guardrails

Comprehensive licenses completeness, never speculation. It authorizes the error
handling, migration, rollback, observability, and test breadth the architectural
change already requires. It does not authorize plugin systems, configuration
layers, or extension points for hypothetical futures; those remain YAGNI
material regardless of how architectural the task feels.

Thoroughness is scaled to blast radius, not to effort available. State the
boundary the change crosses and let that boundary set the depth. If no boundary
is actually crossed, the selection was wrong and KISS applies.

Comprehensive composes with DRY. When a DRY threshold in [dry.md](dry.md) is met
inside the crossed boundary, state `Comprehensive + DRY` and unify those call
sites as part of the same change. A contract duplicated across two or more
boundaries meets that threshold, which is common in exactly the changes that
select Comprehensive.

Breadth is not licence to widen scope. Every surface named must belong to the
contract in the confirmed Focus Record scope.

## Endpoint

Comprehensive shapes the change; it does not advance the endpoint. Stop when
**Proof** passes and treat **Not needed** as out of scope.
