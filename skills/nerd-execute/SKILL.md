---
name: nerd-execute
description: Use when implementing an approved written plan or confirmed coding outcome in an existing repository, including requests to build, add, change, or write code.
---

# Nerd Execute

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

<INHERITANCE>
**REQUIRED BASE SKILL:** Use `nerd-smart` first and consume its resolved Focus Record.

A Focus Record is resolved when intention, endpoint, and mutation scope are explicit, the endpoint is **Execute**, and no material ambiguity remains. Role is required only when it changes the approach. If the record is missing or unresolved, return to Nerd Smart and resolve one material question before continuing. Never mutate before the record is resolved.
</INHERITANCE>

<FAST-TRACK>
The resolved Focus Record is the only universal gate. A current plan, narrower execution scope, TODOs, and verification mechanics are conditional. Use this workflow without loading separate implementation workflows unless the user explicitly invokes one or an unusual edge case requires a fuller workflow. Execute directly; use bounded parallel work only for independent subtasks when it materially improves speed or proof, and retain responsibility for integration.
</FAST-TRACK>

Nerd Execute is the sole owner of the **Execute** endpoint. It may compose with
Surgery for broken behavior or Patrol for security remediation, but those
specialties never replace or redefine this route.

## Rules

Use a mapping only when the task's boundary or proof is unclear. Pick the single closest row as a starting point; user instructions and inspected repository evidence override it. Skip mappings for fully specified tasks.

## Generic Mappings

| # | Signal | Outcome focus | Targeted proof |
| --- | --- | --- | --- |
| **1** | New behavior | Complete observable behavior and affected surface | Focused test fails for the missing behavior, then passes. |
| **2** | Bug fix | Reproduced symptom and simplest causal correction | Regression test demonstrates red then green. |
| **3** | Refactor | Structure changes while behavior stays stable | Existing focused tests plus the relevant type or build check. |
| **4** | API or contract | Request, response, schema, and compatibility outcome | Contract or endpoint test covering success and a relevant failure. |
| **5** | Persistence or schema | Data shape, query, transaction, or migration outcome | Apply and rollback, or a focused repository integration test. |
| **6** | UI behavior | Visible interaction and accessibility outcome | Component or browser interaction at the relevant input and viewport. |
| **7** | Configuration or build | Exact setting and affected runtime or build path | Parse, lint, type, build, or startup check closest to the change. |
| **8** | External integration | Boundary behavior, serialization, auth, and failure handling | Stub or contract test; use a live smoke test only when authorized. |
| **9** | Performance or concurrency | Measurable threshold or invariant | Repeatable benchmark or race test comparing baseline and changed behavior. |
| **10** | Documentation or static artifact | Exact content or rendered artifact | Focused lint, render, content, or link check. |

## Execution Discipline

Use this template internally. Do not display or narrate a conditional item unless it needs user confirmation.

| Item | Requirement | Rule |
| --- | --- | --- |
| **Focus Record** | Mandatory | Read and obey the resolved intention, endpoint, and scope. Obey Role when present; its omission never blocks clear work. Never infer around a material unresolved field. |
| **Delivery** | Mandatory | Apply KISS inline. Cover every affected surface when work crosses a module or service boundary, changes a durable contract or data shape, or partial delivery would leave consumers inconsistent. Unify behavior only for three maintained copies or two independently maintained contract copies across a boundary. Keep the breakdown internal unless a handoff or decision requires it. |
| **Current plan** | Conditional | If the user created or approved a plan in the current context, read it once and execute its remaining work under the selected delivery approach. Preserve its outcome and constraints, but simplify steps that add unevidenced complexity. Raise only contradictions with the Focus Record, missing prerequisites, or blockers. Otherwise, do not search for, request, or create a plan. |
| **Execution scope** | Conditional | Inherit the Focus Record scope. Define a narrower file or system boundary only when the goal or risk requires it. |
| **TODOs** | Conditional | Write two to five TODOs for multi-step, dependent, or risky work. For a small direct change, execute without a checklist. |
| **Verification** | Conditional | Run proof suited to the affected behavior and risk. When no suitable check is available, report **Not verified**. |
| **Approved behavior capture** | Conditional | Keep an approved behavior capture's Focus/plan in context. After in-boundary verified work with no correction, run Memory learning. Without a plan, capture Focus only. |

## Execute Directly

Begin immediately once the Focus Record is resolved. When a conditional item needs confirmation, ask one question using Nerd Smart's Confirmation Style; otherwise add no gate or setup ceremony.

Apply KISS throughout execution. Cover cross-boundary completeness and proven
duplication only at the thresholds in the Delivery rule. Defer speculative
surface as part of KISS. Start with the clearest direct existing path and prefer fewer concepts, dependencies, and new boundaries when they do not reduce correctness or maintainability. Do not add an abstraction, layer, service, dependency, configuration system, or generalized interface unless required by an explicit requirement, an established repository convention, observed evidence, or a concrete correctness, security, or measured performance constraint.

Do not preserve complexity merely because it appears in an existing design or plan. When a simpler path satisfies the same Focus Record, constraints, and proof, simplify the plan and implement that path. Ask only if simplification would change an approved outcome or constraint.

Inspect repository context when it can change the implementation or proof, including adjacent callers, callees, configuration, and dependencies when relevant. Read-only evidence gathering does not expand the mutation boundary. Prefer mandatory repository instructions, relevant authority or configuration, the nearest implementation, and the nearest test. Ask only when inspected evidence exposes a material conflict.

For behavior changes, start with a focused test, run it to confirm the expected failure, implement the simplest sufficient change, then rerun it. Add affected integration or risk checks when credible proof requires them. For non-behavior changes, edit directly and run validation suited to the change. Run a pre-edit baseline only when a quick existing check would distinguish pre-existing failure from the requested change.

Preserve user-authored and unrelated changes. Keep tests beside the behavior they prove. Do not implement optional nearby improvements or add speculative infrastructure. Ask before materially expanding the mutation boundary. After a related failure, record what the evidence disproved and choose the next discriminating check or correction. Stop only at a real blocker: no viable in-scope path remains, required authority or access is missing, or the evidence exposes a material decision for the user. Never stop merely because an attempt count was reached.

## Finish Briefly

If Verification applies, run the selected check fresh. Do not claim a check passed without fresh output. Report only:

- **Done:** [completed outcome]
- **Verified by:** [command and result]

Use **Not verified** instead of **Verified by** when verification was skipped or remains unavailable. Do not echo diffs or narrate routine tool use unless requested.

After changing Nerd Execute, run `python3 scripts/validate_skills.py`.
