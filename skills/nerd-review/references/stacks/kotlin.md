# Kotlin Review

- **Use:** Kotlin boundary; preserve source set, variant, Kotlin/JDK targets,
  plugins, and generated sources. Add Java for interop.
- **Level 1:** Check compilation, platform/null types, casts, `!!`, `lateinit`,
  resources, coroutine scope, dispatcher, blocking, cancellation, and cleanup.
- **Level 2:** Match null/result/coroutine conventions; test invalid input,
  exceptions, timeout, cancellation, ordering, interop, and generated contracts.
- **Level 3:** Check dependency direction, global scopes, shared flows, hidden
  dispatchers, callback/coroutine mixing, and state-machine ownership.
- **Proof:** Prefer wrapper and exact module/source-set compile or focused test.
- **Escalate:** Lost cancellation, unbounded coroutines, state leakage,
  nullability failure, transaction escape, or API break.
- **Avoid:** Generators, dependency refresh, formatters, and Kotlin-style opinions.

