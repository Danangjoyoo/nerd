# Comprehensive Companion

Add to KISS when work crosses modules/services, changes a durable API, data,
message, or migration contract, leaves consumers inconsistent if partial, or
needs more than local proof. Breadth follows the existing boundary, not speculation.

| Field | Meaning |
| --- | --- |
| Required outcome | Guaranteed behavior, including relevant failures and compatibility |
| Simplest sufficient design | Coherent path across producers, consumers, stored shapes, and migrations |
| Required surfaces | Surfaces that must change together to preserve the contract |
| Proof | Risk-appropriate success, failure, rollback, migration, and compatibility evidence |
| Deferred | Work outside the contract or beyond its required depth |

KISS still governs: add only necessary error handling, migration, rollback,
observability, and proof. Scale depth to consequence and blast radius.
Investigation may follow the real contract; mutation stays within confirmed or
clearly implied scope, with confirmation for material expansion. Add [DRY](dry.md)
only at its duplication threshold. This companion shapes delivery depth, never
the endpoint; stop at the requested outcome with boundary-appropriate proof.
