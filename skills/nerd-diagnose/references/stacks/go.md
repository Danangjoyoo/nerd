# Go Diagnosis

- Load after Go evidence reaches the active failure boundary.
- Keep one hypothesis; apply the parent **Confirmed / Probable / Unknown** gate.

## Capture

- Record symptom, minimal input, package/test/binary, revision/dirty state, working directory, runner, OS/architecture, limits, exact command, tags, seed, arguments, and relevant redacted environment.
- Capture `go version` and `go env -json GOVERSION GOOS GOARCH GOHOSTOS GOHOSTARCH GOROOT GOTOOLDIR GOMOD GOWORK GOTOOLCHAIN GOFLAGS CGO_ENABLED CC CXX`.
- Capture `go list -m -json`; use `go version -m <binary>` for an existing failing binary.
- Record target knobs (`GOAMD64`, `GOARM64`, `GOARM`) and compiler/native-library identity when cgo matters.
- Query named environment values only. Inspect proxy/private-module settings only for module-access hypotheses; redact credentials, URL userinfo, private modules, paths, and CI metadata.

## Diagnose

1. **Separate stages.** Find the first loader/compiler/vet/generator/runtime diagnostic. Compile the smallest package with `go test -run '^$' -count=1 ./path/to/pkg`; preserve tags, target, cgo, and `GOFLAGS`.
   - The test binary still starts and may run initialization or `TestMain`; use a safe target.
   - Treat vet separately; use `-vet=off` only as a recorded one-variable comparison.
   - Build an exact non-test package into a disposable directory. Never run `go generate`; inspect directives, generator versions, headers, and existing logs.
2. **Resolve inputs.** Compare `GOMOD`, `GOWORK`, `go.mod`, `go.sum`, `go.work`, `replace`, vendor mode, selected toolchain, and build tags/files.
   - Use `go list -m -json all` only when graph evidence is causal and private/network access is authorized.
   - Use `GOWORK=off` only as a recorded comparison; do not edit modules/workspaces or run `go get`, `go mod tidy`, or `go work sync`.
3. **Focus the test.** Run `go test -run '^TestName$/^subtest$' -count=1 -json ./path/to/pkg`; retain events, exit status, elapsed time, and flags.
   - Use `-count=N` for repeatability; record and replay `-shuffle` seeds. Compare `-p=1` and `-parallel=1` separately.
   - Replay an existing fuzz seed/corpus input; do not start broad or unbounded fuzzing. A timing change is sensitivity evidence, not a race.
4. **Trace failures.** Preserve concrete error and wrapping chain, operation/input, panic value, full stack, first application frame, and `recover` boundary. For a focused local case, `GOTRACEBACK=all` adds user-goroutine stacks.
5. **Test races.** Run the smallest exercised path: `go test -race -run '^TestName$' -count=1 ./path/to/pkg`.
   - A clean run covers only executed paths. The detector needs cgo, a supported target, and often a C compiler; the `race` tag changes selection.
   - Expect roughly 2–20x runtime and 5–10x memory; never use race-mode latency or allocation as a production baseline.
6. **Inspect hangs.** Bound a focused test with `go test -run '^TestName$' -count=1 -timeout=30s ./path/to/pkg`; compare repeated goroutine dumps.
   - Trace channel ownership, mutex order, WaitGroup balance, goroutine growth, and context creation/propagation.
   - Distinguish cancellation from deadline expiry, upstream budget from inner timeout, and blocked dependency from leaked work.
7. **Measure performance.** Keep workload, toolchain, target/tags/cgo, resources, `GOMAXPROCS`, warmup, and samples identical; run `go test -run '^$' -bench '^BenchmarkName$' -benchmem -count=5 ./path/to/pkg`.
   - Attribute CPU, wall time, allocations/retained heap, GC, blocking, and mutex contention separately.
   - Collect one disposable profile at a time (`-cpuprofile`, `-memprofile`, `-blockprofile`, `-mutexprofile`) and inspect with `go tool pprof -top <profile>`.
   - Use `-trace <file>` / `go tool trace <file>` for scheduler, syscall, GC, or serialization evidence—not as a CPU-hotspot substitute.
8. **Check boundaries.** Preserve concrete I/O/network/cgo error type, sanitized endpoint/path, operation, deadline source, retries, reuse, DNS/TLS evidence, limits, dependency latency, target, linker/compiler, and native library provenance.

## Evidence Signals

| Symptom | Required discriminator |
| --- | --- |
| Build/generated mismatch | First diagnostic; toolchain, tags/files, target/cgo, module/workspace; generator provenance without execution. |
| Wrong result/error/panic | Minimal input; first wrong operation; error chain or panic/stack/recover boundary. |
| Flaky/race/deadlock | Rate, events/seed, isolated concurrency checks; race report or repeated blocked stacks and ownership. |
| Timeout/cancellation | Context owner, budget, `ctx.Err()`, last boundary, dependency latency, blocked stack. |
| CPU/memory/GC | Faithful baseline, samples, one matched profile; allocations versus retained heap. |
| Environment/boundary | One controlled factor plus exact Go/runner/module settings and concrete sanitized boundary evidence. |

## Guardrails

- Diagnose only: no source/generated/module/workspace/data/infrastructure/production changes; route corrections through Execute.
- Allow only required disposable local cache/build/profile output; record paths and keep artifacts outside the repository when possible.
- Never use `go env -w/-u`, broad `./...`, network graph access, or unknown generators when narrower local evidence discriminates.
- Use existing authenticated pprof only; never expose a new endpoint. Profile/trace only with authorized overhead and safe storage.
- Treat `SIGQUIT` as interrupting and potentially terminating; never send it to production without explicit authorization.
- Redact profiles, traces, logs, private-module data, credentials, and customer inputs; stop at cause and evidence.
