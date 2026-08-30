# Architecture

## Decision

The POC treats behavioral memory as an adaptive, global corpus of verified
episodes with contextual applicability. Repository identity is a context
feature, not a storage namespace or authority boundary. Cross-repository reuse
is allowed only through compatible non-repository context and must abstain when
evidence is weak or conflicting.

This is an experiment architecture, not a migration of the production
`skills/nerd-memory` runtime.

## Trust boundary

The learner accepts sanitized observations and emits advisory predictions. It
does not receive or persist current instructions, endpoint choices,
permissions, credentials, executable tool arguments, or action authority.

```text
trusted current request                       untrusted behavioral memory
-----------------------                       ---------------------------
instructions / authority  ---- outside ----> episode learner
explicit choices          ---- override ----> advisory prediction
verification evidence     ---- qualifies ---> episode eligibility
                                                |
                                                v
                                     action/tools/steps/skills/guard
                                     + source episode provenance
```

An external resolver applies current explicit choices after prediction. This
separation makes it impossible for the learner itself to broaden authority.

## Episode contract

Every persisted episode has:

- `episode_id` and monotonic `sequence`;
- a non-secret repository label and contextual features (`language`,
  `surface`, and `project_kind`);
- normalized, sanitized `command_cues` rather than a raw transcript;
- observed `action`, `tools`, ordered `steps`, and `skills`;
- `output_signals`, `output_valid`, and output severity;
- verification status and verifier name;
- feedback (`accepted`, `corrected`, or `rejected`) and optional replacement;
- measured synthetic cost units; and
- `memory_origin` plus source episode provenance.

Capture does not represent authority-bearing inputs and recursively redacts
common credential forms from persisted string fields before cue extraction.
Canonical JSON round trips are the reconstruction oracle.

## Eligibility and provenance

Successful behavior is positive evidence only when verification passed and
feedback accepted it. A correction contributes its reviewed replacement and
invalidates the contradicted recommendation for the matching context. A
rejected or invalid output is negative guard evidence, not a successful
workflow. Silence without verification contributes nothing.

Every prediction includes `origin=behavioral_memory_advice` and the exact
episode IDs used. Repository and subagent/tool content cannot become current
authority through provenance laundering.

## Learner checkpoints

| Checkpoint | Single causal intervention | Behavior |
| --- | --- | --- |
| M1 | Enable simple counts | Cue-to-action counts; action-level majority tools, skills, and steps. |
| M2 | Replace keying with a contextual hybrid | Global cue transfer plus exact compatible context ranking; repository is excluded from the compatibility key. |
| M3 | Replace evidence admission with a refinement policy | Only verified/reviewed positives, learned invalid-output guards, calibrated abstention, and three-contradiction retirement. |

M3's refinement policy is one composite intervention. Its components are not
independently attributable in this three-iteration experiment; an ablation is
the precise next experiment.

## Baselines

| ID | Description | Oracle status |
| --- | --- | --- |
| B0 | No memory: always abstain and reject nothing. | Non-oracle control |
| B1 | Global majority by action with no command or context discrimination. | Non-oracle |
| B2 | Hard repository partition; no transfer to an unseen repository. | Non-oracle |
| B3 | Fixture-template lookup using the gold context/action mapping. | Oracle ceiling; excluded from improvement thresholds |

## Prediction targets

The learner separately predicts:

1. command cues to action;
2. action plus context to tool set;
3. action plus context to a step DAG represented by mandatory ordering edges;
4. output signals to reject/accept guard advice; and
5. action plus context to skill set.

Set predictions use exact set-F1. Workflow predictions use edge-F1 and count a
mandatory ordering violation when a gold edge is reversed or absent from the
predicted order. Abstention is a first-class result, not the nearest match.

## Determinism

Fixtures use isolated `random.Random(seed)` instances. Sorting breaks all
count ties. Canonical JSON uses sorted keys and compact separators. Verification
v4 projects functional/metric evidence, including the frozen H8 and H9
agent-experiment verdicts, into an exact canonical digest. Real
runtime measurements remain in each verification record but are excluded from
that projection because wall-clock timing is inherently variable. Two-run
runtime evidence must independently satisfy median `<5 ms` and p95 `<10 ms`,
then differ by no more than `max(0.05 ms, 25% of the slower measurement)`.

## Cross-agent Python boundary

Iteration 005 adds a separate SQLite-backed integration POC. It does not alter
the M3 learner or installed Nerd Memory runtime.

- One `behaviors` table stores verified cue phrases, action, tools, steps,
  skills, invalid-output signals, and source provenance.
- One `recall_events` table audits trial, consumer, repository provenance,
  outcome, score, and rejection without storing the raw command.
- The API and schema accept no storage partition selector. Repository labels
  are provenance only and do not filter recall.
- SQLite WAL mode and a busy timeout permit the three consumers to use the same
  local file safely in this bounded experiment.
- The matcher uses normalized token overlap, a fixed threshold, deterministic
  tie-breaking, and abstention on equal top matches.

This establishes a user/host-local global corpus shape. It does not establish
cross-device sharing, multi-user access, automatic hook activation, or a
production migration.

## Paired-agent measurement boundary

Iteration 006 reuses the Python-only SQLite boundary for a matched comparison.
One fresh teacher must first produce an exact verified output before its single
behavior trace is recorded. Five later rounds give identical inputs to one
memory-enabled and one memory-blind fresh agent. The memory arm makes exactly
one audited lookup; the control arm has no store, trace, gold, or recall access.
Spawn order alternates between rounds.

Accuracy is exact canonical JSON equality with leaf-level accuracy as a
secondary measure. End-to-end wall time runs from a common persisted round
start to answer finalization. Because the subagent interface exposes no billed
token telemetry, cost uses a frozen lexical proxy over the public protocol,
card, retrieved advice, and answer. That proxy deliberately excludes hidden
reasoning, system/developer prompts, tool traffic, and actual model tokens.
Consequently iteration 006 can test paired usefulness and observed speed, but
cannot close H7's production token/overhead claim.
