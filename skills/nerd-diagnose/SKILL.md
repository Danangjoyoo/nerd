---
name: nerd-diagnose
description: Use when establishing why behavior is broken, unexpected, or inconsistent and reporting a confirmed, probable, or unknown cause without performing repair.
---

# Nerd Diagnose

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

<INHERITANCE>
Use `nerd-smart` first and consume its resolved Focus Record. This route accepts
only the **Diagnose** endpoint. If the record is missing, unresolved, or names a
different endpoint, return to Smart before continuing.
</INHERITANCE>

## Diagnosis Type Mappings

Match the observed symptom to exactly one closest row. Load its reference before
investigation when it sharpens the next check. Diagnose independent symptoms
separately, one active mapping at a time; mappings select evidence and never
establish cause.

| # | Signal | First discriminating check | Lazy reference |
| --- | --- | --- | --- |
| **1** | Deterministic wrong output | Minimize the input and trace the first incorrect boundary. | [Wrong output](references/types/deterministic-wrong-output.md) |
| **2** | Intermittent or flaky | Repeat while recording seed, time, order, load, and concurrency. | [Intermittent or flaky](references/types/intermittent-flaky.md) |
| **3** | Crash or exception | Capture the smallest trigger and first relevant stack frame. | [Crash or exception](references/types/crash-exception.md) |
| **4** | Hang or timeout | Find the last completed boundary and inspect blocked work. | [Hang or timeout](references/types/hang-timeout.md) |
| **5** | Performance regression | Compare the same workload and profile with a known baseline. | [Performance regression](references/types/performance-regression.md) |
| **6** | State or data corruption | Trace reads, writes, and transformations against one invariant. | [State or data corruption](references/types/state-data-corruption.md) |
| **7** | Integration or API failure | Capture sanitized request, response, auth, serialization, and retry signals. | [Integration or API](references/types/integration-api-failure.md) |
| **8** | Build, compile, or type failure | Start from the first causal diagnostic using the exact toolchain. | [Build, compile, or type](references/types/build-compile-type-failure.md) |
| **9** | Environment or configuration mismatch | Diff effective runtime, configuration, and dependencies. | [Environment or configuration](references/types/environment-config-mismatch.md) |
| **10** | Visual or UI mismatch | Capture viewport, rendered state, events, and relevant network activity. | [Visual or UI](references/types/visual-ui-mismatch.md) |

## Tech Stack Mappings

Detect stacks from repository files, runtime evidence, and the failing boundary.
Load only the stack references needed for that boundary. Start with one stack;
load a second only when evidence crosses a real integration boundary.

| Stack | Primary evidence | Lazy reference |
| --- | --- | --- |
| Kotlin | Gradle, JVM traces, coroutines, framework logs | [Kotlin](references/stacks/kotlin.md) |
| Java | Maven/Gradle, JVM traces, threads, classpath | [Java](references/stacks/java.md) |
| Python | Environment, traceback, imports, sync/async runtime | [Python](references/stacks/python.md) |
| Ruby | Bundler, backtrace, Rails/RSpec, persistence boundary | [Ruby](references/stacks/ruby.md) |
| TypeScript | `tsconfig`, compiler, source maps, emitted runtime | [TypeScript](references/stacks/typescript.md) |
| JavaScript | Node/browser runtime, event loop, source maps | [JavaScript](references/stacks/javascript.md) |
| Docker | Engine/context, images, containers, logs, networks, volumes, Compose model | [Docker and Compose](references/stacks/docker.md) |
| Kubernetes | Workload state, events, logs, probes, resources | [Kubernetes](references/stacks/kubernetes.md) |
| Terraform | Configuration, plan, state, providers, drift | [Terraform](references/stacks/terraform.md) |
| Redis | Key shape, TTL, memory, latency, clients | [Redis](references/stacks/redis.md) |
| MySQL | Query plan, locks, schema, indexes, server state | [MySQL](references/stacks/mysql.md) |
| PostgreSQL | Query plan, statistics, locks, schema, settings | [PostgreSQL](references/stacks/postgresql.md) |
| Go | Focused tests, errors, races, goroutines, profiles | [Go](references/stacks/go.md) |
| Rust | Cargo graph, features, compiler, panic, ownership | [Rust](references/stacks/rust.md) |

## Framework Mappings

Detect frameworks from dependency manifests, generated artifacts, configuration,
and runtime evidence. Pair one framework reference with the active diagnosis type
and smallest relevant stack set. Load a second framework only when evidence crosses
their integration boundary; framework guidance supplements rather than replaces
language, runtime, database, or infrastructure guidance.

| Framework | Primary evidence | Lazy reference |
| --- | --- | --- |
| Spring Boot | Profiles, auto-configuration, beans, routes, Actuator, web runtime | [Spring Boot](references/frameworks/springboot.md) |
| jOOQ | Dialect, generated schema, rendered SQL, binds, execution lifecycle | [jOOQ](references/frameworks/jooq.md) |
| FastAPI | ASGI lifecycle, routes, dependencies, validation, middleware | [FastAPI](references/frameworks/fastapi.md) |
| Ruby on Rails | Boot, routes, Zeitwerk, callbacks, Active Record, requests/jobs | [Ruby on Rails](references/frameworks/ruby-on-rails.md) |
| Sidekiq | Job lifecycle, queues, retries, concurrency, Redis | [Sidekiq](references/frameworks/sidekiq.md) |
| React | Props/state, render/commit, Effects, hydration, browser events | [React](references/frameworks/reactjs.md) |
| gRPC | Protobuf contract, metadata, deadlines, status, streaming, transport | [gRPC](references/frameworks/grpc.md) |

## General Discipline

Use this discipline internally. Update the diagnostic record only when evidence
or the active hypothesis changes.

| Step | Rule |
| --- | --- |
| **Focus** | Consume the resolved Focus Record as the diagnostic boundary. Treat a suggested cause as a hypothesis, not evidence. |
| **Observe** | Capture inputs and expected versus actual behavior. Reproduce when possible; otherwise preserve the evidence gap. |
| **Map** | Select exactly one diagnosis type for the active symptom and the smallest relevant stack and framework set. Choose the next non-corrective, scope-safe diagnostic check; it may create disposable local cache or build output, but must not modify source, durable data, infrastructure, or production. |
| **Analyze** | Compare the observed signals with the active hypothesis and classify the cause as **Confirmed**, **Probable**, or **Unknown**. |

## Diagnose

Gather discriminating evidence and keep one active hypothesis. Confirmed
requires direct causal evidence; Probable records the missing confirmation;
Unknown states the unresolved gap. Use `nerd-surgery` only when a systematic
debugging specialty materially improves the investigation. Surgery must
preserve the Diagnose endpoint and cannot repair.

Use the [diagnosis template](references/diagnosis-template.md) for a current
failure and the [RCA template](references/rca-template.md) for a retrospective
incident. Load only the matched template. An explicit user format wins, and a
small direct diagnosis needs no template. Persist an artifact only when the
user requests it, supplies a path, or an established repository workflow
requires it.

Stop at cause and evidence. Do not repair, edit, or execute corrective actions.
Do not modify source or durable artifacts, data, or infrastructure. A diagnostic
command may create disposable local cache or build output when required to
observe the failure. Confirm an Execute endpoint through Smart before repair.
