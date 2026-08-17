# Python Diagnosis

## Scope and provenance

- Use for the Python boundary; keep the active diagnosis-type reference authoritative.
- Treat the shell, IDE label, and activated prompt as untrusted until runtime identity agrees.
- Choose the repository-native runner: existing `uv`, Poetry, Pipenv, Hatch, tox/nox, venv, container, or task command.
- Never create, install, sync, upgrade, or relock an environment for diagnosis.
- Let `<py>` mean the verified interpreter command; never type the placeholder literally.
- Official anchors: interpreter flags, `importlib`, `importlib.metadata`, `traceback`, `faulthandler`, `asyncio`, `pytest`/`unittest`.

```sh
<py> -VV
<py> -c 'import os,platform,sys; print(sys.executable,sys.prefix,sys.base_prefix,platform.python_implementation(),platform.platform(),os.getcwd(),sep="\n")'
<py> -m pip --version
```

- Record runner, executable, version, implementation, platform, venv state, cwd, origin, image digest, and config source; missing `pip` is evidence, not permission to install it.

## Diagnose

1. **Fix invocation:** capture sanitized argv, cwd, relevant config, expected/actual result, and terminal/IDE/server/worker/subprocess context.
2. **Compare identity:** run provenance in working and failing contexts; resolve interpreter, version, platform, cwd, `sys.path`, package, or runner drift first.
3. **Capture failure:** preserve separate stdout/stderr, sanitized logs, and the full chained traceback; start at the earliest relevant application frame.
4. **Check imports:** inspect targeted resolution without importing when safe:

```sh
<py> -c 'import importlib.util,sys; print(*sys.path,sep="\n"); s=importlib.util.find_spec("PACKAGE"); print(None if s is None else s.origin)'
```

5. **Minimize faithfully:** use one existing command, fixture, job, or configured test: `<py> -m pytest path::test` or `<py> -m unittest package.tests.Case.test`.
6. **Inspect one branch:** change one diagnostic variable; preserve plugins/config unless they are the hypothesis.
7. **Classify:** apply the parent **Confirmed / Probable / Unknown** gate; stop at cause.

## High-signal branches

- **Packaging:** lock/config selected, environment identity, and targeted `<py> -c 'import importlib.metadata as m; print(m.version("DISTRIBUTION"))'`; import and distribution names can differ.
- **Imports:** ordered redacted `sys.path`, cwd, `find_spec()` origin, namespace layout, same-named files; dotted `find_spec()` may import its parent.
- **Exception/wrong result:** smallest input, complete cause/context chain, earliest relevant frame, value shapes, violated invariant.
- **Tests/types:** first causal diagnostic, exact target/config/interpreter; distinguish collection/import failure from assertion failure.
- **Async:** task/cancellation/loop ownership, un-awaited coroutine warnings, blocking call, library versions.
- **Threads/processes:** stacks, locks, queues, PID lineage, start method, timeout, signal/exit code, child interpreter.
- **Environment:** effective non-secret values and provenance, key presence, flags, locale/timezone, permissions, proxy/network boundary.
- **Native extension:** module/extension origin, Python ABI, OS/architecture, loader error, owning distribution, import versus native-call failure.
- **Performance/memory:** identical workload/baseline, wall/CPU/RSS/allocation signal, hotspot, cache/warmup, concurrency; one sample proves nothing.
- **Subprocess:** executable/argv, cwd, return code/signal, timeout, separate streams, and a narrow environment-key diff.

## Diagnostic aids

- Local fatal native crash: `PYTHONFAULTHANDLER=1 <project-command>`; for a hang, prefer an existing task/thread/process stack-dump hook.
- Suspected asyncio lifecycle: `PYTHONASYNCIODEBUG=1 <project-command>` only in an authorized local reproduction.
- Profile: use project-native tooling, identical workloads, disposable output, and recorded overhead.

## Guardrails

- Avoid imports with startup, network, database, migration, or registration side effects.
- Debug/profiling modes can alter timing; never enable them in production without explicit authorization.
- Redact users, paths, internal indexes/packages, tokens, credentials, connection strings, headers, environment dumps, and payloads.
- Do not edit source, tests, fixtures, lockfiles, durable data, infrastructure, or production.
- Keep disposable bytecode, caches, profiles, traces, or build output identified and non-durable; stop at the parent confidence gate.
