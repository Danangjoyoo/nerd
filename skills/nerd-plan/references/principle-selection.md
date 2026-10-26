# Delivery Companion Selection

Read only when evidence suggests cross-boundary work or proven duplication and
the right companion is unclear. Routine Plan/Execute work uses inline KISS.
Read [extended KISS](kiss.md) only for disputed simplicity; [legacy YAGNI](yagni.md)
explains deferral but is never selected separately.

| Observed evidence | Selection |
| --- | --- |
| Crosses modules/services, changes durable contracts/data, or partial delivery leaves consumers inconsistent | KISS + [Comprehensive](comprehensive.md) |
| Same behavior at three maintained sites, or two independent contract copies across a boundary | KISS + [DRY](dry.md) |
| Both | KISS + Comprehensive + DRY; read both |
| Neither | KISS; read neither |

Predicted reuse, edit size, and hypothetical requirements do not qualify.
Comprehensive sets delivery breadth; DRY gives proven duplication one owner.
Keep this breakdown internal for clear work; show only in a requested plan,
material handoff, or decision where its trade-off helps:

> **Delivery Breakdown**
> - **Approach:** [KISS plus evidence-selected companions]
> - **Required outcome:** [Observable result]
> - **Simplest sufficient design:** [Direct design]
> - **Required surfaces:** [Necessary correctness/integration work]
> - **Proof:** [Behavior- and risk-appropriate evidence]
> - **Deferred:** [Optional/speculative work]

Restore deferred work when evidence requires it; ask only when crossing the
resolved Focus Record's authority boundary.
