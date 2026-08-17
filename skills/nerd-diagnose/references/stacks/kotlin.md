# Kotlin Diagnosis

- Use after Kotlin is mapped at the failing boundary and one diagnosis type is active.
- Diagnose only; apply the parent skill's confidence gate and stop before repair.

## Select and Record

- Target: JVM, Android, Native, or JS; exact module, source set, variant, task/phase, entry point, and test engine.
- Build entry: repository `gradlew`/`mvnw` and wrapper properties; do not substitute global tools.
- Toolchain: Kotlin and present compiler/KSP/KAPT/serialization/Compose/framework plugins; JDK/Android/Native/JS toolchain.
- Runtime: JVM command/flags, Android device/API and build variant, Native target/binary, or JS runtime/bundle/source map.
- Build context: plugin declarations, version catalogs, toolchains, relevant configuration/scope, generated-source roots, environment names.
- Record `./gradlew --version` or `./mvnw --version`; sanitize environment and JVM/config values.
- If no wrapper or faithful target exists, record the gap and use only repository-documented tooling.

## Diagnose

1. Freeze the smallest input, expected/actual result, exact command/directory, full first diagnostic or cause chain, and failure phase.
2. Reproduce the narrowest existing module/task/test/variant; avoid broad builds, `clean`, dependency refresh, and invented task names.
3. Locate the first boundary: build configuration, compiler/plugin, generated code, runtime/framework, coroutine/Flow, interop, or dependency.
4. Map `*Kt`, lambda, inline, suspend state-machine, synthetic, and generated frames to the matching source and build artifact.
5. State one hypothesis and predicted signal; vary one factor with the same target, input, toolchain, and artifact.
6. Prefer focused compile/test or dependency evidence; use dumps/profiles only for measured hang/performance symptoms.
7. Recheck without instrumentation, classify through the parent gate, and stop.

## Focused Commands

- Gradle compile/test: `./gradlew <module>:<task> --stacktrace --info`; use `--tests '<package.Test.method>'` only on an existing compatible test task.
- Maven test: `./mvnw -pl <module> -am -Dtest='<TestClass>#<method>' test -e` when the repository uses that test provider.
- Gradle graph: `./gradlew <module>:dependencyInsight --dependency <name> --configuration <configuration>`; derive configuration from the failing task.
- Maven graph: `./mvnw -pl <module> dependency:tree -Dincludes=<groupId>:<artifactId>` only with the repository-configured plugin.
- JVM ownership/version first: verify PID; run `jcmd <pid> help <command>` because commands vary by JDK.
- JVM hang: take multiple timestamped `jcmd <pid> Thread.print -l` dumps; stable waits and changing stacks mean different things.
- JVM profile: use JFR only for reproducible symptoms, a disposable absolute path, equal workload/JDK, and a baseline.

## Failure Signals

- **Build/compiler:** preserve the first diagnostic, file/line, source set, arguments reported by the build, toolchain, and preceding codegen/configuration failure; later errors may cascade.
- **Target mismatch:** compare declared and actual JVM bytecode/JDK, Android variant/device, Native target/binary, or JS runtime/module/bundle.
- **Runtime/linkage:** capture full cause/suppressed chain, first application frame, actual classpath/module path, resolved artifact, metadata, and loaded symbol origin.
- **Nullability/interop:** trace the value through Java signatures/annotations, platform types, generics, overrides, reflection, or serialization; a downstream NPE is not origin proof.
- **Coroutines/Flow:** record parent/child Job, context/name, dispatcher/thread around suspension, cancellation cause, timeout owner, exception handler, collector, and upstream/downstream boundary.
- **Hang:** separate suspension, blocking, deadlock, dispatcher starvation, backpressure, and slow dependency using repeated thread/coroutine state.
- **Generated code:** identify generator/plugin, input, output file/line, source-set wiring, and timestamps; inspect but never edit generated output.
- **Bytecode/decompilation:** use only to resolve erased/synthetic/inline or generated behavior; correlate it back to the exact compiled artifact and source metadata.
- **Dependency:** record requested/selected version, selection reason, configuration/scope, duplicates, compatibility, and the artifact used on the failing path.
- **Tests/environment:** compare runner, variant/profile, dispatcher or virtual-time setup, locale/time zone, flags, filesystem, permissions, and sanitized effective config.

## Coroutines and Runtime Evidence

- Prefer existing logs or debugger support; `-Dkotlinx.coroutines.debug` must use an existing JVM-argument channel and changes diagnostics.
- Use `DebugProbes` only if the project already includes/enables `kotlinx-coroutines-debug`; do not add it, and do not use it on Android.
- Attachment, debug probes, dumps, and profiling add overhead and may expose command lines, paths, arguments, or application data.

## Guardrails

- Do not edit source/config, regenerate code, change dependencies, clear caches, run `clean`, restart/kill processes, deploy, or mutate data/infrastructure.
- Never invent modules, variants, configurations, profiles, compiler flags, or JVM argument channels.
- Never attach to production without separate authorization; keep logs/dumps/recordings disposable and sanitized.
- Redact credentials, system properties, command lines, URLs, personal data, and internal topology.
- Treat stack proximity, compiler text, profiler correlation, and decompiled output as evidence—not causality by themselves.
