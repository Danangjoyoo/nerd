# Loop Profiles and Routes: Examples

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Loop Profiles and Routes router](index.md) and load it only for its named trigger.

## Routing Examples

| Task | Endpoint | Route/profile | Why |
| --- | --- | --- | --- |
| Correct one typo and run its exact check | Execute | `direct/D0` | No useful back edge |
| Find bugs in one module | Review | `inspect/L1` | Bounded probes and validated findings |
| Establish why a named crash occurs | Diagnose | `inspect/L1`, then `experiment/L2` if needed | Cause sought; no repair authority |
| Fix a null crash with a regression test | Execute | `tdd/L2` | Local mutation and deterministic correction cycle |
| Implement a stable OpenAPI endpoint | Execute | `spec_delivery/L2` | Fixed criteria and local integration proof |
| Specify, plan, and implement one feature | Execute | `spec_delivery/L2` or L3 if components/handoffs emerge | Root endpoint includes the whole lifecycle |
| Code, push a PR, triage CI, and wait for review | Execute | `pr_delivery/L3` | External effects, durable waits, human feedback |
| Perform the same bounded dependency-update task daily | Execute | `routine/L2`, L3 when PR/CI applies | Reusable route; fresh episode and proof |
| Observe a deployment until healthy | Monitor | `monitor/L3` | Durable event-driven wait; no busy polling |
| Zero-downtime migration across services and databases | Execute | `adaptive_program/L4` | Coupled contracts, rollback, staged operational evidence |
## Profile-Router Definition of Done

The router is correct only when:

- exactly one user endpoint controls deliverable, authority, and stop;
- D0 bypasses loop artifacts when iteration adds no value;
- every actual loop has an observable DoD and one current focus;
- the selected profile is the minimum satisfying every observed hard floor;
- all reducer commands share one hash-bound admission and cumulative budget,
  so no later phase can downgrade the route/state or reset the active limit;
- route templates contain only useful stages and cause-labelled back edges;
- every route named by the endpoint mapping has one defined template and one
  unambiguous base profile;
- state persistence is proportionate and authorized;
- waiting consumes no active iteration budget;
- lower profiles compress representation rather than weaken rigor;
- higher profiles add a required capability rather than ceremonial artifacts;
- escalation and de-escalation preserve contracts and verified evidence;
- each child uses its own cheapest adequate profile;
- memory, specialties, and speed modifiers retain their authority boundaries;
- endpoint, cost, risk, persistence, external-effect, and hard-budget changes
  receive required user confirmation; and
- the task stops immediately at verified DoD completion or an honest typed
  non-success state.
