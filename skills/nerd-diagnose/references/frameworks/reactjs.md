# React Diagnosis

## Scope

- Use when React owns the active UI boundary.
- Pair with JavaScript or TypeScript; add visual/UI mapping for appearance failures.

## Capture

- React, React DOM, framework, and bundler versions; lockfile and revision.
- Dev/production build, executed bundle/source-map identity, feature flags.
- Root API, Strict Mode boundary, server/client path, route, browser, viewport.
- Exact interaction; expected/observed UI; console, network, DOM, accessibility state.
- Component identity, tree, props, state, context/store, events, and timestamps.

## Diagnose

1. **Freeze one interaction.** Find the first incorrect render or commit boundary.
2. **Locate the phase.** Separate input/loading, render, reconciliation, commit,
   layout/passive Effect, handler, Suspense/transition, error boundary, and hydration.
3. **Trace one value.** Follow API/cache -> loader -> props/store/state -> render -> DOM;
   record update source, batching/transition, closure value, mutation, memo, and key.
4. **Check Effects.** Compare setup, dependency identity, cleanup, external system,
   and commit order. Prove the production symptom before blaming Strict Mode's
   development-only extra render and setup/cleanup checks.
5. **Check identity.** Compare element type, position, stable key, branch, list order,
   portal, and state preservation/reset; DOM reuse alone proves nothing.
6. **Check hydration.** Compare server HTML/data with the initial client render under
   identical locale, time, random/data snapshot, and flags; keep the first warning/subtree.
7. **Check async paths.** Correlate request/promise owner, abort, race/order, fallback,
   transition, error capture, rejection, and unmount.
8. **Cross boundaries carefully.** Separate browser/event, API/network, React runtime,
   and build/bundle evidence; development behavior does not prove production behavior.
9. **Classify and stop.** Record first divergence, component/bundle provenance,
   direct evidence, and missing confirmation; apply the parent confidence gate.

## Signals

- Stale UI: stale input, reused identity, mutation, memoization, or stale closure.
- Duplicate work: Strict Mode check, repeated event, retry, remount, or Effect lifecycle.
- Hydration mismatch: server/client input or environment diverged before recovery.
- Timing change under profiling: evidence may be observer-sensitive; verify original build.

## Guardrails

- Prefer existing React DevTools, browser evidence, and focused repository tests.
- Do not change keys, Hook arrays, memoization, state, Strict Mode, SSR, or flags.
- Redact props, stores, cookies, tokens, user data, screenshots, traces, and source maps.
- Diagnose only; stop before source, dependency, configuration, data, or deployment edits.

Anchors: [Strict Mode](https://react.dev/reference/react/StrictMode),
[Effects](https://react.dev/reference/react/useEffect),
[hydration](https://react.dev/reference/react-dom/client/hydrateRoot).
