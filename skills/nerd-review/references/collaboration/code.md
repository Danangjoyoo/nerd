# Code Review Collaboration

Use for source, configuration, infrastructure, or implementation contracts.
Keep stack/framework references as specialized checks within the broader review
orchestration; code review does not define every other review context.

## Companion Sequence

| Step | Skill / lens | Bounded task | Return to Review |
| --- | --- | --- | --- |
| Resolve a contract gap | `nerd-explore`, when needed | Follow the exact caller, schema, configuration, or neighboring implementation | Sourced invariant and reachable inputs |
| Inspect behavior | Review + stack/framework references | Trace the scope or delta through affected paths | Candidate defect, trigger, and consequence |
| Verify regression evidence | Review + test guide when needed | Check that existing tests observe the changed contract | Supported protection or credible escaping failure |
| Challenge the finding | Review | Seek guards, caller restrictions, intentional behavior, and counterexamples | Keep, narrow, downgrade, or discard |

Map the stack from local evidence and read the smallest matching reference set.
Use Explore for one factual gap rather than a repository-wide inventory. Add
nerd-document's criteria when the concern is a user-facing contract or misleading
documentation. Use nerd-patrol only under the entrypoint's evidence-led security
gate, and the hotfix guide when incident causality is part of the request.

## Review Lenses

- **Level 1:** Invalid constructs, runtime errors, unsafe state, broken inputs.
- **Level 2:** Local contracts, configuration, test behavior, compatibility.
- **Level 3:** Dependency, ownership, concurrency, and control-flow consequences.

For pull request review, establish the baseline and isolate introduced or
materially worsened behavior. For plain review, existing defects qualify.
Generated files and callers may provide proof, but their presence does not
expand the review into unrelated changes.

## Proof and Completion

Show that the triggering state is reachable and the issue is not handled at
another boundary. A missing abstraction or stylistic inconsistency alone is not
a finding. Prefer existing narrow checks after inspecting their side effects;
do not format, generate, autofix, or repair. Return consolidated findings with
exact locations, rather than a walkthrough of everything inspected.
