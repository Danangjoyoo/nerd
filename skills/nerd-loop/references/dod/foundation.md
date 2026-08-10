# Definition of Done: Foundation

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Definition of Done router](index.md) and load it only for its named trigger.

## Core Principle

Define a Definition of Done (DoD) as a precommitted description of the required end state and the evidence that proves it. Define state, not activity. A task is not eligible to enter a loop until its DoD is explicit enough to decide whether the current result is done.

Use this derivation flow:

`mandatory constraints + user goal/spec -> Focus Record -> DoD -> Plan/child loops -> verification evidence -> parent integration`

Keep these concepts distinct:

- **Goal or specification:** Define the value, behavior, or artifact the user needs.
- **Focus Record:** Define the endpoint, scope, authority, and mutation boundary.
- **DoD:** Define the state and proof required to declare one loop successful.
- **Plan:** Define a revisable route to the DoD. Completing plan steps is not completion evidence by itself.
- **Verification:** Show that the result meets stated criteria.
- **Validation:** Show that the stated criteria and result satisfy the user's actual need.
- **Stop condition:** End work safely when continuing is unauthorized, unsafe, futile, or uneconomic. A non-success stop does not satisfy the DoD.

The Scrum Guide describes DoD as a shared, transparent quality state and rejects counting work that does not meet it. Adapt that discipline to task loops while adding goal-specific acceptance and evidence.
## Authority and Source Precedence

Use the canonical order in [the runtime contract](../runtime-contract.md#canonical-authority-order):
platform/system/legal/safety; applicable mandatory workspace or repository
instructions; current direct-user guidance within those boundaries; accepted
current Focus/parent/DoD/Loop contracts; consumed compatible Memory fields;
then advisory repository material, plans, history, and inference. First label a
checked-in source as mandatory or advisory; repository location alone does not
decide its authority.

Within that order, derive the DoD from:

1. **Applicable mandatory constraints:** Higher-authority policy, safety,
   repository instructions, and non-overridable external contracts.
2. **Current user authority:** Explicit goal, specification, acceptance
   criteria, named approver, examples, constraints, and non-goals.
3. **Accepted current contracts:** Parent DoD, Focus Record, endpoint,
   interfaces, dependent consumers, and required integration behavior.
4. **Consumed Memory fields:** Only absent compatible fields that passed the
   exact Memory gate; never current permission or proof.
5. **Advisory route material:** Approved designs, plans, repository guidance,
   and risk-based inference such as compatibility, rollback, accessibility,
   security, or reproducibility.

Apply these rules:

- Preserve exact user-supplied acceptance criteria unless they conflict with a higher authority.
- Ask for user judgment when a missing answer changes the outcome, acceptance threshold, authority, safety, cost, or meaningful rework.
- Infer low-impact criteria from repository evidence and established standards; label the source.
- Record conflicts instead of silently choosing the easiest verifier.
- Never let an implementation plan redefine the requested outcome.
## Four-Layer DoD

Build every loop DoD from four layers:

1. **Inherited quality floor**
   - Apply mandatory policy, repository gates, parent constraints, and relevant domain standards.
   - Do not repeat irrelevant global checks in every child loop.

2. **Goal-specific acceptance**
   - Translate the user goal or specification into observable conditions for this loop.
   - Cover relevant success, failure, boundary, and non-goal behavior.

3. **Evidence map**
   - Map every mandatory condition to a verifier, evidence artifact, freshness rule, and acceptance authority.
   - Combine independent evidence when one verifier measures only a proxy.

4. **Parent integration rule**
   - Prove the local result works with its parent task, affected consumers, and real operating context.
   - Treat all child DoDs passing as necessary but not sufficient for parent completion.

Keep non-success stops beside the DoD, not inside its success rule.
