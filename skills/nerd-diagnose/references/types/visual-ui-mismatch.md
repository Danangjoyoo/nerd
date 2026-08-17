# Visual or UI Mismatch

Use for incorrect rendering or visual state, including hover, focus, active, disabled, loading, error, responsive, and accessibility states.

## Capture

- Route; build/commit; browser/version; OS.
- Viewport; device-pixel ratio; zoom; theme; locale; direction.
- Font availability/loading; auth/user state; feature flags; exact navigation and interaction sequence.
- Expected-state provenance: approved design/acceptance rule, known-good screenshot, or same-build browser/device baseline.
- Privacy-safe screenshot of actual and expected states.
- Smallest relevant DOM subtree or native hierarchy.
- Computed styles, winning/overridden declarations, layout/scroll boxes.
- Stacking/containing blocks, pseudo-elements, interaction state, accessibility state.
- Console errors; relevant sanitized network data; event/state transitions.
- Loaded assets, decoded image sizes, font requests/faces, timing, and cache status.

## Diagnose

1. **Normalize the observation frame.**
   - Match route, build, viewport, DPR, zoom, state, and interaction sequence.
   - Do not compare unlike environments or states.
2. **Validate the oracle.**
   - Confirm the expected source covers this breakpoint and state.
   - If sources disagree or omit it, keep the expectation unresolved.
3. **Find the first divergent layer.**
   - DOM/state differs: trace props, application state, conditional rendering, events, and data.
   - DOM matches; style differs: inspect cascade, inheritance, specificity, variables, queries, and UA defaults.
   - Style matches; geometry differs: inspect intrinsic size, box model, flex/grid, overflow, transforms, rounding, and font metrics.
   - Geometry matches; pixels differ: inspect fonts, image/SVG assets, raster density, color, compositing, antialiasing, and platform rendering.
4. **Test responsive behavior.**
   - Compare just below, at, and above the suspected threshold.
   - Keep DPR and zoom fixed; inspect media/container queries and overflow.
5. **Test timing without correction.**
   - Freeze or record animations/transitions at a stable frame.
   - Repeat for load order, cache, font/image arrival, and reduced-motion state.
6. **Check accessibility presentation.**
   - Compare focus visibility, disabled/error state, semantics, labels, and exposed state.
   - Separate semantic/accessibility divergence from pixel-only divergence.
7. **Classify with the parent confidence gate.**
   - Name the first divergent layer and responsible state, rule, constraint, asset, font, or input.
   - Record the missing oracle, faithful environment, isolation, or capture when unresolved.

## Mapping Signals

- Incorrect stable action/result: remap to deterministic wrong output.
- Missing or malformed remote data: remap to integration/API failure.
- Load, animation, or frame timing changes failure rate: remap to intermittent/flaky.
- Keep secondary visual effects under the active primary mapping.

## Guardrails

- Diagnose only: do not edit source/styles, change durable data, mutate infrastructure, deploy, or alter production.
- Redact credentials, tokens, personal data, and private content from captures.
- Keep screenshots, traces, accessibility snapshots, and DOM/style exports scoped and disposable unless requested as artifacts.
