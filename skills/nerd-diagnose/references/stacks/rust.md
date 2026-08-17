# Rust Diagnosis

## Scope and Provenance

- Use only when Rust is the smallest relevant stack; diagnose one symptom and one hypothesis.
- Record working directory, exact command, exit status, input, and expected versus observed result.
- Capture `rustup show active-toolchain` when available, `rustc -Vv`, and `cargo -V`.
- Resolve overrides: `RUSTUP_TOOLCHAIN`, directory override, `rust-toolchain.toml`, `rust-toolchain`, then default.
- Record host/requested target, components, package, Cargo target, profile, features, default-feature state, and relevant `cfg`.
- Capture workspace members, editions, features, and resolver with `cargo metadata --no-deps --format-version 1`.
- Inspect relevant `Cargo.toml`, workspace inheritance, `.cargo/config.toml`, source replacement, and unchanged `Cargo.lock`.
- Sanitize relevant `RUSTFLAGS`, `RUSTDOCFLAGS`, `CARGO_BUILD_TARGET`, `CARGO_TARGET_DIR`, build, and runtime environment.
- For compiler/linker/build-script/FFI boundaries, record OS, architecture, linker, native libraries, and container/CI image.
- Preserve fidelity: use `cargo +<toolchain> ...`, `--locked`, original target/profile/features, and repository-native orchestration.

## Diagnose

1. **Freeze:** Save the first relevant diagnostic, panic, error chain, timeout, wrong value, or measured regression; treat warnings and suggestions as evidence, not cause.
2. **Reproduce:** Keep toolchain, lockfile, target, profile, features, and environment fixed; narrow package/target first with `cargo +<toolchain> check --locked -p <package> --lib`.
3. **Classify:** Locate the first causal boundary: rustc, graph/features, build script, proc macro/generated code, linker/native code, test harness, runtime, or environment.
4. **Discriminate:** Predict one observation that differs if the hypothesis is true; run one non-corrective check without changing source or durable configuration.
5. **Compare:** Record predicted versus observed signals, competing explanations, and the parent skill's **Confirmed**, **Probable**, or **Unknown** gate.

## Symptom and Evidence

- **Types/ownership:** Keep rustc's first span, notes, crate, and target; later move, borrow, lifetime, trait, or type errors may be cascades.
- **Graph/features:** Compare metadata, lockfile, resolver, defaults, target/build/dev edges, and source/version; use `cargo tree -e features`, `cargo tree -e features -i <crate>`, or `cargo tree -d` only for the matching hypothesis.
- **Build script/macro/generated:** Identify the producer; use faithful `cargo +<toolchain> check -vv -p <package>` and compare `OUT_DIR`, sanitized environment, target, native tools, and producer stderr.
- **Panic/abort:** Reproduce with `RUST_BACKTRACE=1`; separate panic, explicit abort, stack overflow, signal, and foreign crash; optimized/inlined frames may be incomplete.
- **Error/wrong output:** Capture the existing `Result` source chain and boundary values; find the first broken invariant, not merely the final display string.
- **Tests/doc tests:** Re-run the exact test or doc test, then its target/package; use `-- --exact --nocapture` only when faithful and `-- --test-threads=1` only for standard libtest order hypotheses.
- **Stale/order state:** Compare a disposable `CARGO_TARGET_DIR`; do not `cargo clean`; separate cache from filesystem, clock, seed, port, network, and process-global state.
- **Async/hang:** Record executor, spawn/join ownership, progress/wake signals, timeout owner, cancellation, blocking work, and shutdown; distinguish pending, starved, blocked, detached, cancelled, and un-driven work.
- **Threads/locks/channels:** Capture task/thread states and last boundary; map lock order, poisoning, channel lifetime, blocking calls, atomics, and invariants; timeout alone does not prove deadlock.
- **Unsafe/FFI:** Record ABI, layout, ownership, lifetime, alignment, initialization, unwind, allocator, and thread assumptions at the smallest boundary.
- **Performance/memory:** Hold toolchain, target CPU, profile, features, input, allocator, load, and method constant; attribute a measured hotspot/allocation against a known baseline.
- **Environment:** Diff effective toolchain, Cargo config, linker/libraries, environment, filesystem/case behavior, locale/time zone, limits, and image; require one predictive difference.

## Deep Tools

- Use Miri only when its compatible component/toolchain and repository command already exist; check with `rustup component list --installed --toolchain <toolchain>`.
- Use sanitizers only with an existing compatible compiler/target/runtime invocation; a clean run covers only that execution.
- Use debuggers, profilers, macro expansion, or tracing only when installed, source-aligned, scoped, and more discriminating than current evidence.
- Record tool blind spots; avoid high-overhead production collection unless authorized and safe.

## Official Anchors

- [Cargo Reference](https://doc.rust-lang.org/cargo/reference/) · [rustc Book](https://doc.rust-lang.org/rustc/) · [rustup Book](https://rust-lang.github.io/rustup/)

## Guardrails

- Diagnose only; stop with cause, evidence, confidence, competing explanations, and the smallest missing verification.
- Do not edit source, manifests, lockfiles, generated files, data, infrastructure, or production state.
- Do not run `cargo fix`, `cargo update`, `cargo clean`, installers, deployments, migrations, or corrective scripts.
- Disposable build/test output is allowed; avoid extra network access and redact credentials, secrets, paths, payloads, and sensitive environment values.
- Do not use cloning, `unwrap`, broader bounds, new `unsafe`, feature/dependency changes, runtime swaps, or synchronization changes as proof.
