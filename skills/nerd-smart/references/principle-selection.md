# Plan and Execute Principle Selection

## Use When

Use this reference only after the active endpoint resolves to Plan or Execute.
When a goal queue exists, select from only the active goal's evidence. Never use
this reference for another endpoint or select one principle for an entire queue.

## Selection

Selection has two independent steps. Run both in order and load only the
selected principle references. DRY is never selected on its own.

### Step 1 — Test DRY

DRY is a composable modifier, not a scale principle. Add it when either threshold
is met in the confirmed scope; otherwise omit it.

| DRY threshold | Applies when |
| --- | --- |
| Rule of three | The same behavior already exists at **three or more** call sites. |
| Duplicated contract | **Two or more independently maintained copies** of one contract sit across a module or service boundary and will drift apart without a single owner. |

The duplicated-contract threshold is the only exception to the rule of three,
because divergence across a boundary is a correctness defect rather than a
style preference. Count copies, not boundaries: two copies on either side of a
single boundary meet it. Below both thresholds, omit DRY and record the accepted
trade-off. DRY requires proven existing duplication, never predicted
duplication, and edit size never overrides the count. See [dry.md](dry.md).

### Step 2 — Choose One Scale Principle

KISS, YAGNI, and Comprehensive are mutually exclusive:

| Order | Condition observed in the confirmed scope | Principle | Reference |
| --- | --- | --- | --- |
| 1 | Default: a local change that crosses no boundary | **KISS** | [kiss.md](kiss.md) |
| 2 | A one-off script, throwaway automation, or glue code carrying speculative features, configuration, or extension points | **YAGNI** | [yagni.md](yagni.md) |
| 3 | The change crosses modules or services, or alters a durable contract or data shape | **Comprehensive** | [comprehensive.md](comprehensive.md) |

When two rows appear to hold, take the later row and record the rejected one as
an accepted trade-off. State the scale principle alone, such as `KISS`, or pair
it with DRY when Step 1 applied, such as `KISS + DRY` or `Comprehensive + DRY`.
Never state `DRY` by itself.

YAGNI never removes work required by an approved architectural outcome, explicit
requirement, or correctness or security constraint. Comprehensive never licenses
speculative features; it licenses only the failure handling, migration,
observability, and test breadth the architectural change already requires.

## Principle Breakdown

The selected principle is subordinate to Focus and never replaces or abbreviates
it. Show the current resolved Focus Record immediately before this breakdown in
the same response or artifact. Derive every field from that record without
changing its intention, expectation, scope, or role, then proceed without
another confirmation when clear:

> **Principle Breakdown**
> - **Principle:** [KISS, YAGNI, or Comprehensive, optionally combined with DRY, plus the deciding evidence]
> - **Required outcome:** [Smallest observable behavior that must change]
> - **Smallest change:** [Most direct path under the selected principle]
> - **Proof:** [Focused check that demonstrates the outcome]
> - **Not needed:** [Speculative abstractions, refactors, infrastructure, or future features]

If a template contains the breakdown but omits the Focus Record, insert the
complete Focus Record before it. Treat **Not needed** as out of scope and stop
when **Proof** passes.
