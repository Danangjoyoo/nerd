# Iteration 001 — Simple Counts

## Hypothesis

Simple counts should prove deterministic capture and basic command-to-action
reuse, but should fail when one action maps to different tools, skills, and
steps across contexts. Invalid-output rejection, contradiction retirement, and
calibrated abstention are intentionally absent.

## Artifact and data revision

- Model: `M1`
- Result digest: `sha256:faa3bb765ca5ed52a59cebe70387262876a740ea1298c92504e452c385b1ef4f`
- Dataset: `synthetic-chronological-v1`
- Dataset digest: `sha256:01a95c2dc297faa3c9f4827e0bcbfa0aec418a8f6dac6ada0a52f1b1259faa98`
- Seeds: development `11`, `17`, `23`
- Split: chronological 60% train / 20% calibration / 20% test per seed

## Control and intervention

- Controls: B0 no memory, B1 global majority, B2 hard repository partition,
  and B3 oracle ceiling.
- Intervention: cue-to-action counts plus action-level majority tools, skills,
  and ordered steps. No repository or context key is used.

## Metrics

| Measure | M1 result | Relevant threshold |
| --- | ---: | ---: |
| Capture reconstruction | 1.0000 | 1.0000 |
| Persisted seeded-secret leaks | 0 | 0 |
| Action accuracy | 1.0000 | diagnostic |
| Tool/skill macro set-F1 | 0.6275 | gain >= 0.08 |
| Gain over best B0-B2 | -0.1389 | >= 0.08 |
| Workflow edge-F1 | 0.5356 | diagnostic |
| Workflow gain over best B0-B2 | -0.1624 | >= 0.10 |
| Mandatory-edge violation | 46.44% | < 5% |
| Invalid-output recall | 0% | >= 90% |
| Severe false acceptance | 15 | 0 |
| Cross-context contamination | 42.86% | < 2% |
| Obsolete usage after three corrections | 36.51% | < 10% |
| Median / p95 prediction runtime | 0.0266 / 0.0274 ms | < 5 / < 10 ms |

Verdicts: H1 `PASS`; H2–H6 `FAIL`; H7 `UNTESTED`.

## Result and disconfirming evidence

The expected failure was observed. Exact command cues made action accuracy look
perfect, but this did not transfer to the resources and order required to carry
out the action. M1 underperformed B2 by 0.1389 macro set-F1 and contaminated
42.86% of transfer provenance with incompatible contexts. Global action
accuracy alone is therefore a misleading proxy for behavioral usefulness.

The unknown-fixture abstention rate was 100% because unseen cues had no count;
this is a natural empty lookup, not evidence that M1 can handle ambiguous known
cues. Runtime is comfortably bounded but says nothing about H7's live-agent
token or task-success effects.

## Decision and next focus

Keep the dataset and baselines frozen. Change only the key/ranking strategy to
the context-aware global hybrid in M2. The next iteration must test whether
compatible cross-repository reuse closes H2, H3, and H5 without adding guard or
correction logic.
