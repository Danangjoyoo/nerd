# Rust Review

- **Use:** Rust boundary; preserve workspace, crate/target, toolchain, features,
  target triple, profile, build scripts, bindings, and unsafe boundary.
- **Level 1:** Check compile, `Result`/`Option`, panic paths, casts, overflow,
  ownership, locks, atomics, `unsafe` invariants, FFI, async cancellation, and drop.
- **Level 2:** Match error, ownership, feature, visibility, runtime, and test
  conventions; test failures, features, targets, concurrency, and unsafe contracts.
- **Level 3:** Check crate direction, safe wrappers, global state, lock coupling,
  detached tasks, generic/trait complexity, and feature-matrix drift.
- **Proof:** Prefer narrow `cargo check`, Clippy, or test with explicit features.
- **Escalate:** Unsound safe API, UB, race, deadlock, untrusted panic, unbounded
  resources, or public compatibility break.
- **Avoid:** Format/fix, updates, unsafe build scripts, and Clippy-only style.

