# Test Cases and Execution Records

## Purpose and Boundary

Give a tester enough information to reproduce a scenario and compare the result
with an explicit expectation. Keep the reusable case definition separate from
each execution record. Use the test-plan guide for overall strategy and release
criteria. Documentation alone never establishes that a case was run.

## Case Fields

| Field | What to record |
| --- | --- |
| Case ID and title | Stable ID and observable behavior |
| Requirement / risk | Trace to the accepted behavior being checked |
| Preconditions | Starting state, access, environment, and fixtures |
| Input | Exact relevant values or reproducible fixture references |
| Steps | Numbered actions in executable order |
| Expected result | Observable response, state, output, and relevant side effects |
| Cleanup | Restoration needed to keep later cases independent |

For execution, add a run ID, case ID, build, environment, actual result, status,
evidence, and defect link when one exists. Use `Not run`, `Passed`, `Failed`, or
`Blocked` consistently. A missing observation cannot establish a pass.

## Filled Example: Authorization Case

Fictional case definition:

```markdown
# TC-02 — A Viewer Cannot Request an Export

Requirement: R2 — only account administrators can request exports
Status: Not run

## Preconditions and Inputs

- Account A exists with a viewer user V.
- V is authenticated and has no administrator role.
- The test can inspect export jobs created for the unique test request.

## Steps

1. As V, request an export for account A.
2. Inspect the response for an access-denied result.
3. Inspect job records associated with the test request.

## Expected Result

- The request is denied according to the established API error contract.
- The response contains no download link or file content.
- No export job is created for the denied request.

## Cleanup

Remove the isolated fixture account after the test suite finishes.
```

Use the exact status code and error shape when established. If the API error
contract is unknown, record that limitation; do not guess `401` or `403`.

## Filled Example: Expiry Boundary Matrix

Assume the confirmed contract requires `now < expiresAt`:

| Case ID | Clock input | Expected download behavior |
| --- | --- | --- |
| TC-03a | Just before expiry, at supported clock precision | Authorized caller receives file content |
| TC-03b | Exactly at expiry | No file content returned |
| TC-03c | Just after expiry, at supported clock precision | No file content returned |

State the actual clock precision and fixture strategy before execution. Test
expected content or denial, not only that the client did not crash.

## Example Execution Register

Fictional records, not evidence of real testing:

| Run ID | Case | Build / environment | Actual result | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| RUN-10 | TC-02 | demo-12 / isolated-demo | Denied; no job created | Passed | Demo log E10 |
| RUN-11 | TC-03b | demo-12 / isolated-demo | File returned at expiry | Failed | Demo log E11; defect D4 |
| RUN-12 | TC-03c | demo-12 / isolated-demo | Clock fixture unavailable | Blocked | Fixture issue F2 |

In real documentation, evidence must be retrievable and the result must match
the observation. Keep old run history when the same case is rerun on a new build.

## Writing Corrections

- Replace “verify the result is correct” with named output values or invariants.
- Split cases whose different outcomes cannot be diagnosed independently.
- Link a common fixture instead of copying a large setup into every row.
- Record a failed result without rewriting the expected result to match it.

## Completion Check

Confirm traceability, reproducible inputs, action order, meaningful expectations,
and independent setup/cleanup. Check that every claimed executed status includes
the build, environment, actual observation, and evidence. For Google Sheets,
separate case definitions from runs using the platform guide.
