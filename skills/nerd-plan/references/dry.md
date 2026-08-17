# DRY Modifier Knowledge

Use this reference when Nerd Plan's duplication trigger adds DRY. DRY composes with
KISS and Comprehensive when applicable; never state it on its own.

## Use When

At least one threshold is met:

- **Rule of three:** the same behavior already exists at three or more call
  sites in the confirmed scope.
- **Duplicated contract:** two or more independently maintained copies of one
  contract sit across a module or service boundary and will drift apart without
  a single owner.

The duplicated-contract case is the only exception to the rule of three because
divergence across a boundary is a correctness defect. DRY requires observed
existing duplication, never predicted duplication.

## Field Meaning

- **Required outcome:** the complete behavior that must remain consistent
  everywhere it appears.
- **Simplest sufficient design:** one clear source of truth plus every proven
  duplicated call site unified onto it.
- **Required surfaces:** the named call sites and contract surfaces that
  must move together.
- **Proof:** evidence that fails when any unified call site diverges
  and covers material compatibility behavior.
- **Deferred:** unrelated lookalike code, unproven future callers, and
  generalization beyond the observed duplication.

## Guardrails

- DRY is about one source of truth for one behavior, not textual similarity.
  Code that changes for different reasons stays separate.
- Two occurrences inside one boundary are insufficient. Record the accepted
  duplication instead of predicting a third caller.
- Do not build a framework, plugin system, or configuration layer around the
  extracted behavior. Extract exactly what is proven shared.
- Unifying call sites can widen blast radius. Confirm first when it would change
  authorized behavior or materially expand the mutation boundary.

## Endpoint

DRY shapes structure; it does not advance the endpoint. Stop when the requested
outcome passes proof suited to the affected call sites and risk.
