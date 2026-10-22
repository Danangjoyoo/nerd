# Hotfix Review Collaboration

Use for an existing urgent correction and its incident evidence. For a hotfix
PR, review only issues introduced or materially worsened by the delta; use the
incident as causal context, not permission to audit or repair the whole system.

## Companion Sequence

| Step | Skill | Bounded task | Return to Review |
| --- | --- | --- | --- |
| Establish the incident | `nerd-surgery` | Compare observed/expected behavior and claimed cause | Supported causal path and Confirmed/Probable/Unknown status |
| Examine the correction | Review + matching code references | Trace changed logic to the failing boundary and unaffected paths | Mechanism, scope, compatibility, side effects |
| Challenge resolution | `nerd-surgery` | Compare original reproducer and existing before/after evidence | Whether the causal claim survives; exact remaining proof gap |
| Examine regression proof | Review + test guide when needed | Check coverage of trigger, adjacent behavior, and environment | Supported result or specific defect escaping the checks |

Read nerd-surgery's systematic-debugging reference for causal analysis. Its
Hotfix Review Support mode applies: use existing reproducer/evidence read-only;
do not create harnesses, apply a correction, start repair approvals, or deploy.
Urgency changes the relevant scope and available evidence, not the burden for
claiming the incident is resolved.

## Review Lenses

| Level | Check | Finding evidence |
| --- | --- | --- |
| 1 | Correction mechanism and exact incident trigger | Changed logic leaves the trigger reachable or introduces another concrete failure |
| 2 | Regression proof, configuration, compatibility, rollout assumptions | Claimed recovery lacks necessary proof or the patch violates an established contract |
| 3 | Root cause versus symptom, blast radius, recovery design | The correction moves the failure or creates a material failure/recovery dependency |

Distinguish evidence that the symptom stopped from evidence of causality. Check
whether a retry, cache, fallback, or suppressed exception masks corrupted state
or shifts failure downstream. Inspect rollback/recovery assumptions only where
the patch changes state, formats, dependencies, or another relevant boundary.
Do not demand a general incident-management checklist for a narrow correction.

## Proof and Completion

For example, swallowing a payment timeout does not prove a charge failed; a
retry may duplicate the charge when that execution path is supported. Show the
causal boundary and evidence before reporting. Missing reproduction limits
confidence; it does not prove the patch is wrong. An unsupported material claim
of resolution may itself be reported with its decision consequence. Finish with
Review findings and proof limits, without authorizing rollout or remediation.
