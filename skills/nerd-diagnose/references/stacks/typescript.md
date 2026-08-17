# TypeScript Diagnosis

## Provenance and Scope

- Scope: smallest failing package, project reference, file, test, or runtime boundary.
- Runtime: Node, Deno, Bun, browser, worker, edge, or framework server/client; record version, flags, and mode.
- Toolchain: locked package manager, lockfile, repository-local TypeScript, script, working directory, and CI image.
- Build path: root/leaf `tsconfig`, `extends`, references, transpiler, bundler, test runner, generator, and source maps.
- Repro: exact command/input, expected/actual result, first causal diagnostic or stack frame, and working comparison.
- Use existing scripts (`npm run`, `pnpm run`, `yarn`, or `bun run`) only after identifying the repository's manager.
- Let `<tsc>` mean the selected repository-local compiler invocation; never type the placeholder or substitute a global compiler.

## Diagnose

1. **Classify the boundary.** Separate type checking, declaration emit, JS emit, module resolution, bundling, test transforms, and runtime execution.
   - A passing `tsc` does not validate a transpiler that skips checking.
   - A type error does not prove emitted JavaScript fails; types and assertions vanish at runtime.
2. **Reproduce narrowly.** Run the exact failing script for one package, project, test, or entry point; keep the first causal diagnostic.
   - Do not guess narrowing flags; use documented repository configuration.
3. **Resolve effective compiler state.** Inspect `<tsc> -p <tsconfig> --showConfig`.
   - Trace `extends` and project references.
   - Check `files`/`include`/`exclude`, `types`, `lib`, `target`, `module`, `moduleResolution`, `paths`, `baseUrl`, roots/output, declarations, and strictness.
   - Identify whether a leaf project or referenced declaration/build output owns the failure.
4. **Inspect the matching branch.**
   - Types/declarations: first diagnostic, inference, overloads, generics, narrowing, ambient declarations, and consumed declaration version/path.
   - Imports: compiler versus runtime/bundler resolution, spelling/extensions, package `type`, `exports`/`imports`, conditions, and ESM/CJS.
   - Trace only the scoped project with `<tsc> -p <tsconfig> --traceResolution --noEmit`; first confirm `--noEmit` is compatible and any configured output is disposable.
   - Runtime/emit: identify the tool that produced executed JS; inspect its transform, actual values, artifact identity, and matching source map.
   - Runner/framework: compare its transforms/config with `tsc`; check server/client globals, conditional exports, env, serialization, DOM events, hydration, and network boundaries.
   - Generated types: record schema/input, generator/plugin version, existing output, and consumer; do not regenerate durable files.
5. **Follow runtime causality.** Capture the first wrong value and call path.
   - Async: missing `await`, detached promises, rejection handling, timers, cancellation, scheduling, event-loop ownership, and active handles.
   - Performance/memory: compare the same workload; use runtime-native profiles or heap evidence only when the hypothesis requires it.
   - Contracts: compare sanitized wire data and runtime validation; shared interfaces do not validate payloads.
6. **Compare environments.** Diff runtime flags, package manager, lockfile resolution, TypeScript, `@types`, loaders, transformers, bundlers, and framework versions.
   - Treat version correlation as **Probable** until a controlled comparison or authoritative change record connects it to the symptom.
7. **Apply the parent confidence gate.** Report **Confirmed**, **Probable**, or **Unknown**, including the exact missing discriminator.

## Signals

- Local/CI mismatch → versions, lockfile, workspace, effective config, runtime flags; source diff alone is weak.
- Missing/wrong import → relevant resolution trace plus runtime resolver and export conditions; file existence is insufficient.
- Editor/CLI mismatch → editor SDK/config versus repository-local compiler/config.
- `tsc` passes/runtime fails → executed transform, emitted JS, actual value, and mapped stack.
- Stale consumer types → resolved declaration path, reference output, and generator provenance.
- Async hang/race → promise ownership, scheduling, cancellation, rejection path, and active handles.
- Client/server mismatch → sanitized payload and runtime validation on both sides.

## Guardrails

- Diagnose only: do not cast, suppress errors, edit config/source, regenerate, upgrade, change module format, or repair.
- Do not install dependencies, clean repositories, run broad builds/traces, or create durable output when a narrower check works.
- Diagnostic commands may create identified disposable cache/build output; never commit it or mutate durable data/infrastructure.
- Profiles and traces can add overhead; scope production capture, use approved tooling, and redact secrets, payloads, paths, and environment values.
- Stop at cause and evidence; offer a minimal prescription and verification check only after Execute authorization.
