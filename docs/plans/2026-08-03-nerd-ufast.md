# Nerd UFast Prompt-Only Plan

## Goal

Establish a minimal prompt-only UFast baseline before adding specialized tools.

## Work

1. Remove the five bundled runtime modules, the MCP installer, calibration
   fixtures, telemetry, and tool-only tests.
2. Rewrite `skills/nerd-ufast/SKILL.md` around context, action, and proof waves.
3. Make installation uniform across Codex, Claude Code, and Cursor with no
   UFast-specific flag or runtime configuration.
4. Isolate both benchmark arms from user configuration and reject runtime or
   UFast-tool evidence in the prompt-only report.
5. Run one unchanged case once with Luna and once with Terra, judge and score
   all four workloads, and publish the measured result without a speed claim.

## Verification

- UFast has no `scripts/` directory.
- The repository contract and skill validator pass.
- Benchmark planning yields exactly four workloads and two pairs.
- Both result directories share the frozen prompt and harness hashes.
- All workloads pass external proof with valid blind judging and no hard gates.
- README evidence is generated from the accepted result summary.

## Later

Add tools individually. Each tool must earn its complexity with an isolated
benchmark against this prompt-only baseline.
