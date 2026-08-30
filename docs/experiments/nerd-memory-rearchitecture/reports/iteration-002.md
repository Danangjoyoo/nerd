# Iteration 002 — Context-Aware Hybrid

## Hypothesis

Replacing global action-level keying with global command transfer plus exact
non-repository context compatibility should improve tool/skill selection and
workflow ordering while preserving unseen-repository action transfer and
eliminating incompatible provenance.

## Artifact and data revision

- Model: `M2`
- Result digest: `sha256:d9331e58ebf17994b6aa892d4418084228c19814970437951f26afec057eb8c2`
- Dataset: `synthetic-chronological-v1`
- Dataset digest: `sha256:01a95c2dc297faa3c9f4827e0bcbfa0aec418a8f6dac6ada0a52f1b1259faa98`
- Seeds: development `11`, `17`, `23`
- Split: unchanged chronological 60% / 20% / 20%

## Control and intervention

- Control: M1 and frozen B0–B3 on the same fixtures.
- Intervention: only the prediction key/ranker changes. Action cues and
  resource votes are constrained by language, surface, and project kind;
  repository is excluded so compatible experience can transfer globally.
- Still absent: verified-only evidence admission, learned output guard,
  contradiction retirement, and calibrated confidence abstention.

## Metrics

| Measure | M2 result | Threshold |
| --- | ---: | ---: |
| Tool/skill macro set-F1 | 1.0000 | diagnostic |
| Gain over best B0-B2 | +0.2336 | >= 0.08 |
| Workflow edge-F1 | 1.0000 | diagnostic |
| Workflow gain over best B0-B2 | +0.3020 | >= 0.10 |
| Mandatory-edge violation | 0% | < 5% |
| Unseen-repository action gain over B2 | +1.0000 | >= 0.10 |
| Cross-context contamination | 0% | < 2% |
| Invalid-output recall | 0% | >= 90% |
| Severe false acceptance | 15 | 0 |
| Obsolete usage after three corrections | 47.22% | < 10% |
| Median / p95 prediction runtime | 0.0241 / 0.0260 ms | < 5 / < 10 ms |

Verdicts: H1, H2, H3, and H5 `PASS`; H4 and H6 `FAIL`; H7 `UNTESTED`.

## Result and disconfirming evidence

The contextual hypothesis was supported on development fixtures: the same
global corpus transferred to unseen repository labels with zero incompatible
source references. H2 and H3 cleared their margins by 0.1536 and 0.2020,
respectively.

The perfect selection and workflow scores expose a synthetic-ceiling risk:
fixture contexts are separable and stable, so this does not establish behavior
under noisy or missing context. Naive evidence admission also happened not to
damage majority selection despite rejected traces; that absence of measured
damage is not proof that failures are safe to learn. M2 still accepted every
invalid output and retained 47.22% obsolete-tool support after three direct
corrections.

## Decision and next focus

Retain the M2 representation and ranker. Change only the evidence-admission
policy to M3's predeclared verified/correction-aware/guarded/abstaining policy.
Iteration 3 must close H4 and H6 without reopening H2, H3, or H5, then freeze
M3 before the untouched holdout gate.
