# Nerd UFast Prompt-Only Baseline Research

## Decision

The initial tool-backed UFast implementation was too broad for a first step. It
combined project indexing, search, transactional editing, test selection, MCP
transport, installer wiring, telemetry, and reporting before a prompt-only
baseline was established.

UFast now starts with `SKILL.md` instructions only, plus UI metadata. The tool
runtime, installer, and calibration artifacts are removed. Specialized tools
can be added one at a time later and measured against this baseline.

## Prompt Discipline

The smallest distinct behavior is a strict three-wave path:

1. batch all known independent context;
2. batch all known mutations; and
3. make one V0/V1 proof decision.

This keeps UFast distinct from XFast. XFast is deliberately lossy; UFast keeps
the active workflow's accuracy and final proof contract. It differs from Fast
by enforcing a fixed wave boundary rather than applying latency reductions
adaptively.

## Benchmark Control

- Case: `xfast-v3-discovery-edit`, byte-identical to the XFast v3 source case.
- Case SHA-256:
  `6f6ba4ea8c190189428deb9e411b63acd9be3026f53cb954614159002e456791`.
- Matrix: one case, one repetition, Luna and Terra, XFast and UFast.
- Total: four isolated Codex workloads and two matched pairs.
- Both conditions ignore user configuration.
- Prompt-only evidence rejects UFast runtime metadata and tool-call telemetry.

The result is directional. One small Python case cannot establish a universal
speedup or predict the value of future deterministic tools.

## Accepted Evidence

Fresh result directories, source hashes, scores, and measured deltas are added
only after the prompt-only source freezes and all four workloads pass.
