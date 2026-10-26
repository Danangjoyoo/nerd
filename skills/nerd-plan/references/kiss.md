# Extended KISS Rationale

Read only when simplicity is disputed or a locally small design shifts complexity
elsewhere; routine planning uses the inline rule.

Choose the simplest sufficient path across the whole change, not the fewest
lines, files, checks, or minutes. Hidden coupling, duplicated durable contracts,
caller complexity, and missing failures/compatibility are not simplicity.
Prefer fewer concepts, dependencies, and boundaries when correct and maintainable.
Add layers, services, interfaces, configuration, or extension points only for an
explicit requirement, established convention, observed duplication, or concrete
correctness, security, or measured performance need.

YAGNI is part of KISS: defer speculative features, options, backends, hooks,
and abstractions without dropping required outcomes, conventions, correctness,
security, accessibility, data integrity, or compatibility. Investigation,
integration, migration, cleanup, and proof remain necessary when evidence requires
them; focused proof must establish the result at the change's risk.

Defer optional nearby improvements; reporting them is optional. Restore deferred
work when evidence makes it necessary, confirming only when it crosses the
resolved Focus Record's authority boundary.
