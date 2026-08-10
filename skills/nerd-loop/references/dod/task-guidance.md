# Definition of Done: Task Guidance

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Definition of Done router](index.md) and load it only for its named trigger.

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
