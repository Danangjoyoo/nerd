# Java Review

- **Use:** Java/JVM boundary; preserve wrapper, module, JDK, release, profiles,
  processors, and generated sources.
- **Level 1:** Check compilation, nullability, casts/generics, equality/hash,
  overflow, exception causes, interruption, resource cleanup, locks, and executors.
- **Level 2:** Match package, DI, exception, immutability, logging, and test
  conventions; test invalid input, cleanup, transactions, and concurrency.
- **Level 3:** Check module/layer direction, shared state, transaction/executor
  ownership, cycles, and framework/persistence leakage into domain contracts.
- **Proof:** Prefer checked-in wrapper and narrow compile/test target.
- **Escalate:** Binary/API break, transaction corruption, deadlock, exhaustion,
  swallowed core failure, or cross-request state.
- **Avoid:** Generation, dependency updates, formatters, unsafe lifecycle tasks,
  and preference-only patterns.

