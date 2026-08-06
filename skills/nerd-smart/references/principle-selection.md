# Optional Delivery Companion Selection

## Use When

Use this reference only when a Plan or Execute goal has credible evidence for
cross-boundary completeness or proven duplication and the right companion is
unclear. Routine work uses Smart's inline KISS rule and loads no principle
reference.

KISS always applies. [Extended KISS rationale](kiss.md) is available when its
meaning is disputed, not as a routine prerequisite. YAGNI's useful rule—defer
speculative surface—is folded into KISS; [legacy YAGNI rationale](yagni.md) is
retained only for that explanation and is never selected separately.

## Selection

Select from observed evidence:

| Evidence | Selection | Reference |
| --- | --- | --- |
| Work crosses modules or services, changes a durable contract or data shape, or partial delivery leaves consumers inconsistent. | **KISS + Comprehensive** | [comprehensive.md](comprehensive.md) |
| The same behavior has three or more maintained copies, or one contract has two independently maintained copies across a boundary. | **KISS + DRY** | [dry.md](dry.md) |
| Both conditions hold. | **KISS + Comprehensive + DRY** | Load both references. |
| Neither condition holds. | **KISS** | Load neither reference. |

Predicted reuse, edit size, and hypothetical future requirements are not
evidence. Comprehensive determines required delivery breadth; DRY determines
whether proven duplication needs one owner.

## Delivery Breakdown

Keep this internal for clear work. Show it only in a requested Plan, a material
handoff, or when the trade-off helps the user decide:

> **Delivery Breakdown**
> - **Approach:** [KISS plus an evidence-selected companion]
> - **Required outcome:** [Requested observable result]
> - **Simplest sufficient design:** [Direct design without accidental complexity]
> - **Required surfaces:** [Supporting work needed for correctness or integration]
> - **Proof:** [Evidence suited to behavior and risk]
> - **Deferred:** [Optional or speculative work excluded]

Deferred is provisional. Restore an item when evidence makes it necessary, and
ask first only when doing so crosses Smart's authority boundary.
