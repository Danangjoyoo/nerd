# Spring Boot Review

- **Use:** Spring Boot boundary; pair with Java/Kotlin and crossed dependencies.
- **Level 1:** Check beans, conditions, scopes, config, binding, filters/security,
  routes, errors, transactions/proxies, execution model, startup, and shutdown.
- **Level 2:** Match controller/service/repository, DTO, validation, error, logging,
  and test-slice conventions; test binding, auth, errors, rollback, and profiles.
- **Level 3:** Check dependency direction, transport/persistence leakage, cycles,
  service locators, broad scans, hidden startup work, and duplicated policy.
- **Proof:** Prefer focused wrapper compile/tests; inspect boot side effects first.
- **Escalate:** Auth gap, transaction loss, contract break, state leak, startup
  failure, blocking, or exhaustion.
- **Avoid:** Profile/Actuator changes, generation, autofix, and annotation style.

