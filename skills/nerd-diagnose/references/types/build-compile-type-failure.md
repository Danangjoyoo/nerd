# Build, Compile, or Type Failure

Use when a compiler, type checker, linker, generator, or build graph rejects a target—not when a successful build later crashes, misbehaves, or fails only during deployment.

## Capture

- Repository revision, working directory, exact repository wrapper and command, target, profile/configuration, platform, and relevant environment overrides.
- Toolchain/runtime versions, lockfile state, features, flags, and the full first causal diagnostic with surrounding warnings and nested causes.
- Smallest faithful target plus the relevant dependency, classpath, module, or build-graph path.
- Generated-source provenance, effective configuration, and observed working/failing or local/CI differences.

## Diagnose

1. **Freeze the invocation.** Prefer the repository wrapper to a global tool; keep command, toolchain, target, configuration, and inputs unchanged while comparing evidence.
2. **Find the first causal diagnostic.** Defer repeated and cascading errors until the earliest explanatory error is understood.
   - Preserve preceding warnings, wrapper context, and nested causes.
   - If parallel ordering is ambiguous, rerun the same command with ordering or verbosity diagnostics; do not change compilation semantics for a cleaner message.
3. **Reduce the boundary.** Run the smallest existing target, module, package, or type-check unit that retains the same causal diagnostic.
   - If reduction changes or removes it, keep the smallest faithful target and record which omitted boundary matters.
4. **Locate the causal layer.** Tie the diagnostic to one violated rule or graph edge:
   - **Source/contract:** syntax, types, signatures, visibility, ownership, or language rules fail under the selected configuration.
   - **Toolchain/configuration:** wrapper, compiler, plugin, language level, target platform, flags, or configuration is unsupported or inconsistent.
   - **Dependency/graph:** version resolution, lockfile, features, classpath, module path, linkage, or an edge differs from target requirements.
   - **Generation:** required output is missing, stale, malformed, emitted elsewhere, or blocked by a failed upstream task.
   - **Environment:** filesystem, permissions, architecture, runtime location, locale, resource limit, or injected environment differs.
5. **Discriminate with comparison.** Compare effective configuration and graph output with a known-working target or environment when available.
   - For local/CI splits, compare wrapper/toolchain, command, platform, environment, lockfiles, features/flags, resolution, generated inputs, and task order.
   - Change at most one diagnostic condition per check; record whether it toggles, isolates, or changes the first causal diagnostic without introducing another cause.
6. **Treat cache staleness as a hypothesis.** Inspect supported cache keys, timestamps, task inputs/outputs, and clean-build or isolated-output evidence.
   - Prefer tool-provided checks, fresh disposable output, or a scoped temporary cache that preserves the original evidence.
7. **Record gaps precisely.** Name any unavailable artifact or single non-corrective check needed to distinguish remaining layers; do not guess.

## Guardrails

- Diagnose only: do not edit source/generated files, update dependencies/lockfiles, change durable configuration, mutate data/infrastructure, access production, or apply repair.
- Do not delete shared or broad caches. Diagnostic builds may create identified disposable local caches or build output.
- Stop at cause and evidence; leave correction to a separately confirmed Execute endpoint.
- Apply the parent **Confirmed / Probable / Unknown** gate to the recorded evidence and gaps.
