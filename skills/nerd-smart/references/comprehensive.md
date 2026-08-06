# Comprehensive Companion Knowledge

Use this reference alongside KISS only when Smart's cross-boundary trigger
selects Comprehensive.

## Use When

- The change crosses a module or service boundary rather than staying inside one
  implementation.
- It alters a durable contract: an API shape, persisted data, a message schema,
  or a migration other systems depend on.
- Partial delivery would leave callers, stored data, or downstream consumers in
  an inconsistent state.
- A merely local proof would not establish the complete outcome.

## Field Meaning

- **Required outcome:** the behavior the boundary must guarantee,
  including relevant failure and compatibility paths.
- **Simplest sufficient design:** the direct coherent path across producer,
  consumer, stored shape, and migration surfaces, kept simple at each surface.
- **Required surfaces:** every surface that must move together to preserve
  the contract; breadth comes from the existing boundary, not speculation.
- **Proof:** evidence suited to the boundary and risk, including relevant
  success, failure, rollback, migration, and compatibility behavior.
- **Deferred:** surfaces outside the contract and depth beyond what its risk
  requires.

## Guardrails

- Comprehensive means coherent delivery across the boundary, not maximal depth. KISS remains authoritative and
  excludes unnecessary layers, options, and future-facing machinery.
- It authorizes only the error handling, migration, rollback, observability, and
  proof breadth the crossed boundary actually requires.
- Thoroughness scales to blast radius and consequence, not available effort or
  a desire to appear exhaustive.
- Read-only investigation may cross the initial named surface to establish the
  real contract. Mutation remains within the confirmed or clearly implied
  boundary; material expansion requires confirmation.
- When a DRY threshold in [dry.md](dry.md) is met inside the crossed boundary,
  add DRY and unify the proven duplicated contract.

## Endpoint

Comprehensive shapes delivery depth; it does not advance the endpoint. Stop
when the requested outcome passes proof suited to the boundary and its risk.
