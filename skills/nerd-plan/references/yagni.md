# Legacy YAGNI Rationale

YAGNI is no longer selected as a separate delivery principle. Its useful rule
is part of KISS: do not build speculative features, options, hooks, backends, or
extension points for hypothetical future needs.

This reference remains only to preserve the rationale and compatibility with
older plans. New work states KISS and lists speculative surface under
**Deferred**.

Deferral must not remove behavior required by the requested outcome, an explicit
constraint, an established repository convention, or correctness, security,
accessibility, data-integrity, performance, or compatibility evidence. If the
user explicitly requests speculative surface, explain the trade-off before
dropping it. If later evidence makes a deferred item necessary, restore it and
ask only when doing so crosses the resolved Focus Record's authority boundary.
