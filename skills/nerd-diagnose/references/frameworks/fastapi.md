# FastAPI Diagnosis

- Use when FastAPI owns the active ASGI boundary.
- Pair with Python; add integration or database guidance only at a proven boundary.

## Capture

- Versions: FastAPI, Starlette, Pydantic, ASGI server, Python, plugins.
- Launch: app import/factory, exact command, worker model, event loop, environment.
- Topology: proxy/root path, mounts, routers, middleware, lifespan and exception handlers.
- Overrides: dependencies, security dependencies, effective configuration.
- Event: request or lifespan trigger, timestamp, correlation ID, worker/process.
- Result: expected/actual response, complete traceback or ASGI error.
- Sanitize headers, body/response shapes, cookies, tokens, and validation inputs.

## Diagnose

1. **Match the runtime.**
   - Reproduce with the failing process type; test client, local worker, and multi-worker deployment differ.
2. **Find the first divergent boundary.**
   - Check proxy/TLS -> server -> lifespan -> middleware -> route -> dependency -> validation -> endpoint -> serialization -> background/downstream work.
   - Prove which layer produced the status; the status alone is insufficient.
3. **Resolve routing.**
   - Compare host/root path, mount and router prefixes, path converters, method, trailing slash, and declaration order.
   - Compare source or an existing local OpenAPI/routes artifact with the active app.
4. **Resolve validation.**
   - Preserve error location/type and redacted input shape.
   - Separate path/query/header/body parsing, model validation, dependency input, and response-model validation.
   - Check actual FastAPI/Pydantic versions before blaming the declared model.
5. **Trace dependencies.**
   - Map graph, parameter source, overrides, caching, security, `yield` setup/cleanup, and exception path.
   - Prove which dependency ran and returned what contract; do not infer cause from 401/403.
6. **Trace lifecycle and async work.**
   - Separate import, startup/shutdown, `async def`, `def`, awaited tasks, cancellation, thread pool, blocking calls, background tasks, and worker boundaries.
   - For hangs, capture task/thread state; timing changes do not prove a race or blockage.
7. **Trace middleware and errors.**
   - Reconstruct middleware order and find the exception before handlers transform it.
   - Separate server errors, `HTTPException`, validation responses, and client disconnects.
8. **Classify and stop.**
   - Record first divergence, version/config provenance, direct evidence, and missing confirmation.
   - Apply the parent confidence gate.

## Guardrails

- Prefer focused repository tests and existing traces.
- Starting the app may run lifespan hooks, migrations, schedulers, or external calls; inspect effects first.
- Do not expose docs or enumerate production routes solely to obtain proof.
- Do not change reload/debug, workers, overrides, middleware, handlers, models, or production logging.
- Retain only the minimum redacted causal shape; stop before code, configuration, dependency, data, or deployment changes.

Official anchors: [debugging](https://fastapi.tiangolo.com/tutorial/debugging/), [errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), [dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/).
