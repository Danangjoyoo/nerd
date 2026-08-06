# DRY Principle Knowledge

Use this reference when the selection table resolves to DRY. DRY is not a scale
principle; it composes with the selected KISS, YAGNI, or Comprehensive and is
stated as a pair, such as `Comprehensive + DRY`.

## Use When

- The same behavior already exists at three or more call sites in the confirmed
  scope, and the evidence is observed rather than predicted.
- One requested behavior change must be applied in several places to be correct,
  so partial application is a realistic defect.
- A contract crosses module or service boundaries and its copies will drift
  apart without a single owner.

## Field Meaning

- **Required outcome:** the behavior that must become consistent everywhere it
  appears.
- **Smallest change:** the single source of truth being introduced or reused,
  plus every call site being unified onto it. Name the call sites; an unnamed
  set is not evidence.
- **Proof:** a focused check that fails when any one call site diverges from the
  shared behavior.
- **Not needed:** call sites deliberately left alone, and generalization beyond
  the observed duplication.

## Guardrails

DRY is about a single source of truth for one behavior, not about removing
textual similarity. Code that looks alike but changes for different reasons must
stay separate.

DRY overrides KISS only on proven existing duplication. Predicted duplication,
a second occurrence, or an anticipated third caller is not sufficient; choose
KISS and record the trade-off instead.

DRY is not a licence to build a framework, plugin system, or configuration layer
around the extracted behavior. Extract exactly what is shared.

Unifying call sites can widen blast radius. When unification would change
behavior at any call site, say so and confirm before proceeding.

## Endpoint

DRY shapes the change; it does not advance the endpoint. Stop when **Proof**
passes and treat **Not needed** as out of scope.
