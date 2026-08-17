# Python Review

- **Use:** Python boundary; preserve interpreter range, environment, lock,
  package layout, checker, runner, and sync/async entry point.
- **Level 1:** Check syntax/types, mutable defaults, shared state, late closures,
  iterators, truthiness, exceptions, cleanup, missing awaits, blocking, and tasks.
- **Level 2:** Match packaging, imports, typing, errors, logging, and fixtures;
  test invalid input, exceptions, cleanup, async cancellation, and serialization.
- **Level 3:** Check dependency direction, import-time effects, globals, circular
  imports, hidden I/O, dynamic dispatch, and framework/ORM leakage.
- **Proof:** Prefer repository environment and narrow syntax/type/lint/test target.
- **Escalate:** Data loss, event-loop blocking, leaked tasks/resources, unsafe
  deserialization, state leakage, or public contract break.
- **Avoid:** Installs, lock rewrites, autofix, unsafe imports, and generic style.

