# Loop Profiles and Routes: Persistence

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Loop Profiles and Routes router](index.md) and load it only for its named trigger.

## State and Persistence Classes

Select state separately so one needed receipt does not force an otherwise tiny
task into a heavyweight program.

| Class | State | Typical profiles | Requirement |
| --- | --- | --- | --- |
| `S0` | No loop state | D0 | Working context and final proof only |
| `S1` | Compact in-session state | L1–L2 | DoD, focus, evidence, and next discriminating step |
| `S2` | Durable single-writer state | L3, single-owner L4, or durable lower-tier route | Checkpoint, causal events, resume cursor, effect receipts |
| `S3` | Transactional/fenced state | Shared-resource ownership or consequential multi-writer effects at L3/L4 | Expected revision, ownership epoch, idempotency, recovery protocol |

Raise the state class without raising the full profile when only persistence is
needed. Raise the profile when persistence interacts with coordination,
uncertainty, risk, or multiple back edges.

Likewise, L4 does not automatically force S3: coupled contracts, noisy success,
or a hard-to-reverse single-owner program may remain S2. Raise to S3 when
shared ownership or consequential writers actually require transactional
claims and resource fencing.

Do not make `effect_reconciliation` a universal S2 tax. Require it for S3, an
external-receipt or staged-rollout signal, or a route such as `pr_delivery`
whose remote effect can become ambiguous. A plain durable single-writer
checkpoint remains valid without it.

Creating an unrequested persistent artifact may cross the user's authority
boundary. Prefer a host-provided private state store; ask before adding
repository files or durable infrastructure that the endpoint did not imply.
