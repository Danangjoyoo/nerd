---
name: nerd-execute
description: Use when implementing an approved written plan or a small confirmed coding outcome in an existing repository, including requests to build, add, change, or write code.
---

# Nerd Execute

<INHERITANCE>
**REQUIRED BASE SKILL:** Use `nerd-smart` first and reuse its approved Focus Record.
</INHERITANCE>

<FAST-TRACK>
This lean workflow includes the essential plan-execution, test-first, recovery, and completion-evidence rules. Use it without loading separate implementation workflows unless the user explicitly invokes one or an unusual edge case requires a fuller workflow. Execute inline without subagents.
</FAST-TRACK>

## Rules

Use a mapping only when the task's boundary or proof is unclear. Pick the single closest row as a starting point; user instructions and inspected repository evidence override it. Skip mappings for fully specified tasks.

## Generic Mappings

| # | Signal | Contract focus | Targeted proof |
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

## Gate Repository Pattern Context

Classify the work before repository exploration:

- **Non-code:** Skip repository-pattern context entirely and do not ask about it.
- **Code:** Before searching repository conventions, configuration, analogues, architecture, or test patterns. Search for current pattern first, then confirm to follow the existing pattern or not.

If approved, inspect only relevant authority/configuration, the nearest implementation, and the nearest test. If declined, inspect only named target files, mandatory repository instructions, and directly required tests or dependencies. Never create a repository-pattern artifact unless requested.

## Execute Directly

Make the first user-facing message only the coding gate or, for fully specified non-code work, the contract. Combine any required skill-use announcement into that message instead of sending setup narration. If essential input is missing, ask one focused question before forming the contract.

After the gate and any essential clarification, emit one line:

`Contract: [outcome] | Files: [boundary] | Verify: [targeted check]`

Track a short checklist internally. Use two to five internal items only for multi-step work; do not create milestones, checkpoints, gravity records, or routine status templates. Ask one focused question only when ambiguity materially changes the result.

For behavior changes, write or update one focused test, run it to confirm the expected failure, implement the minimum change, then rerun it. For non-behavior changes, edit directly and run the smallest relevant validation. Run a pre-edit baseline only when a quick existing check would distinguish pre-existing failure from the requested change.

Preserve user-authored and unrelated changes. Keep tests beside the behavior they prove. Do not broaden scope or add infrastructure. After a related failure, make at most two evidence-driven correction attempts using the same targeted check. Then stop with one concise blocker stating the evidence and decision needed.

## Finish Briefly

Run fresh verification scaled to the changed surface. Do not claim success without its output. Report only:

- **Done:** [completed outcome]
- **Verified by:** [command and result]

Add **Not verified** only when an evidence gap remains. Do not echo diffs or narrate routine tool use unless requested.

After changing Nerd Execute, run `python3 scripts/validate_skills.py`.
