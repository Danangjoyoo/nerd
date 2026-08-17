---
name: nerd-review
description: Use when reviewing existing code, implementations, pull requests, or named scopes with stack-aware checks and severity-ranked findings, without edits.
---

# Nerd Review

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

<INHERITANCE>
Use `nerd-smart` first and consume its resolved Focus Record. This route accepts only the **Review** endpoint. If missing, unresolved, or different, return to Smart before continuing.
</INHERITANCE>

## Review Types

Choose exactly one. Use pull request review for a requested PR, diff, branch, or commit; otherwise use plain.

| Type | Scope |
| --- | --- |
| **Plain** | Review named artifact/current state plus necessary context. |
| **Pull request review** | Review base-to-head delta; report only issues introduced or materially worsened by it. |

## Discipline

- **Focus Record**: Review named scope plus only context needed to judge it.
- **Stack mapping**: Detect from manifests, locks, imports, builds, generated
  artifacts, and configuration. Load smallest matching reference set.
- **Levels:** Check every applicable level. Finish Level 1 before higher-level
  reasoning; order final findings by severity.
- **Evidence:** Confirm issue is new, reachable, and not handled elsewhere.
- **Severity:** Prove reachability, trigger, impact, and blast radius. Use lowest
  supported severity; review level never sets severity.
- **Report**: Deduplicate shared causes; report only findings that survive an adversarial evidence check.

## Review Levels

A level identifies the review lens, not impact or confidence.

| Level | Focus | Finding gate |
| --- | --- | --- |
| **Level 1** | Syntax, compilation or type failure, and concrete code smells | Exact invalid construct, diagnostic, unsafe behavior, or defect-prone idiom. |
| **Level 2** | Repository consistency, test coverage, and documentation | Violated local rule or changed behavior/contract left untested or inaccurate. |
| **Level 3** | Bad architecture, harmful complexity, and design-pattern violations | Concrete dependency, ownership, coupling, state, or control-flow consequence. |

- Never report missing tests, docs, abstractions, or patterns alone.
- Tie gaps to changed behavior, repository contract, or credible defect.

## Severity

Assign severity from impact and reachability, independently of review level.

| Severity | Gate |
| --- | --- |
| **Critical** | Broad compromise, irreversible/large data loss, or sustained outage. |
| **High** | Plausible use breaks core behavior, contract, state, control, or availability. |
| **Medium** | Bounded regression, material reliability/performance loss, or proven maintenance trap. |
| **Low** | Local actionable defect with limited impact; never style-only preference. |

## Stack Mapping

Load one; add another only across a real boundary.

| Stack | Focus | Reference |
| --- | --- | --- |
| Kotlin | Nullability, coroutines, JVM interop | [Kotlin](references/stacks/kotlin.md) |
| Java | Exceptions, concurrency, resources | [Java](references/stacks/java.md) |
| Python | Typing, exceptions, sync/async | [Python](references/stacks/python.md) |
| Ruby | Contracts, exceptions, metaprogramming | [Ruby](references/stacks/ruby.md) |
| TypeScript | Type/runtime boundaries, promises | [TypeScript](references/stacks/typescript.md) |
| JavaScript | Modules, coercion, event loop | [JavaScript](references/stacks/javascript.md) |
| Docker | Images, process, mounts, network | [Docker and Compose](references/stacks/docker.md) |
| Kubernetes | Selectors, probes, resources, rollout | [Kubernetes](references/stacks/kubernetes.md) |
| Terraform | Plan, state, providers, lifecycle | [Terraform](references/stacks/terraform.md) |
| Redis | Keys, TTL, atomicity, memory | [Redis](references/stacks/redis.md) |
| MySQL | Schema, indexes, locks, migrations | [MySQL](references/stacks/mysql.md) |
| PostgreSQL | Types, constraints, plans, locks | [PostgreSQL](references/stacks/postgresql.md) |
| Go | Errors, goroutines, interfaces | [Go](references/stacks/go.md) |
| Rust | Ownership, unsafe, errors, async | [Rust](references/stacks/rust.md) |

## Framework Mapping

Pair with its stack; add another only across a real boundary.

| Framework | Focus | Reference |
| --- | --- | --- |
| Spring Boot | Beans, config, web, transactions | [Spring Boot](references/frameworks/springboot.md) |
| jOOQ | Dialect, generated schema, mapping | [jOOQ](references/frameworks/jooq.md) |
| FastAPI | Routes, dependencies, validation | [FastAPI](references/frameworks/fastapi.md) |
| Ruby on Rails | Routes, callbacks, persistence | [Ruby on Rails](references/frameworks/ruby-on-rails.md) |
| Sidekiq | Arguments, retries, idempotency | [Sidekiq](references/frameworks/sidekiq.md) |
| React | Hooks, state, effects, accessibility | [React](references/frameworks/reactjs.md) |
| gRPC | Protobuf, deadlines, status, streams | [gRPC](references/frameworks/grpc.md) |

## Findings

```text
[Severity] Specific title
Location: <path:line or smallest exact scope>
Review level: <Level 1 | Level 2 | Level 3>
Evidence: <trigger and proof>
Impact: <observable consequence>
Direction: <smallest correction outcome; no implementation>
```

- Put findings first; order Critical to Low, then by blast radius.
- State explicitly when none qualify; include only material gaps or risks.
- Skip praise, clean-check lists, style opinions, and walkthroughs.

## Guardrails

- Prefer repository wrappers and narrow, non-mutating checks.
- Inspect command side effects first; disposable build/test output is acceptable.
- Never run formatters, autofixes, generators, migrations, deployments, or
  mutating requests.
- Do not auto-route to `nerd-patrol`. Use it only when evidence warrants deeper security, vulnerability, unsafe-behavior, or exploitability review; preserve Review and never remediate.
- Do not modify the reviewed artifact or write implementation code.
- Stop after findings; confirm endpoint change through Smart.
