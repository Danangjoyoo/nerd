# Test Plan

## Purpose and Boundary

Explain what will be tested, why that coverage matters, which environments and
data it needs, and what evidence is required for a release decision. A test plan
describes verification strategy; detailed repeatable procedures belong in test
cases. Writing either artifact does not execute tests or establish a pass.

## Inputs to Preserve

- Requirements and acceptance criteria, with stable IDs when supplied.
- Known risks, affected surfaces, integration boundaries, and exclusions.
- Available environments, builds, fixtures, tools, owners, and constraints.
- Established entry/exit criteria and release approval responsibilities.

## Suggested Structure

1. **Summary:** What decision the testing supports and the highest-priority risks.
2. **Scope:** Included behavior and explicit exclusions.
3. **Coverage matrix:** Requirement, risk, test level, scenario, and evidence.
4. **Setup:** Environment, build, test data, access, and prerequisites.
5. **Execution approach:** Dependency order, ownership, and result recording.
6. **Entry/exit criteria:** Readiness and completion conditions, if established.
7. **Risks and gaps:** Missing prerequisites and their release consequence.

Do not add every testing category automatically. Include security, performance,
accessibility, migration, compatibility, or recovery coverage when the confirmed
scope and risk require it.

## Filled Example

Fictional testing scope:

```markdown
# Account Export — Test Plan

Status: Planned; no test execution claimed

Testing supports the first CSV export release. The highest-priority risks are
cross-account access and downloads remaining available after link expiry.

## Scope

- Cover request authorization, job states, CSV output, and download expiry.
- Exclude scheduled exports and PDF output, which are outside release scope.

## Coverage

| Requirement | Risk | Test approach | Expected evidence |
| --- | --- | --- | --- |
| R1 | Job belongs to the wrong account | API integration and worker output check | Job identity, account association, sample CSV |
| R2 | Viewer or other account accesses data | API and download authorization cases | Denied responses with no job/file exposure |
| R3 | Link remains usable at expiry | Controlled-clock boundary cases | Before/at/after expiry results |

## Setup

- Isolated test environment with export API, worker, and file storage.
- Account A: administrator and viewer; account B: administrator.
- Deterministic account-scoped fixture records.
- A controlled clock for expiry checks.
- Build identifier: Unknown; record it before execution.

## Execution Order

1. Validate fixture isolation and environment readiness.
2. Run request and download authorization cases.
3. Run generation and output-content cases.
4. Run expiry boundary cases.
5. Record results, evidence, defects, and unresolved coverage gaps.

## Exit Criteria

- Required scenarios have recorded results for the tested build.
- Authorization and expiry blockers have passed verification.
- Any accepted coverage exception is documented by the release decision owner.

## Gaps

| Gap | Consequence |
| --- | --- |
| Performance target not supplied | No performance acceptance claim is possible |
| Retention policy unresolved | File-deletion coverage cannot be finalized |
```

Use actual accepted exit criteria in a real plan. Do not silently promote these
example criteria into project policy or claim risk acceptance on someone's behalf.

## Writing Corrections

| Weak wording | Better wording |
| --- | --- |
| Test all edge cases | Name relevant empty, boundary, permission, and failure scenarios |
| Ensure the feature works | Map each behavior to a scenario and observable evidence |
| QA passed | Identify build, environment, execution record, and remaining gaps |
| Release when quality is good | State the established measurable exit conditions |

## Completion Check

Check requirement coverage, risk priority, reproducible setup, meaningful test
levels, evidence recording, and readiness/exit criteria. Keep expected evidence
distinct from actual results. Make untested behavior visible rather than
summarizing it as a pass.
