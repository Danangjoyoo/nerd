# Definition of Done: Evidence

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Definition of Done router](index.md) and load it only for its named trigger.

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
