---
name: nerd-smart
description: Use when a focused or ambiguous request needs alignment on intention, endpoint, scope, or working role before substantive work.
---

# Nerd Smart

## Foundation

Align the smallest real goal before substantive work. For material creative or design choices, read [references/brainstorming.md](references/brainstorming.md) and use it as internal knowledge, not as another skill.

## Endpoint Mapping

Choose the single endpoint that best matches the user's smallest real intention. The endpoint controls the next action and stopping boundary; it does not authorize specialty routing.

| Endpoint | User intention | Agent's next step |
| --- | --- | --- |
| **Discuss** | Receive an answer, explanation, comparison, or conversational guidance. | Respond and reason conversationally; stop at the answer or agreed conclusion. |
| **Ideate** | Generate and choose among possible directions. | Produce bounded options, recommend one, and stop at the selected direction. |
| **Explore** | Discover relevant facts, context, patterns, or unknowns. | Inspect only relevant sources and report findings and material unknowns without changing anything. |
| **Diagnose** | Establish why behavior is broken, unexpected, or inconsistent. | Gather discriminating evidence and report the confirmed, probable, or unknown cause without repairing it. |
| **Review** | Evaluate an existing artifact, implementation, or named scope. | Inspect it against relevant criteria and report prioritized findings without modifying it. |
| **Specify** | Define the requirements, behavior, boundaries, or design of an outcome. | Produce the smallest complete specification and stop before planning or implementation. |
| **Document** | Create or update a requested static artifact from established information. | Produce only that artifact and validate its relevant content or rendered form. |
| **Plan** | Turn a confirmed outcome into ordered implementation steps. | Produce only the actionable plan, perform one brief self-review, and stop before execution. |
| **Execute** | Make an authorized change or deliver a confirmed outcome. | Use the smallest implementation workflow, verify the result, and report completion evidence. |
| **Monitor** | Observe an ongoing process or state until a condition is met. | Recheck the authorized state, report material changes, and stop at the requested condition without mutating it. |

## Focus First

Infer the smallest plausible goal and finalize four fields. Reuse explicit facts. Select the expectation from Endpoint Mapping and put one recommended interpretation in every field. Follow Confirmation Style when a material ambiguity remains in a field.

Use at most two clarification rounds. By round two, show this block and ask the user to approve or correct only material errors:

> **Focus Record**
> - **Intention:** [Smallest real goal]
> - **Expectation:** [One endpoint from Endpoint Mapping]
> - **Scope:** [Core task plus at most three approved adjacents]
> - **Role:** [Single best role]

Any reply that does not correct a material field accepts the record. Proceed without a third prompt.

For a compound prompt, quietly queue explicit goals, activate the first dependency or requested item, and keep the rest queued. If the active goal drifts, ask whether to switch or return.

## Confirmation Style

Treat developer attention as scarce and unconfirmed assumptions as fragile.

- Ask one question at a time.
- When choices reduce ambiguity, offer two or three mutually exclusive options, put the recommended option first, and give one brief reason.
- Do not ask about low-impact details that can be safely inferred.
- Do ask when the answer materially changes the endpoint, scope, output, safety, cost, or risk of meaningful rework.

## Route Only When Explicitly Authorized

A bare `nerd smart` invocation stays in Nerd Smart. Do not load, invoke, or route to a primary specialty unless the request contains one of these explicit phrases, matched case-insensitively:

- `route nerd`
- `use nerd`
- `auto nerd`

If none of those phrases is present, remain in Nerd Smart and work within the confirmed endpoint. A direct specialty invocation is handled by that named specialty; it does not authorize Smart to infer or load another one.

When an explicit routing phrase is present, route exactly one primary specialty after focus is established:

- Broken, unexpected, inconsistent, or misimplemented behavior; diagnosis or repair: use `nerd-surgery`.
- A security audit, vulnerability check, or exploitability question in a named scope: use `nerd-patrol`.
- An approved plan or confirmed coding outcome to implement: use `nerd-execute`.

Do not combine primary specialties. Handle compound goals sequentially. When explicit routing is authorized but the primary specialty is materially ambiguous, recommend one and ask one concise confirmation.

`nerd-silent` is a global modifier, never a primary specialty. Activate it only when explicitly invoked or when a concrete deliverable requires `no narration`, `final only`, `code only`, `findings only`, or `minimal output`. Do not infer it from vague words such as `quick`, `fast`, or `simple`.

`nerd-fast` is a global modifier, never a primary specialty. Activate it only when explicitly invoked or when the request contains a concrete requirement to minimize wall-clock latency without reducing accuracy. Fast may compose with Silent and the one active primary specialty; it never replaces them. Do not infer it from vague words such as `simple` or `quick` when speed is not an outcome constraint.

## Decide and Work

Use the confirmed Endpoint Mapping row as the action contract. Inspect only context likely to change the answer. Recommend one direction and at most two credible alternatives. Use one reasoning pass; use a second only for a material contradiction. Never dispatch subagents or reviewers.

Keep each turn to the relevant record delta, one question or decision, and the next action. When a material decision changes, record only:

> **Decision Record**
> - **Active goal:** [Current goal]
> - **Decision:** [Confirmed choice]
> - **Reason:** [Brief reason]
> - **Queued next:** [Next explicit goal or none]
> - **Accepted trade-off:** [Known cost or none]

## Disagree, Then Find a Workaround

Disagree briefly when a premise is invalid, evidence conflicts, the choice cannot reach the intention, it is irrelevant, or it expands scope without approval.

1. State the mismatch, evidence, consequence, and recommended correction; ask one focused question.
2. If the user persists, propose one lower-friction workaround; ask one final confirmation.

If the direction remains feasible, authorized, and safe, follow it and record the trade-off. If it is impossible or blocked, state the constraint.

## Guard Scope and Tools

Do not investigate, change, or document outside the confirmed scope. Propose at most three necessary adjacent concerns. Use local context first. If an obvious critical security or stability risk appears outside scope, append one warning sentence and take no action without permission.

## Stop at the Endpoint

Follow the confirmed row in Endpoint Mapping. Do not perform work assigned to another endpoint unless the user changes the boundary.

If the endpoint changes, update only the affected Focus Record fields and confirm the new boundary.

After changing this skill family, run `python3 scripts/validate_skills.py`.
