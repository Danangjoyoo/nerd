# Test Review Collaboration

Use for test strategy, plans, cases, automated tests, execution records, and
claims of coverage or readiness. Establish which of these is in scope before
judging it: reviewing a plan does not imply executing a suite.

## Companion Sequence

| Step | Skill | Bounded task | Return to Review |
| --- | --- | --- | --- |
| Establish traceability | `nerd-document` | Connect accepted requirements and risks to plan/case/run records | Requirement → scenario → expected result → available evidence |
| Challenge coverage | `nerd-brainstorm` | Seek plausible ways the target defect escapes the proposed checks | Relevant counterexample and its risk; assumptions labeled |
| Inspect proof strength | Review | Check assertions, setup, isolation, environment, and actual records | False pass, nondeterminism, missed contract, or unsupported status |
| Check reporting | `nerd-document` | Verify case definitions and run status are distinct and consistent | Build/environment/evidence contradictions or gaps |

Read nerd-document's test-plan or test-cases guide according to the artifact.
For executable tests, add the matching stack/framework references. Do not
require every testing category, complete coverage, or a particular test style
without an established contract or credible defect.

## Review Lenses

| Level | Check | Finding evidence |
| --- | --- | --- |
| 1 | Reproducible steps, fixtures, assertions, expected results | Case cannot run, wrong behavior passes, or assertion does not observe the contract |
| 2 | Requirement/risk coverage, build/environment, result traceability | A concrete failure escapes coverage or a claimed pass lacks required observation |
| 3 | Test boundaries, oracle independence, isolation, failure diagnosis | Shared assumptions or architecture systematically hide material defects |

Ask whether the test fails when the target behavior is wrong. Trace mocks and
fixtures to the boundary they replace; an assertion on the mock's own return
value may prove nothing about the system. Check time, ordering, concurrency,
cleanup, and data isolation only where they can affect this scope. Compare
results with the actual tested revision and environment.

## Proof and Completion

For example, an expiry test that covers only after expiry cannot substantiate
an explicit “at expiry” guarantee. Locate the requirement and exact missing
boundary before reporting. Treat Not run, Blocked, Failed, and Passed as distinct;
a written expected result is never execution evidence. Run existing narrow,
non-mutating checks only when permitted and useful. Do not add tests, fix flaky
cases, change expected results, or certify release readiness through review.
