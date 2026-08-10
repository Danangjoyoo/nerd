# Definition of Done: Construction

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Definition of Done router](index.md) and load it only for its named trigger.

## Construction Workflow

1. **Resolve the outcome.** State who needs what observable result and why it matters.
2. **Bound the loop.** Use the Focus Record to capture endpoint, scope, mutation authority, constraints, and non-goals.
3. **Extract requirements.** Segment the goal, spec, examples, contracts, and policies into atomic required states.
4. **Find counterexamples.** Ask what could be wrong even if the obvious happy-path check passes.
5. **Add the quality floor.** Select only applicable compatibility, security, accessibility, reliability, performance, data, and operational constraints.
6. **Select evidence.** Choose the least expensive credible verifier for each criterion; add broader or independent checks where risk justifies them.
7. **Define integration.** State how the loop result will be checked in its parent or real environment.
8. **Define freshness.** Require affected evidence to be regenerated after the last material change.
9. **Freeze identity.** Sort and freeze the complete mandatory criterion and
   integration ID sets, version the DoD, and hash the immutable definitions.
   Require evidence to bind that exact hash/revision, criterion, verifier,
   current artifact revision, and authenticated observed verdict. Criterion
   status is derived from that verdict, never asserted separately. Bind human
   approval to the exact DoD hash, artifact, and owner as a distinct
   authenticated `APPROVED | REJECTED` decision; presence is not acceptance.
10. **Separate stop states.** Define blocked, unsafe, impossible, cancelled,
   failed, budget-exhausted, handoff, and `STOPPED` no-positive-value outcomes
   without calling them done. Plateau is a dynamic diagnosis; it becomes
   `STOPPED/PLATEAU` only when no authorized proportionate cycle remains.
11. **Challenge and baseline.** Test the DoD for ambiguity, proxy gaming, feasibility, and missing authority; then bind its version in the selected Loop state before execution.

When exploration is the task, define completion as sufficient evidence to answer the agreed questions and expose remaining uncertainty. Do not require certainty that the domain cannot provide.
## Criterion Quality

Apply the **STATE** test to every mandatory criterion:

- **Source-traced:** Name the user statement, spec, policy, parent criterion, or justified inference it comes from.
- **Testable:** Define an inspection, demonstration, analysis, measurement, test, or named approval that can falsify it.
- **Atomic:** Express one required state with one unambiguous subject.
- **Target-state:** Describe what must be true, not what work will be attempted.
- **Evidence-bound:** Name the proof artifact, pass rule, and freshness requirement.

Also require each criterion to be:

- Necessary for the outcome or its risk profile.
- Feasible within the authorized environment and cost.
- Implementation-independent unless the implementation itself is contracted.
- Precise about workload, platform, data, version, or operating conditions when they affect the result.
- Decidable with a binary rule, numerical threshold, anchored rubric, or named acceptance owner.

Use this expanded criterion shape when traceability matters:

```text
ID:
Source: mandatory | current user | spec | parent DoD | Focus Record | consumed memory | advisory plan | inferred
Required state:
Conditions and scope:
Pass rule or threshold:
Verification method:
Required evidence:
Freshness rule:
Acceptance authority:
DoD revision/hash binding:
Current artifact revision binding:
Authenticated observed verdict:
Approval decision and owner binding:
Parent criterion:
```
