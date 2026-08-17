# gRPC Review

- **Use:** gRPC boundary; pair with client/server stacks and preserve protobuf,
  stubs, runtime, proxy, retries, deadlines, and stream shape.
- **Level 1:** Check service/method, field numbers/types/presence, enums/reserved,
  old-client semantics, metadata, status, deadlines, cancellation, retries, and flow.
- **Level 2:** Match evolution, generation, interceptors, errors, deadlines, and
  observability; test old/new pairs, status, retries, cancellation, and streams.
- **Level 3:** Check transport/domain separation, service ownership, chatty calls,
  retry layering, interceptor policy, bounds, stream state, and rollout coupling.
- **Proof:** Prefer protobuf diffs, descriptors, metadata, and local contract tests.
- **Escalate:** Wire break, auth loss, duplicate effect, unbounded stream,
  deadline amplification, or core outage.
- **Avoid:** Live RPCs, reflection, retry/deadline changes, and stub regeneration.

