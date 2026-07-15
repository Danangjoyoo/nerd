---
name: nerd-patrol
description: Use when examining a confirmed code, pull request, module, application, endpoint, dependency, or configuration scope for vulnerabilities, unsafe behavior, or exploitability.
---

# Nerd Patrol

## Inheritance

Use `nerd-smart` first and reuse its approved Focus Record. This specialty adds security examination without broadening the confirmed scope.

At an execute endpoint, read [references/test-first-remediation.md](references/test-first-remediation.md) before changing code and [references/verification.md](references/verification.md) before claiming remediation.

## Generic Security Mappings

Use a mapping only when the confirmed scope does not already identify the threat class or next evidence to inspect. Pick the single closest row; skip this table when the evidence path is already clear. Mappings select evidence; they never establish a finding.

| # | Signal | Trace | Minimum safe proof |
| --- | --- | --- | --- |
| **1** | Authentication or session | Entry point → credential, token, or session validation → privileged identity | Show that a missing, forged, stale, or misbound identity can reach a protected action. |
| **2** | Authorization or object access | Actor-controlled identifier or action → policy check → protected object or operation | Show a cross-user, cross-tenant, or cross-role access path with harmless test data. |
| **3** | Injection or command execution | Attacker-controlled input → validation and transformation → query, template, interpreter, or shell sink | Show that a harmless marker reaches sink semantics rather than only appearing as data. |
| **4** | File or path handling | Filename, path, or archive input → normalization → filesystem or object-storage operation | Show a read, write, or overwrite crossing the intended boundary in an isolated fixture. |
| **5** | Deserialization or parsing | Untrusted payload → parser or type reconstruction → side effect, state change, or resource use | Show a crafted payload reaching unsafe behavior without destructive gadgets or external impact. |
| **6** | Secrets or cryptography | Secret, key, password, token, or nonce lifecycle → storage, logging, transport, comparison, or rotation | Show reachable exposure, reuse, weak verification, or incorrect lifecycle handling using synthetic values. |
| **7** | Network request forgery | Attacker-controlled URL, host, address, or header → resolver or client → destination | Show an isolated request can reach a prohibited loopback, metadata, or internal target. |
| **8** | Browser or client security | Untrusted content or state → DOM, storage, navigation, message, or origin boundary | Show executable interpretation, unsafe navigation, or cross-origin state impact with a harmless payload. |
| **9** | Concurrency or business logic | Attacker-repeatable sequence → transaction, idempotency, or state transition → protected invariant | Show a controlled ordering or replay violates the invariant in a disposable environment. |
| **10** | Dependency or configuration exposure | Installed version, effective configuration, or feature flag → affected capability → reachable path | Show that the vulnerable capability is enabled, deployed, and attacker-reachable; an advisory alone is insufficient. |

## Scope First

Act as the Police: make evidence-bound security judgments inside the user's target.

- Default to explore or document. Change code only when the Focus Record says execute.
- Derive scope from the prompt: changed PR files, named files, module, application, endpoint, or concern.
- If scope is materially ambiguous, show exactly one Scope Check.
- Inspect direct callers, callees, configuration, and dependencies only when needed to prove reachability or impact. This evidence boundary does not expand the audit.
- If an obvious critical issue lies outside scope, warn in one sentence without investigating it.

## Examine Relevant Threats

Choose only two or three classes implied by scope:

- Input handling, injection, or deserialization.
- Authentication, authorization, or state transitions.
- Sensitive data, secrets, or logging.
- Dependency or API misuse.
- CI, infrastructure, or configuration when included.
- Race or integrity failures for shared state.

Do not run broad scanners automatically. Stop examining a class when evidence makes it irrelevant. Perform a comprehensive audit only when explicitly requested.

## Classify Evidence

- **Confirmed Finding:** Direct evidence proves a reachable source-to-sink path and concrete impact.
- **Needs Validation:** A credible signal lacks reachability, environment, version, or exploitability evidence. Request the smallest missing item.
- **Dismissed:** Evidence proves a false positive, unreachable path, test-only behavior, or scoped irrelevance. Keep it out of results.

For dependencies, confirm the installed version and reachable usage; an advisory alone is not a finding. Report confirmed findings first in severity order, then validation needs. Do not inflate counts with duplicates.

## Prove Safely

Use the lowest sufficient proof rung: static reachable path, non-destructive local reproduction, authorized isolated environment, then authenticated staging only with explicit authorization. Never exploit production, exfiltrate data, reveal secrets, or perform destructive actions.

Provide an exact harmless payload only when materially useful. Otherwise provide a sanitized request, concise attack path, and preconditions. Unsafe or impossible proof remains Validation Needed.

Remediate only confirmed findings at an execute endpoint. If no findings qualify, say `No confirmed findings within this scope`; never claim the system is secure or append generic advice.

## Records

**Patrol Scope**
- **Target:** [PR changes, files, module, application, or specific part]
- **Question:** [Security behavior being examined]
- **Evidence boundary:** [Callers, callees, configuration, or dependencies needed for reachability]
- **Excluded:** [Everything outside the confirmed scope]

**Scope Check**
- **Likely scope:** [Smallest inferred target]
- **Include:** [Files, module, application, PR, or concern]
- **Exclude:** [Everything else]
- **Confirm:** Use this scope / correct it

**Security Finding**
- **Severity:** [Critical, high, medium, or low]
- **Location:** [Exact file, line, endpoint, or configuration]
- **Reachability:** [Attacker-controlled source to vulnerable sink]
- **Impact:** [Concrete consequence]
- **Evidence:** [What confirms the finding]
- **Proof:** [Safe reproduction or concise attack path]
- **Remediation:** [Smallest effective correction]

**Validation Needed**
- **Signal:** [Credible concern]
- **Missing evidence:** [What prevents confirmation]
- **Request:** [One smallest evidence item]

**Patrol Result**
- **Scope:** [Exact target examined]
- **Examined:** [Threat classes and evidence boundaries]
- **Confirmed:** [Finding count and highest severity]
- **Needs validation:** [Unresolved signal count]
- **Not examined:** [Explicit exclusions or unavailable evidence]
- **Recommendation:** [Highest-priority next action or none]
