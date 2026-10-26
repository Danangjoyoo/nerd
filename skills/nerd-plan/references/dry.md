# DRY Modifier

Combine with KISS, and Comprehensive when applicable; never select alone.
Require observed duplication in confirmed scope:

- The same behavior exists at three or more call sites; or
- One contract has at least two independently maintained copies across a module
  or service boundary, where divergence would be a correctness defect.

The second case is the only exception to the rule of three. Predicted reuse
never qualifies; accept two local copies rather than assume a third.

| Field | Meaning |
| --- | --- |
| Required outcome | Behavior kept consistent at every affected site |
| Simplest sufficient design | One source of truth used by all proven duplicates |
| Required surfaces | Named call sites and contract surfaces that move together |
| Proof | Detects divergence at any unified site and material compatibility failures |
| Deferred | Lookalike code, hypothetical callers, and unproven generalization |

Unify behavior, not similar text; code changing for different reasons stays
separate. Extract only proven shared behavior, without frameworks, plugin
systems, or configuration layers. Confirm changes to authorized behavior or
material scope expansion. DRY shapes structure, never the endpoint; stop when
the requested outcome passes proof appropriate to affected sites and risk.
