---
name: nerd-execute
description: Use when implementing an approved written plan or a small confirmed coding outcome in an existing repository, including requests to build, add, change, or write code.
---

# Nerd Execute

<INHERITANCE>
**REQUIRED BASE SKILL:** Use `nerd-smart` first and consume its resolved Focus Record.

A Focus Record is resolved only when all four fields are explicit, the endpoint is **Execute**, and no material ambiguity remains. If it is missing or unresolved, return to Nerd Smart and resolve one material question before continuing. Never mutate before the record is resolved.
</INHERITANCE>

<FAST-TRACK>
The resolved Focus Record is the only universal gate. A current plan, narrower execution scope, TODOs, and verification are conditional. Use this workflow without loading separate implementation workflows unless the user explicitly invokes one or an unusual edge case requires a fuller workflow. Execute inline without subagents.
</FAST-TRACK>

## Rules

Use a mapping only when the task's boundary or proof is unclear. Pick the single closest row as a starting point; user instructions and inspected repository evidence override it. Skip mappings for fully specified tasks.

## Generic Mappings

| # | Signal | Outcome focus | Targeted proof |
| --- | --- | --- | --- |
| **1** | New behavior | Smallest observable behavior and surface | Focused test fails for the missing behavior, then passes. |
| **2** | Bug fix | Reproduced symptom and smallest correction | Regression test demonstrates red then green. |
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
| **Focus Record** | Mandatory | Read and obey the resolved intention, endpoint, scope, and role. Never infer around an unresolved field. |
| **Current plan** | Conditional | If the user created or approved a plan in the current context, read it once and execute its remaining work. Raise only contradictions with the Focus Record, missing prerequisites, or blockers. Otherwise, do not search for, request, or create a plan. |
| **Execution scope** | Conditional | Inherit the Focus Record scope. Define a narrower file or system boundary only when the goal or risk requires it. |
| **TODOs** | Conditional | Write two to five TODOs for multi-step, dependent, or risky work. For a small direct change, execute without a checklist. |
| **Verification** | Conditional | Run the smallest relevant check when behavior, risk, or a completion claim needs proof. When no proportionate check is available, skip it and report **Not verified**. |

## Execute Directly

Begin immediately once the Focus Record is resolved. When a conditional item needs confirmation, ask one question using Nerd Smart's Confirmation Style; otherwise add no gate or setup ceremony.

Inspect repository context only when it can change the implementation or proof. Prefer mandatory repository instructions, relevant authority or configuration, the nearest implementation, and the nearest test. Ask only when inspected evidence exposes a material conflict.

For behavior changes, write or update one focused test, run it to confirm the expected failure, implement the minimum change, then rerun it. For non-behavior changes, edit directly and run the smallest relevant validation. Run a pre-edit baseline only when a quick existing check would distinguish pre-existing failure from the requested change.

Preserve user-authored and unrelated changes. Keep tests beside the behavior they prove. Do not broaden scope or add infrastructure. After a related failure, make at most two evidence-driven correction attempts using the same targeted check. Then stop with one concise blocker stating the evidence and decision needed.

## Finish Briefly

If Verification applies, run the selected check fresh. Do not claim a check passed without fresh output. Report only:

- **Done:** [completed outcome]
- **Verified by:** [command and result]

Use **Not verified** instead of **Verified by** when verification was skipped or remains unavailable. Do not echo diffs or narrate routine tool use unless requested.

After changing Nerd Execute, run `python3 scripts/validate_skills.py`.
