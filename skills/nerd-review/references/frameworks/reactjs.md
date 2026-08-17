# React Review

- **Use:** React UI boundary; pair with JavaScript/TypeScript and preserve renderer,
  build mode, server/client path, browser support, and component identity.
- **Level 1:** Check Hook order/deps/cleanup, keys, render purity, state flow,
  closures, mutation, async cancellation, errors, semantics, keyboard, and focus.
- **Level 2:** Match composition, state/data, styling, states, accessibility, and
  tests; cover interaction, async failure/race, cleanup, responsive, and hydration.
- **Level 3:** Check state ownership, duplicate truth, Effect synchronization,
  dependencies, error isolation, render cost, and harmful component complexity.
- **Proof:** Prefer focused component/browser tests in actual build environment.
- **Escalate:** Lost input, broken core flow, inaccessible flow, hydration
  corruption, cross-user state, or render/effect loop.
- **Avoid:** Blind snapshots, dependency changes, autofix, and cosmetic opinions.

