# Iteration 003 — Refinement Policy

## Hypothesis

Replacing naive evidence admission with the predeclared verified,
correction-aware, guarded, and abstaining policy should close H4 and H6 without
regressing the contextual selection, workflow, or transfer gates established
by M2.

## Artifact and data revision

- Model: `M3`
- Result digest: `sha256:eaadf6045a2179048124a21decdfa76099a396c89bf287b78f6fb1c5745fcb9e`
- Dataset: `synthetic-chronological-v1`
- Dataset digest: `sha256:01a95c2dc297faa3c9f4827e0bcbfa0aec418a8f6dac6ada0a52f1b1259faa98`
- Seeds: development `11`, `17`, `23`
- Split: unchanged chronological 60% / 20% / 20%

## Control and intervention

- Control: frozen M2 representation/ranker and B0–B3.
- Intervention: one composite evidence-admission policy. Positive workflow
  evidence must be verified and accepted or corrected; output-signal guards
  are learned and calibrated; unknown/low-confidence queries abstain; three
  independent verified corrections retire contradicted resource advice.

## Metrics

| Measure | M3 result | Threshold |
| --- | ---: | ---: |
| Tool/skill macro set-F1 | 1.0000 | gain >= 0.08 |
| Gain over best B0-B2 | +0.2336 | >= 0.08 |
| Workflow edge-F1 | 1.0000 | gain >= 0.10 |
| Workflow gain over best B0-B2 | +0.3020 | >= 0.10 |
| Mandatory-edge violation | 0% | < 5% |
| Invalid-output recall | 100% | >= 90% |
| False rejection | 0% | <= 2% |
| Severe false acceptance | 0 | 0 |
| Unseen-repository action gain over B2 | +0.9167 | >= 0.10 |
| Cross-context contamination | 0% | < 2% |
| Known / unknown abstention | 0% / 100% | <= 5% / >= 90% |
| Obsolete usage after corrections 1 / 2 / 3 | 84.72% / 73.54% / 0% | third < 10% |
| Median / p95 prediction runtime | 0.0165 / 0.0172 ms | < 5 / < 10 ms |

Verdicts: H1–H6 `PASS`; H7 `UNTESTED`.

## Result and disconfirming evidence

M3 closed every development gate. Rejection separated the seeded signal
classes perfectly, correction retirement removed obsolete advice on the third
independent contradiction, and context provenance remained uncontaminated.
The abstention threshold reduced unseen-repository action accuracy from M2's
1.0000 to 0.9167; this is the measured cost of refusing a weak match and still
leaves H5 well above threshold.

Drift adaptation is abrupt rather than smooth: obsolete support remains high
after the first two corrections and becomes zero only at the third. The
composite intervention prevents causal attribution among verification gating,
guard learning, abstention, and retirement. Perfect separation of output
signals is also a fixture property, not proof against realistic novel failure
language.

## Decision and next focus

Freeze M3 and all thresholds. Do not revise after viewing holdout outcomes.
Run the untouched seeds `101`, `103`, and `107` once, then run fresh unit,
determinism, capture/redaction, contamination, drift, manifest, and runtime
verification. If any mandatory POC gate fails, report a non-success terminal;
otherwise select M3 as the best checkpoint and classify the trace without
claiming H7.
