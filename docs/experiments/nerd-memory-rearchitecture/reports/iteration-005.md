# Iteration 005 — Fresh-Agent Shared-Memory Trial

## Hypothesis

After one teacher agent records at least six verified opaque behavior patterns,
three fresh consumer agents under different repository labels can retrieve the
same Python POC memory without a storage partition selector and improve exact
task-pattern success by at least 50 percentage points over counterbalanced
memory-off trials.

## Artifact and data revision

- Shared store: `shared-behavior-memory/v1`, SQLite standard library only.
- Experiment harness: `shared-agent-experiment/v1`.
- Teacher behaviors: `6`, all verified and sourced from
  `teacher-rust-service`.
- Consumer repositories: `consumer-typescript-web`, `consumer-python-cli`, and
  `consumer-documentation`.
- Randomization seed: `505`.
- Public-card digest:
  `sha256:35fa9e46fb8abf57cd0e73010456931e3094b0fdf9f0b8d13b3abfa145e7a7b7`.
- Hidden-gold digest:
  `sha256:7e943de5d89f5e7c625957a6ef1c857ac8fa5d1f89413b141a324a8aa6616a13`.
- Result digest:
  `sha256:1e317c5e3dc4001bf2be322ea0c26b02ff27b30acb2904af8df2ab18b0c5357d`.

## Control and intervention

- Control: nine known task cards completed without querying or inspecting the
  shared memory.
- Intervention: nine known cards completed after one audited advisory recall
  from the teacher-populated store.
- Abstention control: three unrelated memory-on cards.
- Each of the six behavior families appears in both conditions across workers.
- Public cards include commands and output signals but omit behavior IDs,
  actions, tools, steps, skills, and expected rejection decisions.
- Consumers were spawned with no inherited conversation turns and were
  prohibited from reading teacher, gold, database, source, or peer artifacts.

## Evidence and metrics

| Measure | Result | Gate |
| --- | ---: | ---: |
| Teacher behaviors | 6 verified | `>=6` |
| Consumer submissions | 3 | `=3` |
| Memory-on exact task success | 9/9, `100%` | — |
| Memory-off exact task success | 0/9, `0%` | — |
| Exact success gain | `+100 pp` | `>=+50 pp` |
| Shared behavior availability | 9/9, `100%` | `>=90%` |
| Cross-repository recall | 9/9, `100%`; all 3 workers | `>=90%`; all workers |
| Unknown-pattern abstention | 3/3, `100%` | `>=90%` |
| Memory-on queries | 12/12 exactly once | exact |
| Memory-off queries | 0/9 | `0` |
| Storage partition field | absent from tables and columns | absent |

The known memory-on trials included three invalid-output signals. As a
secondary diagnostic, all three were rejected and none of the six valid
memory-on outputs was falsely rejected. These rates were not added as a new
post-result mandatory gate.

All predeclared E1–E8 gates passed.

## Result and disconfirming evidence

H8 is supported for this bounded Python POC. The same teacher records were
available to three separate consumers across three different repository
labels, and exact learned procedures materially outperformed memory-off
attempts. The audit confirms the control condition did not query the store.

The result does not prove automatic memory activation: cards explicitly stated
whether the experimental recall interface was available. It also does not
prove the installed Nerd Memory runtime shares this architecture, because that
runtime was not changed or called. All agents shared one host filesystem, the
sample is small, only one randomization seed was used, and exact-match scoring
rewards retrieval of procedural wording that a reasonable control might express
differently. Semantic task wording also gives controls partial domain clues,
although it does not disclose the exact recorded procedures.

No token, model-call, or end-to-end latency comparison was collected, so H7
remains `UNTESTED`.

## Decision and next focus

Accept the global, repository-as-provenance storage direction for the Python
POC. Do not claim production convergence. The next discriminating experiment
must place this store behind the actual session hook, remove the explicit
`memory_enabled` card flag, and compare automatic shadow recall against a
memory-blind control over multiple seeds and natural session tasks.
