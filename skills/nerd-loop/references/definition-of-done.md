# Defining a Good Definition of Done

Use [the Nerd Loop Runtime Contract](runtime-contract.md) as the normative
source for authority precedence, criterion states, transition priority, and
terminal outcomes. This reference supplies construction and evidence
techniques; it does not redefine runtime state.

## Contents

- [Core principle](#core-principle)
- [Authority and source precedence](#authority-and-source-precedence)
- [Four-layer DoD](#four-layer-dod)
- [Construction workflow](#construction-workflow)
- [Criterion quality](#criterion-quality)
- [Evidence technique palette](#evidence-technique-palette)
- [Task-specific patterns](#task-specific-patterns)
- [Anti-patterns](#anti-patterns)
- [DoD template](#dod-template)
- [Final challenge](#final-challenge)
- [Research basis](#research-basis)

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

Use the canonical order in [the runtime contract](runtime-contract.md#canonical-authority-order):
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

## Evidence Technique Palette

Select techniques from the task, spec, risk, and available action space. Do not turn the full palette into a universal checklist.

| Technique | Select when | Contribution to the DoD | Do not mistake it for |
| --- | --- | --- | --- |
| User or stakeholder acceptance | Intent, taste, policy, usability, or business judgment is decisive | Name the approver, rubric, review artifact, and accept/reject record | Permission to waive mandatory safety or quality gates |
| Focus Record | Outcome or scope can drift | Bind the DoD to intention, endpoint, authority, and mutation boundary | Evidence that the result works |
| Acceptance criteria | A goal or specification contains item-specific behavior | Translate each criterion into an observable pass rule | A shared quality floor by itself |
| BDD / specification by example | Behavior crosses product and technical language | Discover rules and examples; express visible context-event-result scenarios; automate stable examples | Merely writing Gherkin syntax |
| TDD | Implementing or repairing testable code behavior | Establish red-green-refactor evidence and preserve regressions | Proof of user value, integration, or complete coverage |
| Plan and proof map | Work is multi-step or dependent | Map each ordered task to the DoD criterion and proof it advances | Completion because every checkbox was executed |
| Requirements traceability | Many requirements, regulated work, or multiple parents/consumers | Map source -> criterion -> implementation/artifact -> verifier -> evidence -> status | Extra documentation without coverage decisions |
| Static analysis, types, lint, or build | Structural validity and fast feedback matter | Prove compilation, schema, formatting, or rule conformance | Runtime or user-visible correctness |
| Contract testing | APIs, messages, schemas, or service boundaries can drift | Prove consumer and provider agree on used interactions and compatibility | Full functional or end-to-end behavior |
| Property-based / invariant testing | Input spaces are large or transformations have laws | Generate broad and edge inputs; require invariants and preserve counterexamples | Complete domain coverage or a substitute for key examples |
| Integration testing | Components, storage, files, networks, or generated clients interact | Prove real boundary behavior with representative dependencies | A substitute for focused diagnostics |
| End-to-end / journey testing | The user outcome spans the whole system | Prove a few critical realistic paths through the integrated result | A large, slow duplicate of every lower-level test |
| Negative, boundary, fuzz, or adversarial testing | Untrusted input, failure behavior, or robustness matters | Demonstrate rejection, recovery, and safe behavior beyond the happy path | An undefined request to "test more" |
| Metamorphic, round-trip, or differential testing | No simple exact oracle exists | Compare preserved relations, inverse operations, implementations, or trusted references | Proof when all compared systems share the same defect |
| Mutation testing | Passing tests may be weak or overfit | Change critical logic and require tests to detect meaningful mutants | A universal mutation-score target detached from risk |
| Formal specification / model checking | Concurrency, distribution, state machines, or catastrophic rare interleavings matter | State safety/liveness properties and check bounded models or proofs; record assumptions | Proof beyond the declared model and bounds |
| Golden, approval, or visual regression | Output is structured, rendered, or reference-driven | Compare against a reviewed baseline in a controlled environment | Automatic proof of taste, usability, or intentional baseline changes |
| Performance benchmark / SLI / SLO | Latency, throughput, capacity, cost, or reliability matters | Name indicator, threshold, percentile, window, workload, data, and environment | "Seems fast" or a measurement from an incomparable setup |
| Security verification | Auth, secrets, sensitive data, untrusted input, or public exposure is affected | Select threat-driven checks and applicable OWASP/NIST requirement IDs; resolve or accept findings explicitly | A generic scanner pass as complete security proof |
| Accessibility conformance | UI, documents, or user workflows are affected | Pin WCAG version/level and combine automated, manual, and assistive-technology checks as relevant | Automated scanning alone |
| Data reconciliation / migration proof | Data shape, movement, or persistence changes | Check counts, checksums, invariants, sampling, idempotency, dry runs, and rollback/restore | A successful command exit with unverified data |
| Operational readiness | A result will be deployed, operated, monitored, or recovered | Require ownership, telemetry, dashboards, alerts, runbooks, rollout, rollback, backup/restore, and escalation as applicable | Successful local behavior only |
| Independent or held-out verification | The loop can overfit visible checks or creator bias is material | Reserve unseen cases or an independent reviewer for the final gate; record scope and result | Repeatedly exposing the final gate to the optimizing loop |
| Reproducibility and provenance | Builds, research, analysis, or generated artifacts must be repeatable | Record inputs, versions, environment, commands, sources, and deterministic or tolerance rules | A one-off artifact with no reconstruction path |

Prefer a portfolio with fast local checks for iteration and broader, more independent checks near completion. Verify the verifier when failure cost is high.

## Task-Specific Patterns

Use these as selectors, not fixed recipes:

| Task type | Typical DoD evidence |
| --- | --- |
| New behavior | User/spec acceptance criteria, BDD examples, focused TDD, affected integration checks, and parent journey proof |
| Bug repair | Reproduced symptom, regression test failing for the expected reason before repair, passing after repair, and affected-suite proof |
| Refactor | Preserved observable behavior, contract and regression checks, plus any explicit structure or performance objective |
| API or integration | Schema/spec conformance, consumer/provider contracts, auth and error cases, serialization boundaries, and a representative live or stubbed integration |
| UI or design | Interaction scenarios, keyboard/accessibility checks, responsive states, controlled visual comparison, and named human approval for taste or usability |
| Data or migration | Schema and invariant checks, reconciliation, representative sampling, compatibility, idempotency, dry run, and rollback/restore proof |
| Performance or reliability | Baseline and changed measurements under a declared workload/environment, SLI/SLO threshold, regression allowance, and operational signals |
| Security-sensitive change | Threat-driven acceptance, pinned security-standard requirements, static/dynamic checks, abuse cases, and explicit risk acceptance for residual findings |
| Document or static artifact | Required content, factual/source checks, link or schema validation, render inspection, audience suitability, and delivery-path verification |
| Research or exploration | Agreed questions answered, authoritative and diverse sources, methods recorded, contradictions and uncertainty exposed, and user acceptance of sufficiency |
| Plan or specification | Every goal and constraint covered, requirements observable, dependencies and proof mapped, material unknowns explicit, and stakeholder review completed |
| Agent or model behavior | Representative eval set, held-out final cases, qualitative and quantitative rubric, failure analysis, cost/latency limits, and independent or human review |
| External communication or operation | Exact recipient/target, content or action preview, authorization, delivery receipt or state confirmation, and safe failure handling |

## Anti-Patterns

| Weak DoD | Why it fails | Stronger replacement |
| --- | --- | --- |
| "All tests pass" | Tests may be incomplete, stale, or optimized as a proxy | Name the scoped tests, required behaviors, integration evidence, freshness, and complementary validation |
| "Finish the plan" | Measures route completion, not outcome | Map plan tasks to observable DoD criteria and final integration proof |
| "Make it better" | Has no target or direction | Define user-visible dimensions, anchored rubric, threshold, and approver |
| "Try five times" | Attempt count is a budget, not success | Define the target state; treat attempt limit as a non-success stop |
| "No errors" | May hide ignored, skipped, flaky, or unobserved failure | Define expected signals, zero-tolerance classes, allowed exceptions, and evidence source |
| "Coverage is 90%" | Execution coverage does not show assertion strength or intent | Pair relevant coverage with behavior checks, mutation testing, or independent cases |
| "Looks correct to the agent" | Self-review is vulnerable to confirmation bias | Use deterministic checks, a rubric, independent review, or named human acceptance |
| "Matches the snapshot" | The baseline may be wrong or unintentionally updated | Require baseline provenance, controlled environment, reviewed diffs, and behavior/accessibility checks |
| "Child loops are green" | Local successes may not compose | Require a parent integration criterion after child completion |
| "Budget exhausted, therefore done" | Conflates a stop with success | Report budget-exhausted with unmet criteria and remaining gap |
| "Relax the threshold until it passes" | Moves the target to manufacture convergence | Version the proposed DoD change and obtain the required authority before resuming |
| "Passed before the last edit" | Evidence no longer represents current state | Rerun every affected mandatory gate after the final material change |

## DoD Template

Adapt this template to the task. Omit irrelevant optional fields; never omit the outcome, mandatory criteria, evidence, integration, completion rule, or non-success stops.

```markdown
## Definition of Done — [Loop ID and name]

- **Version:** [Number or timestamp]
- **Authority:** [User/spec/policy/parent sources and named approver]
- **Outcome:** [Observable value or state]
- **Scope:** [Included surface]
- **Non-goals:** [Explicit exclusions]
- **Inherited quality floor:** [Applicable mandatory standards]

### Criteria and Evidence

| ID | Source | Required state | Conditions / threshold | Verification and evidence | Status |
| --- | --- | --- | --- | --- | --- |
| DOD-1 | [Source] | [Atomic target state] | [Scope and pass rule] | [Method, artifact, freshness, authority] | pending |

### Integration

- [Required parent, consumer, or real-environment proof]

### Completion Rule

- Declare **done** only when the submitted ID sets exactly match the accepted
  DoD hash, every mandatory criterion and integration check has an
  authenticated `PASS` verdict bound to that exact hash and the current
  artifact revision, each displayed status equals its verdict, and every
  required approval is authenticated, bound to the exact hash/artifact/named
  owner, and explicitly `APPROVED`.

### Non-success Stops

- **Blocked:** [Missing authority, dependency, access, or information]
- **Unsafe / out of scope:** [Boundary requiring escalation]
- **Impossible:** [Evidence that the target cannot be reached in the action space]
- **Failed:** [Unrecoverable execution or verification failure]
- **Budget exhausted:** [Time, token, attempt, or money ceiling]
- **Stopped:** [No positive-value, plateau, inconclusive-trace, or no-ready-work reason]
- **Cancelled:** [Authorized cancellation source]
- **Handoff:** [Named recipient and accepted continuation packet]
```

## Final Challenge

Before baselining the DoD, answer:

- Does passing this DoD prove the user's intended outcome, or only an easy proxy?
- Can the loop game, memorize, disable, skip, or repeatedly expose the verifier?
- Is every criterion source-traced and necessary?
- Are relevant failure, boundary, integration, and recovery states covered?
- Is subjective judgment anchored to a rubric and named acceptance owner?
- Is the evidence feasible, repeatable, fresh, and proportionate to risk and cost?
- Are the action space and verifier capable of moving the task toward the target?
- Could all child loops pass while the parent still fails?
- Are mandatory standards and residual risks explicit?
- Are non-success stops reported without weakening the DoD?

If a material answer is unknown, keep the DoD in draft and resolve the uncertainty before starting irreversible or expensive work.

## Research Basis

- [The Scrum Guide](https://scrumguides.org/scrum-guide.html): shared quality state, transparency, and the rule that unmet work is not done.
- [NASA Systems Engineering Handbook appendices](https://www.nasa.gov/reference/system-engineering-handbook-appendix/): requirement quality, source traceability, verification matrices, validation planning, and stakeholder evidence.
- [Cucumber BDD guidance](https://cucumber.io/docs/bdd/): discovery, formulation, executable examples, and collaborative validation of behavior.
- [Martin Fowler on TDD](https://martinfowler.com/bliki/TestDrivenDevelopment.html): test-list preparation and red-green-refactor as an inner development loop.
- [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/): property-based and invariant testing across generated edge cases.
- [Pact documentation](https://docs.pact.io/): consumer-driven contracts and executable integration expectations.
- [Stryker mutation-testing guidance](https://stryker-mutator.io/docs/): evaluating whether tests detect meaningful defects rather than merely execute code.
- [TLA+ overview](https://lamport.azurewebsites.net/tla/tla.html): formal modeling and checking for concurrent and distributed system properties.
- [Google SRE on SLOs](https://sre.google/sre-book/service-level-objectives/): user-centered indicators, explicit thresholds and measurement conditions, and control-loop economics.
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/): referenceable application-security verification requirements.
- [NIST Secure Software Development Framework](https://csrc.nist.gov/projects/ssdf): outcome- and risk-based secure-development practices rather than an unfiltered checklist.
- [W3C WCAG overview](https://www.w3.org/WAI/standards-guidelines/wcag/): stable accessibility standards and testable conformance criteria.
- [NIST AI RMF Measure guidance](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/): documented, repeatable evaluation; representative conditions; independent assessors; and user feedback.
- [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots): controlled snapshot evidence and environment sensitivity.
- [OpenTelemetry overview](https://opentelemetry.io/docs/what-is-opentelemetry/): traces, metrics, and logs as operational evidence of system state.

Treat these sources as a technique library. Select only the requirements and evidence justified by the current task, its authorities, and its risks.
