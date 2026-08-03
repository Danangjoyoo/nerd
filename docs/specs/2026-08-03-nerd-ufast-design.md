# Nerd UFast Prompt-Only Design

## Outcome

UFast is an explicitly invoked, prompt-only speed modifier. It preserves the
active workflow's correctness contract while compressing supported work into:

1. one batched context wave;
2. one batched action wave; and
3. one V0/V1 proof decision.

The skill uses only platform-provided tools. It ships no executable scripts,
MCP server, registry, language server, AST engine, or hidden runtime.

## Positioning

- Fast reduces critical-path latency adaptively without lowering accuracy.
- XFast uses native text/patch operations and deliberately accepts reduced
  exploration, completeness, accuracy, and proof.
- UFast preserves accuracy but enforces a strict three-wave prompt discipline.

UFast and XFast never compose.

## Execution Contract

### Context wave

Lock the smallest outcome, known targets, and required proof. Skip discovery
when the path is already known. Otherwise batch all independent reads and
searches in one native call, with at most one focused follow-up for a material
dependency.

### Action wave

Batch all known mutations in one native patch/edit operation. Put focused test
changes in the same wave as behavior changes. UFast overrides intermediate
red-green sequencing, but not the active workflow's final proof requirement.

### Proof decision

- V0 reuses fresh directly relevant evidence or makes no verification claim.
- V1 automatic runs one safe, local, focused proof wave.
- V1 ask first covers broad, slow, stateful, external, destructive,
  configuration-dependent, or newly authorized proof.

Stop after the first sufficient green result. Leave the three-wave path when
the work becomes ambiguous, unsafe, or genuinely iterative.

## Deferred Tools

Future tools are intentionally out of scope. Add one deterministic capability
at a time only after defining its contract, isolation boundary, fallback, and a
paired benchmark against this prompt-only baseline.
