# gRPC Diagnosis

- Use when gRPC owns the active integration boundary.
- Pair with client/server stacks and the integration/API diagnosis type.

## Capture

- Versions on both sides; fully qualified service/method; RPC streaming shape.
- `.proto`, descriptor, and generated-stub provenance.
- Target/authority, resolver, balancer, proxy/mesh, TLS identity, compression.
- Service config, interceptors, deadline, retry/hedging policy, deployment identities.
- One attempt: correlation/trace ID, times, deadline, attempt, peer, selected backend.
- Redacted request/response shapes, metadata names, status/message/details, trailers, logs.
- Never merge retries into one apparent call.

## Diagnose

1. **Find the first failed layer.**
   - Trace resolution -> TLS/connection -> HTTP/2 -> client interceptor -> serialization -> balancing/proxy -> server interceptor -> dispatch -> handler -> dependency -> trailers.
   - Prove whether application, proxy, or library generated the final status.
2. **Verify the contract in force.**
   - Compare package/service/method, field numbers/types/presence, `oneof`, enums, reserved fields, stubs, and actual descriptors.
   - Wire compatibility does not prove semantic compatibility or validation.
3. **Verify metadata and identity.**
   - Preserve names and redacted value classes, TLS peer identity, credential source, authority, and policy decision.
   - Attribute `UNAUTHENTICATED`, `PERMISSION_DENIED`, routing, or application status to the enforcing component.
4. **Resolve deadlines and cancellation.**
   - Build end-to-end and per-attempt timelines: propagation, queue/connect, handler/dependency, cancellation owner.
   - Check whether the server finished after the caller observed `DEADLINE_EXCEEDED`.
5. **Resolve retries and balancing.**
   - Compare service config, retryable codes, backoff, hedging, idempotency, resolver addresses, subchannel state, and backend.
   - Require per-attempt evidence before blaming server instability.
6. **Resolve streaming.**
   - Record sequence/count/size, half-close, cancellation, reader/writer ownership, flow control, backpressure, keepalive/proxy timing, and last message seen by each side.
   - A stalled stream is not automatically a network failure.
7. **Use probes conditionally.**
   - Use health, reflection, channelz, or `grpcdebug` only when already enabled and authorized.
   - Reflection may expose contracts; `grpcurl` invokes real RPCs. Never probe an unknown or mutating method.
8. **Classify and stop.**
   - Record first failed layer, attempt/contract provenance, direct evidence, and missing confirmation.
   - Apply the parent confidence gate.

## Guardrails

- Prefer existing traces, logs, descriptors, and a local stub.
- Treat replay as unsafe until side effects and idempotency are established.
- Do not change deadlines, retries, keepalive, service config, TLS, interceptors, stubs, proxies, balancing, or health.
- Retain no auth metadata, private key material, payloads, internal endpoints, or user data beyond redacted causal shape.
- Stop before contract, code, infrastructure, traffic, or production changes.

Official anchors: [status codes](https://grpc.io/docs/guides/status-codes/), [deadlines](https://grpc.io/docs/guides/deadlines/), [health](https://grpc.io/docs/guides/health-checking/).
