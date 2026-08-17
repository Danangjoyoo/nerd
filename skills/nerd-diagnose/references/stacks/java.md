# Java Diagnosis

- Load after Java/JVM evidence reaches the active failure boundary.
- Keep one hypothesis; apply the parent **Confirmed / Probable / Unknown** gate.

## Select and Capture

- Detect Maven (`mvnw`, `.mvn/`, `pom.xml`), Gradle (`gradlew`, wrapper, settings/build files), or direct `javac`/`java` only when the real launcher uses it.
- Prefer the checked-in wrapper. Record wrapper distribution/checksum, module/task, profiles, plugins, toolchains, locks/catalogs, JVM args, exact command, working directory, runner, OS/architecture, and artifact checksum/version.
- Capture only matching identities: `./mvnw -version`, `./gradlew --version`, `java -version`, `javac -version`; record vendor, exact versions, `JAVA_HOME`, compiler target, and application JVM.
- Inspect CI/container launch files, `.mvn/jvm.config`, `gradle.properties`, `.java-version`, and `.tool-versions` when relevant. Never assume build JVM, compiler toolchain, bytecode target, and runtime JVM match.

## Diagnose

1. **Preserve failure.** Record expected/actual behavior, minimal input, timestamps/correlation IDs, exit status, full first failure, every `Caused by` and suppressed exception, and earliest relevant application frame.
   - Treat framework, proxy, reflection, executor, and build-task exceptions as wrappers until the nested cause is explained.
2. **Reproduce faithfully.** Start with the recorded command, then narrow to one existing target:
   - Maven: `./mvnw -pl :<artifact-id> -am compile` or `./mvnw -pl :<artifact-id> -am test -Dtest=<Class>#<method>`.
   - Gradle: `./gradlew :<module>:compileJava --stacktrace` or `./gradlew :<module>:test --tests '<package.Class.method>' --stacktrace`.
   - Keep repository task/plugin conventions; ad hoc `javac` can omit generated sources, processors, toolchains, or classpaths.
   - Add Maven `-e/-X` or Gradle `--info/--debug` only for missing provenance; sanitize their output.
3. **Trace dependency/class origin.** Use the affected module/configuration only: `./mvnw -pl :<artifact-id> dependency:tree -Dincludes=<group>:<artifact>` or `./gradlew :<module>:dependencyInsight --dependency <name> --configuration <configuration>`.
   - Identify selected version and introducing path. For an isolated run, use JDK 9+ `-Xlog:class+load=info` or older-JVM `-verbose:class`.
   - Inspect without execution using `javap -verbose <class-or-file>`; compare origin, major version, signatures, `Compiled from`, and deployed artifact.
4. **Trace runtime exceptions.** Preserve causal/suppressed chains, profile/config source, transaction/executor ownership, async handoff, and first application boundary.
5. **Inspect hangs.** Capture the last completed boundary and 2–3 time-separated thread dumps; compare states, monitor owners, lock cycles, executors, connection pools, and downstream latency.
   - Identify the exact PID, run `jcmd <pid> help`, then check supported commands. For hangs, inspect `jcmd <pid> help Thread.print` before `jcmd <pid> Thread.print -l`.
6. **Inspect memory/GC.** Preserve exact OOM subtype, heap/metaspace/direct/native/thread limits, container limit, existing GC logs, and allocation/retention trend.
   - Distinguish Java-heap retention, metaspace/classloader, direct buffers, native memory, thread creation, and container pressure.
7. **Profile performance.** Hold workload, artifact, JVM, resources, and warm-up constant; separate application CPU/allocation/locks/I/O from JIT, GC, dependency, and environment effects.
   - Use bounded JFR only on local or explicitly authorized targets after `jcmd <pid> help JFR.start`; record settings, duration, destination, and overhead.
8. **Compare one factor.** Use a non-corrective local comparison: same artifact under recorded/expected JDK or same focused task in working/failing environment. Do not change dependencies, source, flags, data, infrastructure, or production to hide the symptom.

## Evidence Signals

| Symptom | Required discriminator |
| --- | --- |
| Compile/build | First compiler diagnostic; build JVM/toolchain; release/source/target; source set; generation/processor output. |
| Missing class/init | Requested class, loader, graph, runtime class/module path, nested initializer failure. |
| Linkage error | Loaded caller/callee origins, selected dependency paths, and `javap` signatures. |
| Bytecode/module access | Runtime JVM, class major version, artifact identity; caller/target modules, module path, launch flags. |
| Exception/hang | Full cause chain and first application frame; repeated dumps showing stable owner/cycle versus waiting/starvation/downstream delay. |
| OOM/crash/performance | OOM subtype and limit/retention evidence; `hs_err_pid*.log` signal/problem frame/native origin; faithful baseline and matched profile. |

## Guardrails

- Diagnose only: no source/build/dependency/data/infrastructure/production changes; route the smallest proposed correction through Execute.
- Do not run `clean`, purge caches, refresh dependencies, edit builds, persist JVM flags, add `--add-opens`, raise limits, restart, or deploy.
- Build/test tasks execute plugins or application code; use only known targets in a safe local/sandboxed scope. Record disposable `target/`, `build/`, cache, or download side effects.
- Heap dumps, live histograms, NMT, native/core capture, and attach operations may pause processes, consume disk, or expose secrets; require explicit need, impact/storage review, and authorization.
- Never attach broadly with PID `0` or a partial class match. Obtain explicit authorization before profiling or attaching to a non-local JVM.
- Redact credentials, tokens, customer data, environment/system properties, heap content, paths, diagnostics, and profiles; stop at cause and evidence.
