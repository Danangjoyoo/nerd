# Spring Boot Diagnosis

- Load when Spring Boot owns the active boundary.
- Pair with one diagnosis type and Java or Kotlin; add database, Kubernetes, or integration guidance only when evidence crosses that boundary.

## Capture

- Record Spring Boot, Spring Framework, JVM, build-wrapper, and artifact versions.
- Record the launch command, main class, packaging, server/container, context path, and feature flags.
- Record active/default profiles, configuration sources/imports, command-line arguments, and effective classpath.
- Record the web stack: Spring MVC, WebFlux, or non-web.
- Preserve the first causal exception, full `Caused by` chain, failure analysis, and first application frame.

## Diagnose

1. **Locate the phase:** Separate build/configuration, context creation, embedded-server startup, request dispatch, scheduled/async work, persistence, and shutdown.
2. **Inspect startup:** Map the failed bean, dependency, property, or auto-configuration condition to the effective classpath and profiles. Prefer an existing condition report.
3. **Resolve configuration:** Trace each relevant property to its winning source and precedence; compare profiles, imports, environment names, command-line values, config trees, and `@ConfigurationProperties` binding diagnostics.
4. **Resolve beans:** Verify type, qualifier, primary/conditional status, scope, proxying, package scan, and the exact matched or failed condition.
5. **Trace web flow:** Correlate one request through filters/WebFilters, security, route mapping, conversion/validation, controller, service, serialization, and exception handling.
6. **Trace data:** Correlate repository calls, rendered queries, pool state, transaction boundaries, propagation, commit/rollback, and the first database divergence.
7. **Trace runtime:** For hangs or latency, capture request threads/tasks, Reactor context when applicable, executors, pools, downstream timings, and timeout ownership.
8. **Classify:** Record the exact Boot boundary, effective condition/value, causal evidence, ruled-out layer, and missing confirmation; apply the parent confidence gate.

## Evidence Rules

- Do not assume IDE, tests, and deployed artifacts select the same profiles or classpath.
- Treat a missing bean as a symptom until scanning, conditions, classpath, and earlier creation failures are distinguished.
- Do not infer a missing route from status alone.
- Use existing authorized Actuator `env`, `configprops`, or `mappings` reads only when already exposed and sanitized.
- Use `--debug` only in a safe local reproduction; it changes logging and is not a production probe.
- Cross into JVM, database, messaging, or network guidance only at the first evidenced failure.

## Guardrails

- Prefer existing output, tests, metrics, traces, and read-only endpoints; local boot may run migrations, initializers, listeners, schedulers, or external calls.
- Do not expose/reconfigure Actuator or change logging, profiles, properties, beans, ports, security, or dependencies.
- Never invoke Actuator writes, shutdown, heap dumps, or unsanitized environment reads.
- Treat condition reports, bean lists, mappings, logs, and configuration as sensitive; retain only causal fields.
- Stop at cause; route configuration, code, data, or operational changes through Execute.

Official anchors:

- [Auto-configuration](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)
- [Externalized configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html)
- [Actuator endpoints](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html)
