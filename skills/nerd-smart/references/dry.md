# DRY Principle Knowledge

Use this reference when Step 1 of principle selection adds DRY. DRY is not a
scale principle; it composes with the selected KISS, YAGNI, or Comprehensive and
is always stated as a pair, such as `Comprehensive + DRY`. Never state DRY on
its own.

## Use When

- At least one of these two thresholds must be met. There is no third trigger.
  - **Rule of three.** The same behavior already exists at three or more call
    sites in the confirmed scope, and the evidence is observed rather than
    predicted.
  - **Duplicated contract.** Two or more independently maintained copies of one
    contract sit across a module or service boundary and will drift apart
    without a single owner. Count copies, not boundaries: two copies on either
    side of a single boundary already meet this threshold.
- The duplicated-contract threshold is the only exception to the rule of three.
- It exists because divergence across a boundary is a correctness defect, not a
  style preference.
- Everywhere else, two occurrences are not enough.

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

- DRY is about a single source of truth for one behavior, not about removing
  textual similarity. Code that looks alike but changes for different reasons
  must stay separate.
- DRY requires proven existing duplication.
  - Predicted duplication and an anticipated third caller are never sufficient.
  - A second occurrence is not sufficient either, unless it is the
    duplicated-contract case above, where two independently maintained copies
    across a module or service boundary do meet the threshold.
  - When no threshold is met, omit DRY and record the trade-off instead.
- DRY is not a licence to build a framework, plugin system, or configuration
  layer around the extracted behavior. Extract exactly what is shared.
- Unifying call sites can widen blast radius. When unification would change
  behavior at any call site, say so and confirm before proceeding.

## Endpoint

- DRY shapes the change; it does not advance the endpoint.
- Stop when **Proof** passes and treat **Not needed** as out of scope.
