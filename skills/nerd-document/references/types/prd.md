# Product Requirements Document (PRD)

## Purpose and Boundary

Help product, design, engineering, and QA agree on the user problem, intended
outcome, release scope, and evidence of success. Document supplied product
decisions. Do not invent priorities, research, metrics, or commitments to fill
the template; use explicit unknowns and their consequences.

Use the TRD for technical design and the test plan for execution coverage.
Link those documents instead of repeating their bodies here.

## Inputs to Preserve

- Intended users and the task or problem they face.
- Evidence for the problem and any established baseline.
- Accepted goals, scope, exclusions, and constraints.
- Requirements, acceptance criteria, and known unresolved questions.

## Suggested Structure

| Section | What belongs here | Useful format |
| --- | --- | --- |
| Summary | Problem, target user, proposed outcome, decision needed | Short paragraph |
| Problem and evidence | Current workflow, pain, established research | Bullets with source links |
| Goals and success | Outcomes, measurement method, confirmed targets | Metric table |
| Scope | Included capabilities and explicit exclusions | Bullets or comparison table |
| User flow | Main path and important exceptions | Numbered points |
| Requirements | Stable IDs, priority if known, observable behavior | Table |
| Acceptance | Conditions that demonstrate each requirement | Numbered criteria or scenario table |
| Risks and questions | Unresolved decisions and why they matter | Table with owner when known |

Add rollout or dependencies when established. Avoid speculative roadmaps.

## Filled Example

Fictional product facts, illustrating the writing style:

```markdown
# Account CSV Export — PRD

Status: Draft | Audience: Product, engineering, QA

Administrators need an account report for monthly reconciliation. The first
release lets them request a one-time CSV export and download it through a link
that expires after 24 hours.

## Release Scope

- Included: administrator access, one-time CSV generation, download expiry.
- Excluded: scheduled exports, PDF output, viewer access.

## Requirements and Acceptance

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| R1 | An administrator can request an export for their account | Accepted job is associated with that account |
| R2 | Viewers and other accounts cannot access the export | Denied request returns no job or file data |
| R3 | The download link expires after 24 hours | A request at or after expiry returns no file content |

## Main Flow

1. The administrator requests an export from the account's Exports page.
2. The service reports the job state.
3. Once the job is ready, the administrator downloads its CSV.

## Success Measurement

| Outcome | Measure | Target |
| --- | --- | --- |
| Reconciliation can use the export | Successful downloads and reconciliation feedback | Unknown; no target supplied |

## Open Questions

| Question | Why it matters |
| --- | --- |
| When are generated files deleted? | Determines retention behavior and user guidance |
| What dataset size must the first release support? | Defines the performance acceptance boundary |
```

In a real PRD, attach source evidence for the problem and accepted requirements.
The example's missing measurement target must remain a gap rather than become
an invented percentage.

## Writing Corrections

- Weak: “The export should be fast and secure.”
  Better: state established performance targets and authorization behavior
  separately; mark a missing target as unknown.
- Weak: “Use a queue because the implementation will need one.”
  Better: describe the required user behavior; link the accepted queue design
  in the TRD if it is already decided.
- Weak: “Improve the user experience.”
  Better: name the user task and the observable improvement supported by evidence.

## Completion Check

Confirm each requirement has a stable ID, clear behavior, scope, and acceptance
criterion; success metrics are sourced or explicitly unresolved; exceptions do
not contradict the main flow; and open questions identify their practical impact.
Do not label a draft approved without evidence of approval.
