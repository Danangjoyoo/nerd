# JavaScript Diagnosis

- Use for a JavaScript boundary after selecting one diagnosis type.
- Diagnose only; apply the parent skill's confidence gate and stop before repair.

## Select and Record

- Runtime: Node, browser, worker, service worker, edge, or embedded; exact version.
- Node provenance: `node --version`; record platform, architecture, and `process.versions` only when relevant.
- Package model: nearest `package.json`, `engines`, `packageManager`, `type`, `exports`, `imports`, workspace.
- Dependency source: committed lockfile and its package manager; never substitute managers.
- Invocation: exact script, directory, `pre*`/`post*` hooks, test runner, and environment names.
- Artifact: source entry, emitted/bundled asset, mode, target, build ID/hash, source map, cache use.
- Browser: version, origin, viewport, frame/worker, served asset URL, cache/service worker, extensions.
- If local provenance differs from the failing runtime or asset, record the gap.

## Diagnose

1. Freeze the smallest trigger, expected/actual result, frequency, timestamp/request ID, exit status, and full first error.
2. Reproduce through the lockfile-selected manager and an existing repository script; inspect script effects first.
3. Verify the executing file or served asset, resolved package path/version, generated location, and matching source map.
4. Classify the first divergence: module load, sync execution, async continuation, scheduling, I/O/stream, dependency, DOM/network/policy, or environment.
5. State one hypothesis and predicted signal; change one diagnostic condition while keeping input, runtime, and artifact fixed.
6. Recheck uninstrumented conditions, classify through the parent gate, and stop.

## Failure Signals

- **Module/load:** correlate importer, `.js`/`.mjs`/`.cjs`, package `type`, import versus `require`, `exports` condition, and resolved file; separate Node resolution from bundler/test transforms.
- **Build-only:** map the generated frame to the emitted chunk, target, defines/polyfills, minification, tree-shaking, and source map; source presence does not prove shipment.
- **Throw/exit:** retain the first throw, `cause`, suppressed context, generated stack, exit code, and signal.
- **Promise/async:** distinguish the original rejection from a later handler error; record create/await/handler timing and cancellation or timeout owner.
- **Order/hang:** timestamp tasks, microtasks, timers, I/O, worker messages, and long sync callbacks; do not call ordering alone a race.
- **Stream:** record rates, buffers, `.write()` result, backpressure, `drain`/`finish`/`close`/`error`, abort, and ownership.
- **DOM/UI:** capture DOM/state around the event, target/propagation, frame/shadow root, console error, render, and worker messages.
- **Network:** capture final URL, initiator, redirects, status, timing, content type, sanitized headers/body shape, cache/service-worker source, and relevant CORS/CSP/origin signal.
- **Dependency/native:** record lockfile version/path, duplicates, peer/optional state, platform/architecture, Node ABI, and loader error.
- **Environment:** diff runtime/browser, invocation, artifact, non-secret config, flags, locale/time zone, permissions, proxy/CA, and filesystem behavior.

## Focused Evidence

- Use `node --test <file>` only when the repository uses Node's test runner; never guess runner flags.
- On supported Node versions, verify diagnostic flags with `node --help` before use.
- `node --enable-source-maps <entry>` may aid a local reproducer; retain the generated frame as ground truth.
- `--trace-uncaught`, `--trace-warnings`, and strict rejection mode change or expand evidence; they do not alone prove production behavior.
- CPU: compare the same workload/baseline; a supported local run may use `--cpu-prof --diagnostic-dir=<disposable-dir>`.
- Memory: compare equivalent warm-up/workload and separate retention, allocation/GC, RSS, and native buffers; a supported local run may use `--heap-prof --diagnostic-dir=<disposable-dir>`.
- Browser DevTools: preserve Console, Network, Performance, and source-map evidence tied to the actual served asset.

## Guardrails

- Do not install/update packages, alter lockfiles, rebuild native addons, edit source/config, clear shared caches, or mutate durable state/infrastructure.
- Keep reproducers, builds, profiles, reports, and caches in explicit disposable local paths; report cleanup needs.
- Never attach inspectors/profilers or collect heap dumps in production without separate authorization; they perturb runtime and may expose data.
- Redact tokens, cookies, storage, request bodies, heap contents, paths, personal data, and internal network details.
- Cache bypass, service-worker bypass, throttling, tracing, and profilers alter execution; confirm against original conditions.
- Unsupported commands or flags: verify against the detected tool version or omit them.
