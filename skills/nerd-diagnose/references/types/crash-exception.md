# Crash or Exception

Use when execution terminates via an uncaught exception, panic, abort, fatal runtime/native fault, signal, or OOM—not for a live hang, handled error, wrong result, build failure, or healthy lifecycle stop.

## Capture

- One event: timestamp, process/workload identity, artifact/build ID, runtime version, exit code, signal/termination reason, and smallest known trigger.
- Logs, dumps, metrics, and platform termination state correlated to that event; never merge similar-looking crashes.
- Complete causal trace, first relevant application-owned frame, symbol/source-map fidelity, and sanitized pre-failure state.
- Crash fingerprint: mechanism, exception/signal, originating frame, artifact/build ID, exact environment, and minimal input/action sequence.

## Diagnose

1. **Classify termination before frames.**
   - **Managed exception/panic:** preserve the complete unmodified trace, causes, suppressed exceptions, and wrapper messages.
   - **Native fault/fatal signal:** capture code, fault address, thread, loaded-module build IDs, and core/minidump metadata.
   - **OOM:** distinguish application heap exhaustion from OS/container eviction or kill using runtime output, termination state, limits, and immediately preceding memory metrics.
   - **Explicit exit/watchdog/probe/operator kill:** identify the initiator; if no fault caused it, remap to hang/timeout or environment/configuration.
   - If still unknown, request the missing bounded log, dump, exit status, or platform termination record; do not infer from frames.
2. **Follow the originating chain.** Start at the earliest causal failure, not the wrapper, final handler, or cleanup exception.
   - Traverse cause links and suppressed failures in execution order; call cleanup causal only when evidence shows it triggered termination.
3. **Verify frame fidelity.** Match symbols, source maps, debug files, and source revision to the crashing artifact/build ID.
   - Treat minified, unresolved, or stale line numbers as an evidence gap, not reliable location evidence.
4. **Locate the first relevant application-owned frame.** Find the code owning the violated contract, then trace its inputs across the adjacent runtime, library, framework, or native boundary.
   - With no application frame, inspect boundary-contract and version evidence; do not blame the deepest library frame.
5. **Reduce safely.** Re-run only in an authorized safe environment with the exact artifact, runtime, configuration, and input sequence.
   - Remove one input or prior action at a time. A faithful reproducer retains exception type/signal, causal frame, and relevant state—not only the exit code.
6. **Capture pre-failure state at the causal frame.** Record sanitized arguments, relevant locals/object state, thread/task, breadcrumbs, resources, and the expected invariant/API contract.
   - For native faults, include symbolized frames and pointer/ownership evidence; for OOM, allocation pressure, limit, and killer/eviction evidence.
7. **Test one explanation.** State its predictions for trigger, originating frame, and pre-failure state; reject it when any prediction conflicts.
   - Prefer a non-crashing event differing in one observed factor. Do not apply a repair to obtain confirmation.
8. **Record fidelity and gaps.** Name symbol/source mismatches, missing dump/log/state, unsafe or unavailable reproduction, and the next bounded discriminator.

## Guardrails

- In a crash loop, collect existing prior-instance logs, termination state, metrics, and dump metadata once; do not restart, scale, attach an invasive debugger, or repeatedly trigger production.
- Do not suppress exceptions, alter retries/probes/limits, increase memory, patch source, mutate durable data/infrastructure, or alter production.
- Scope-safe local diagnostics may create identified disposable caches, builds, or dumps.
- Sanitize secrets and personal data while preserving types, sizes, order, correlation IDs, and causal structure.
- Stop at cause and evidence; repair requires a separately confirmed Execute endpoint.
- Apply the parent **Confirmed / Probable / Unknown** gate to the recorded evidence and gaps.
