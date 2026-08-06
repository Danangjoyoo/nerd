# KISS Principle Knowledge

Use this reference when the selection table resolves to KISS.

## Use When

- The change is local and no other scale principle has decisive evidence. KISS
  is the default scale principle.
- The change does not cross a module or service boundary and does not alter a
  durable contract or data shape; if it does, select Comprehensive instead.
- The work is not a one-off script carrying speculative surface; if it is,
  select YAGNI instead.
- The behavior lives at one or two call sites. When a DRY threshold in
  [dry.md](dry.md) is met, add DRY and state the pair as `KISS + DRY`.
- The future shape of the requirement is unclear, contested, or unstated.
- A correct, obvious solution already exists on a direct path through existing
  code.

## Field Meaning

- **Required outcome:** the smallest observable behavior that must change,
  stated without reference to structure.
- **Smallest change:** the most direct existing path, preferring fewer concepts,
  files, dependencies, and changed boundaries over elegance.
- **Proof:** the nearest focused check that demonstrates the outcome.
- **Not needed:** speculative abstractions, refactors, infrastructure, and
  future features excluded from this change.

## Guardrails

- KISS is structural, not temporal. It answers what the simplest correct shape
  is now, not what will be needed later.
- KISS may leave duplication in place only below every DRY threshold in
  [dry.md](dry.md).
  - At one or two call sites inside a single module, record the accepted
    trade-off rather than pre-abstracting.
  - At three or more, DRY composes with KISS and the call sites are unified,
    however small the edit at each site happens to be.
  - A one-line change repeated three times is duplication, not a local change.
- The duplicated-contract exception survives KISS.
  - Two independently maintained copies of one contract across a module or
    service boundary add DRY even though the count is only two, so `KISS + DRY`
    is correct there.
  - Never use the "one or two call sites" allowance to skip that case.
- Simplicity never overrides correctness, security, or an explicit requirement.
  A solution that is simpler because it is wrong is not KISS.

## Endpoint

- KISS shapes the change; it does not advance the endpoint.
- Stop when **Proof** passes and treat **Not needed** as out of scope.
