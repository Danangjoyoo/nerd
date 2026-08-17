# Go Review

- **Use:** Go boundary; preserve module, workspace, toolchain, target, tags, and cgo.
- **Level 1:** Check affected package; trace errors, nil interfaces, aliasing,
  conversions, cleanup, goroutines, channels, locks, and context cancellation.
- **Level 2:** Match package/error/context conventions; test success, failure,
  timeout, cancellation, boundaries, and concurrency; document exported contracts.
- **Level 3:** Check dependency direction, interface ownership, shared state,
  goroutine/channel lifecycle, fan-out, retries, and hidden partial success.
- **Proof:** Prefer focused package compile/test, `go vet`, or targeted race test.
- **Escalate:** Deadlock, state corruption, lost errors, unbounded resources, or
  public API break.
- **Avoid:** Generators, module rewrites, broad autofixes, and style-only findings.

