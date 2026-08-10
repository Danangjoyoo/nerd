# Loop Profiles and Routes: Endpoint Map

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Loop Profiles and Routes router](index.md) and load it only for its named trigger.

## Nerd Endpoint Mapping

Use this as a starting map after Nerd Smart resolves exactly one endpoint. Task
facts and hard floors override defaults.

| Endpoint | Lowest common route/profile | Escalate when |
| --- | --- | --- |
| **Discuss** | `direct/D0` | Evidence gathering or iterative decision testing becomes necessary |
| **Ideate** | `options/L1`: generate -> screen -> recommend | Prototypes, experiments, or several stakeholder constraints must be reconciled |
| **Explore** | `inspect/L1`: question -> evidence -> synthesis | Broad coverage or durable research state raises the profile but remains non-mutating |
| **Diagnose** | `inspect/L1` or `experiment/L2` | Reproduction is iterative, boundaries interact, or the runtime must be observed over time |
| **Review** | `inspect/L1` | Several coupled surfaces, independent reviewers, or integration reasoning is necessary |
| **Specify** | `draft_validate/L1`; raise the profile to L2 for an authorized persisted revision cycle without changing the route | Multiple interfaces or stakeholder gates make the specification adaptive; a durable approval wait raises it to L3 |
| **Document** | `direct/D0` or `draft_validate/L1` | Rendering, examples, cross-document consistency, or review feedback creates back edges |
| **Plan** | `plan_validate/L1` | Dependencies, unknowns, or experiments are required to make the plan actionable |
| **Execute** | `direct/D0`, `piv/L2`, or `tdd/L2` | Persistence/external gates require L3; coupled high-risk work requires L4 |
| **Monitor** | `inspect/L1` for one immediate recheck or `monitor/L3` for durable waiting | Waiting must survive turns, conditions interact, or action/incident recovery is authorized |

Endpoint boundaries always win:

- `Specify` stops before planning or implementation unless the user requested a
  broader Execute outcome.
- `Plan` stops before mutation.
- `Diagnose` stops before repair.
- `Review` reports findings without edits.
- `Monitor` observes without mutation unless the endpoint is explicitly changed
  or Execute already authorizes a larger lifecycle.
