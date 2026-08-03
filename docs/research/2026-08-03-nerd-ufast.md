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

The prompt-only source froze at
`f642c02ba14c8405f18984a160cf485501b3e16e`. The benchmark ran from a clean
detached worktree so preserved user changes could not enter the materialized
Smart, Execute, XFast, or UFast prompts.

| Source | SHA-256 |
| --- | --- |
| Case corpus | `6f6ba4ea8c190189428deb9e411b63acd9be3026f53cb954614159002e456791` |
| Smart skill | `0ddb3ce8440e4f6945280fba992566bd58dc074ffcd42ca4e4d683561b5fc591` |
| Execute skill | `abb9cf466fae242c1c53f6c65455e64ce5e6ef17c7e5ca07c83125c7d2c3e06b` |
| XFast skill | `a3657d201205571d045acb0249be74e11eb66f2d211fe81aa86ff0fb7426c0f3` |
| UFast skill | `a5db8498b53ef0dcab2b630ad3c22d5f1de26012fc8d98ce6c6fa72d6c7647bb` |
| Benchmark runner | `fb137511617dd13118b61e51db4bfce4f81a24fb91732a02b4fd879a6a6abc6e` |
| Materializer | `92659940ca024eb33fb8bbd3116c498beb0d0ca33a0cfbcf270d37a83f94660c` |
| Adapter | `a1cf222743b03d7ead2f15cb4bbbfa7d445f93528b24261f7cbd34b18c6e3060` |
| Scorer | `d11b0fe0b51f24403695190d0c0b43bcdd55f4d18d06037eb678bf1ec4548018` |
| UFast reporter | `0a4f74f779597e3b5f46ec040cc77e82999d33e3f3dc5d38ea6f1e83b9d27d8e` |

| Model | Accepted result directory | XFast score | UFast score | XFast latency | UFast latency | XFast tokens | UFast tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | `20260803T062637Z-f642c02-gpt-5.6-luna-high` | 100 | 100 | 53.8499 s | 63.2017 s | 2,264 | 2,721 |
| Terra | `20260803T062917Z-f642c02-gpt-5.6-terra-high` | 100 | 100 | 48.3090 s | 85.3347 s | 1,960 | 3,624 |

All four workloads passed external proof, both blind judges were valid, and no
hard gate failed. Luna completed the three-wave path. Terra encountered an
exact patch-path error, completed correctly under the active workflow, and
honestly reported `UFast prompt path: fell back`.

Across the two pairs, prompt-only UFast matched XFast's 100-point mean score but
was 47.0048% slower and used 52.5418% more output tokens. This baseline does not
show a speed benefit. It gives future single-tool additions a clean result to
beat without conflating several new capabilities at once.
