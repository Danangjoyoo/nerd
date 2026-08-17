# TypeScript Review

- **Use:** TypeScript/TSX boundary; preserve effective `tsconfig`, project refs,
  module resolution, runtime target, transforms, declarations, and lock.
- **Level 1:** Check types and emitted semantics: `any`, assertions, nullability,
  unions, serialized input, promises, cleanup, coercion, mutation, and imports.
- **Level 2:** Match import/type/error/validation/state conventions; test runtime
  success, invalid input, rejection, cleanup, boundaries, and build output.
- **Level 3:** Align static types with runtime validation; check dependency
  direction, state ownership, async flow, circular imports, and duplicate schemas.
- **Proof:** Prefer repository scripts and narrow `tsc`, lint, test, or build.
- **Escalate:** Type/runtime contract gap, unhandled rejection, state corruption,
  resource leak, broken module, or public API break.
- **Avoid:** Emit, generators, autofix, lock changes, and tooling-owned style.

