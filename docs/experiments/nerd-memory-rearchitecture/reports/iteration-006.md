# Iteration 006 — Five Paired Task Replications

## Hypothesis

After one fresh teacher completes and records a verified task procedure, five
fresh memory-enabled agents executing new instances of that task pattern will
achieve mean exact-output accuracy `>=0.80` and improve by at least `0.40` over
five matched memory-blind agents given the same inputs.

## Artifact and data revision

- Harness: `paired-agent-experiment/v1`, Python standard library only.
- Fixture seed: `606`; paired rounds: `5`; consumer agents: `10`.
- Experiment manifest digest:
  `sha256:7419a85732e355abd77b209cc494fd3bb81bfa55f65de2464481c5ac193d0cbd`.
- Private procedure digest:
  `sha256:4b5489071b480c5656271e948eb8c9a987005480fe4de0951cb7e6039dc80d7c`.
- Teacher verdict digest:
  `sha256:5a15d58bb1279ee0a58dc9880f588c07f4d7422a3dd883eb4c8022bc68353adc`.
- Result digest:
  `sha256:03fdc50d5eba5dd7b1b057517bfbb9d137e1b62d930bdf2892e04bc0f074de62`.

## Pre-consumer correction

The teacher's first exact-verification attempt exposed an underdetermined
procedure contract: transformation rules were specified, but output field
names and nesting were not. Before any consumer was spawned, the procedure was
amended to declare the output shape and fingerprint serialization contract.
The same teacher then passed exact verification. No thresholds, round inputs,
gold outputs, or scoring rules changed, and no consumer observation existed at
the time of correction.

## Control and intervention

- Teacher: one fresh agent processed a private training fixture; exact output
  and its behavior trace were verified before one record entered the store.
- Intervention: five fresh agents each made exactly one audited recall and
  followed the returned procedure.
- Control: five fresh agents were prohibited from any memory or teacher access.
- Matching: both arms in each round received the same input digest.
- Dispatch order: memory first in rounds 1, 3, and 5; control first in rounds 2
  and 4.
- No intermediate accuracy result was calculated or shown before all ten
  consumer submissions finalized.

## Accuracy

| Measure | Memory | Control | Paired gain |
| --- | ---: | ---: | ---: |
| Exact-output mean | `100%` | `0%` | `+100 pp` |
| Exact-output median | `100%` | `0%` | — |
| Leaf-level mean | `100%` | `2.48%` | `+97.52 pp` |
| Leaf-level median | `100%` | `1.32%` | — |

Memory passed exact output in all five rounds. No control reproduced the exact
user-specific procedure. H9's accuracy and paired-advantage thresholds passed.

## Speed

Wall time is measured from the common persisted round start until each answer
was finalized.

| Measure | Memory | Control | Memory − control |
| --- | ---: | ---: | ---: |
| Mean | `63.73 s` | `80.39 s` | `-16.66 s` |
| Median | `61.37 s` | `82.94 s` | `-17.83 s` |
| Population stddev | `4.54 s` | `13.59 s` | `15.17 s` paired |

Memory was `20.72%` faster on the mean and faster in four of five rounds. In
round 2 it was `1.95 s` slower, so speed improvement was not universal.

## Observable token proxy

The subagent interface does not expose billed model tokens. The preregistered
proxy counts lexical tokens in the stored arm protocol, public card, retrieved
advice, and submitted answer.

| Measure | Memory | Control | Memory − control |
| --- | ---: | ---: | ---: |
| Mean | `878.2` | `745.6` | `+132.6` |
| Median | `878` | `768` | `+110` |
| Population stddev | `0.4` | `113.78` | `113.99` paired |

Memory used `17.78%` more observable proxy tokens on the mean and used fewer
proxy tokens in only one of five rounds. These numbers exclude system and
developer prompts, hidden reasoning, tool traffic, and actual billed tokens.

## Result and disconfirming evidence

All F1–F7 gates passed; H9 is supported for this bounded task pattern. Memory
produced a large accuracy gain and lower average wall time, while increasing
the observable token proxy.

The control prompt intentionally lacks the user-specific meaning of the opaque
task marker, so this is a test of remembered private procedure—not general
reasoning superiority. Exact matching penalizes semantically reasonable but
contract-incompatible control answers. The experiment uses one procedure, one
fixture generator, one seed, one host, and agents that know their assigned
arm. Shared-start timing includes sequential dispatch skew despite alternating
order. Actual model tokens remain unavailable, so H7 stays `UNTESTED`.

## Decision and next focus

Accept H9 and the hypothesis that behavioral memory can trade a modest context
increase for substantially higher exactness and lower task-completion time on
opaque recurring work. Next, repeat this paired protocol over several natural
task families with automatic memory activation, arm-blind task prompts, more
seeds, and host-provided model usage telemetry.
