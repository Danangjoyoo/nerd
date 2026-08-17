# FastAPI Review

- **Use:** FastAPI/ASGI boundary; pair with Python and crossed dependencies.
- **Level 1:** Check route/method/order, parameter sources, dependencies, models,
  status/OpenAPI, async/blocking, cleanup, middleware, lifespan, and auth scope.
- **Level 2:** Match router, model, error, logging, and async persistence patterns;
  test input, dependencies, auth, errors, response validation, and cleanup.
- **Level 3:** Check HTTP/domain/persistence separation, unit-of-work ownership,
  global state, business logic in middleware, and background-work durability.
- **Proof:** Prefer focused tests/source; inspect app-start side effects first.
- **Escalate:** Auth gap, contract break, event-loop blocking, lost cleanup,
  cross-request state, or dropped background work.
- **Avoid:** Debug/override changes, mutating endpoints, and route-layout opinions.

