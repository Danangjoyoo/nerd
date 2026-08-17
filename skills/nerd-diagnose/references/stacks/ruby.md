# Ruby Diagnosis

## Scope

- Use for the Ruby runtime boundary; pair with one parent diagnosis type.
- Prefer checked-in binstubs, then `bundle exec`; keep `Gemfile.lock` authoritative.
- Apply the parent **Confirmed / Probable / Unknown** gate and stop at cause.

## Capture

- Runtime: `ruby -v` and `ruby -e 'puts [RUBY_ENGINE, RUBY_VERSION, RUBY_PATCHLEVEL, RUBY_PLATFORM].join(" ")'`.
- Selector: `.ruby-version`, `.tool-versions`, container image, CI config, version manager.
- Bundle: `bundle --version`, `Gemfile.lock`, `bundle platform`, sanitized `bundle config list`.
- Context: included/excluded groups; presence—not values—of `RAILS_ENV`, `RACK_ENV`, and secrets.
- Invocation: exact binstub/command, cwd, arguments, seed, process model, environment names.
- Failure: smallest trigger, expected/actual result, occurrence, timestamp, full cause chain/backtrace.

## Diagnose

1. **Match provenance.** Compare engine, version, platform, bundle, groups, environment, and runner between working and failing paths.
2. **Separate parse from load.** Use `ruby -c path/to/file.rb`; for load failures capture the feature/constant, `$LOAD_PATH`, `Gem.loaded_specs`, groups, and locked platforms.
3. **Narrow faithfully.** Use one existing target: `bin/rspec path/to/spec.rb:LINE`, `bin/rails test path/to/test.rb:LINE`, the project Minitest command, or `bundle exec ruby path/to/reproducer.rb`.
4. **Preserve execution semantics.** Keep seed, ordering, request/job payload shape, environment, concurrency, and repository configuration fixed.
5. **Trace the first divergence.** Start at the first application-owned frame; follow only the relevant caller, callback, gem, query, request/job, thread, or native boundary.
6. **Test one hypothesis.** State its prediction; change at most one disposable diagnostic factor; record exit status, trace, logs, queries, timing, or runtime state.
7. **Route framework evidence.** Treat Rails boot, initializers, middleware, callbacks, and autoloading as context; load the Rails reference for deeper framework diagnosis.
8. **Classify and stop.** Record causal evidence or the exact remaining gap; do not repair.

## Signals

- **Parser/load/gems:** distinguish syntax, `require`, autoload, and Bundler resolution; a global `ruby` success does not disprove a bundle failure.
- **Exceptions:** retain nested causes and the unfiltered trace; check where rescue, retry, callbacks, or middleware replaced the original error.
- **Rails/autoload:** correlate constant, namespace, file, acronym, eager-load path, and safe local `bin/rails zeitwerk:check`; avoid production boot.
- **Requests/jobs:** correlate sanitized request/job IDs, serialized payload, adapter, retries, timeout, and downstream boundary; never replay mutations.
- **Active Record:** capture sanitized SQL/binds, connection, pool wait, transaction/savepoint, callback, isolation assumption, and commit/rollback evidence.
- **Threads/fibers/processes:** record engine, process model, identities, pools, locks, queues, and last completed boundary; do not assume MRI scheduling applies to JRuby or TruffleRuby.
- **Native extensions:** match engine, ABI, architecture, locked platform, extension version, loader, and host; preserve loader/compiler output.
- **Performance/memory:** compare identical workload, data, warm-up, concurrency, engine, GC settings, and dependencies; attribute with approved metrics/profile and record overhead.

## Guardrails

- Diagnose only: no source, dependency, lockfile, durable-data, infrastructure, or production-config changes.
- Do not run `bundle install`, `bundle update`, `bundle lock`, `bundle pristine`, `gem pristine`, migrations, repair tasks, record writes, or job enqueueing.
- Use `EXPLAIN` only on an authorized read-only/disposable database; `EXPLAIN ANALYZE` requires explicit disposable-database authorization because it executes the statement.
- Do not attach debuggers/profilers, signal processes, increase production logging, or dump memory without explicit authorization.
- Redact secrets, personal data, internal paths, SQL binds, payloads, and `bundle config` values; note diagnostic overhead.
- Keep disposable caches, logs, profiles, and build output outside tracked source where practical.

## Official Anchors

- [Ruby documentation](https://docs.ruby-lang.org/) · [Bundler guides](https://bundler.io/guides/) · [Rails autoloading guide](https://guides.rubyonrails.org/autoloading_and_reloading_constants.html)
