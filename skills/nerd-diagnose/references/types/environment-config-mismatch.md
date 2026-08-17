# Environment or Configuration Mismatch

Scope:

- Use when the same input or path differs across environments and runtime, dependency, platform, or configuration may explain it.
- Remap same-environment defects, matched-environment API failures, and identified source/type build errors.

## Capture

- Failing input, command/request, timestamp, expected and observed result, and closest working run.
- Context identity and provenance: host, container image, CI runner, or equivalent.
- Effective runtime/tool versions, dependency graph, OS/architecture, locale/timezone, working directory, and executable/library paths.
- Relevant environment-variable presence, flags, endpoints, and application settings as observed by the failing process.
- Each effective value's source and precedence, plus a redacted structured diff of relevant fields.
- Active hypothesis, predicted signal, controlled factor/result, uncontrolled differences, inaccessible contexts, and withheld secret evidence.

## Diagnose

1. **Fix the comparison frame.** Compare the failing and closest working runs at like-for-like lifecycle phases.
   Compare CI build with developer runtime only when that boundary is the hypothesis.
2. **Capture effective state.** Prefer process-observed values over declarations and identify runtime provenance.
3. **Trace provenance and precedence.** Map each relevant winner through built-in default,
   config file/profile, environment, command line, injected secret/config object, and remote flag.
   Distinguish absent, explicitly empty, and inherited values; check default drift across app,
   runtime, tool, image, and dependency versions.
4. **Build a redacted structured diff.** Start with symptom-relevant fields and preserve name,
   effective type/shape, source, precedence, and sanitized value or fingerprint.
   For secrets, record only presence, source, version/identifier, length/format class, and a safe
   digest when policy permits; never print, persist, transmit, or compare plaintext.
5. **Locate the causal layer.** Classify differences as application config, runtime/toolchain,
   resolved dependency, OS/architecture/locale/timezone/path, container/host, CI injection,
   remote flag, or external service/network policy. Prefer the earliest layer reaching the failure.
6. **Discriminate one factor.** State the predicted signal and correlate it with existing runs.
   If needed, replay the same input in a disposable local process or sandbox with only that factor varied.
   Record the override and restore/discard the sandbox; never silently align, edit, or restart a real environment.
7. **Recheck competitors.** A difference is causal only if precedence and data path reach the symptom
   and a controlled or natural one-factor variation toggles the prediction with other factors controlled.
   Mark mere co-occurrence incidental and test the next candidate.

## Guardrails

- Do not combine simultaneous differences into one experiment or choose a cause by plausibility alone.
- Stop after classification, causal evidence, incidental differences, and the smallest prescription; do not apply it.
- Do not modify source, durable data, config stores, infrastructure, CI, containers, hosts, remote flags, secrets, or production.
- Diagnostic commands may create named, secret-free disposable local artifacts or isolated process state; discard them when no longer useful.
- When unresolved, name the missing confirmation and exactly one next diagnostic check.
- Apply the parent Confirmed/Probable/Unknown gate.
