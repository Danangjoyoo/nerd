# Integration or API Failure

- Use when caller and remote process, service, gateway, or API disagree across a network or protocol boundary.
- Choose a closer type when evidence already isolates the defect inside one process, build, environment, or data invariant.
- Never assign ownership from an HTTP/RPC status alone.

## Capture

- Observation window: expected/actual behavior, environment, caller/API versions, UTC time range, original timezone, correlation/request/trace IDs.
- Sanitized exchange: operation, destination/route, relevant query/header names, body shape, status/code, response shape, elapsed time.
- Payload evidence: retain values only when necessary and safe; otherwise retain types, lengths, hashes, or redacted samples.
- Delivery timeline: attempts, backoff, per-attempt/end-to-end budgets, cancellation, rate limits, idempotency keys, completion after caller timeout.
- Never record credentials, cookies, tokens, secrets, or unnecessary PII.

## Diagnose

1. Correlate caller, DNS, connection, TLS, gateway, service, and dependency evidence by timestamp and ID.
2. Stop at the first boundary where expected evidence disappears or first violates the contract.
3. Check transport before payload hypotheses: resolver result, address family, IP/port, proxy, certificate chain, hostname/SNI, trust store, protocol/ALPN.
4. Check edge routing: matching edge ID, route decision, upstream selection, generated response, and corresponding service span.
5. Check the deployed contract: route/schema version, generated-client version, fields, nullability, enums, numbers/dates, envelope, `Content-Type`, `Accept`, charset, encoding, and protocol/version headers.
6. Separate server rejection from a valid response the client cannot receive or deserialize.
7. Check identity without exposing credentials: source/type, issuer, audience, expiry/clock, authoritative authentication log.
8. Check authorization separately: principal, resource/action, and enforcing policy decision; treat `401`/`403` only as clues.
9. Check delivery: distinguish the first failure from retry amplification, duplicates, timeout-budget loss, and downstream propagation.
10. Report first causal boundary, owner, mechanism, supporting IDs/times, ruled-out layers, and missing proof; apply the parent skill's confidence gate.

## Boundary Signals

- **No outbound attempt:** caller validation, URL construction, or serialization.
- **Resolution/connect/TLS failure:** DNS, environment, network, proxy, TLS, or endpoint.
- **Edge sees request; service does not:** gateway, proxy, or routing.
- **Rejected before handler:** authentication, authorization, protocol, serialization, or deployed contract.
- **Handler emits failure:** service domain logic or exception.
- **Child span fails or waits:** dependency or service integration.
- **Server succeeds; caller fails:** response path or client parser.
- A timeout is not network proof; verify whether service or dependency work continued.

## Safe Replay

- Prefer existing traces, logs, fixtures, and local stubs.
- Replay only to local/isolated targets after proving the request side-effect-free; nominal idempotency is insufficient.
- Never replay production writes, webhooks, payments, publications, destructive reads, unknown effects, production tokens, or sensitive payloads.
- For unsafe requests, reproduce only the protocol shape against a disposable local stub.
- Use one bounded attempt; honor rate limits; stop before side effects, alerts, lockouts, cost, load, or retry storms.

## Guardrails

- Use correlated adjacent-boundary evidence; a status, timing coincidence, or isolated log is not causal proof.
- Keep captures sanitized, disposable, local, and outside source-controlled changes.
- Diagnose only: no contract, client, service, policy, data, configuration, or infrastructure repair or mutation.
- Stop at classification or the single missing evidence source; any corrective or effectful probe requires a confirmed Execute endpoint.
