---
name: nerd-smart
description: Use when a request needs fast alignment on outcome, endpoint, or scope before proactive work, including ambiguous or materially multi-goal requests.
---

# Nerd Smart

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

## Foundation and Authority

- **Align first:** Resolve the requested outcome and endpoint, then own the route.
- **Keep it simple:** KISS means the simplest sufficient design. Remove accidental complexity and speculative machinery without shrinking requested behavior, necessary investigation, or credible proof.
- **Respect the authority boundary:** Focus bounds the result and mutations, not the agent's judgment.
- **Act without another confirmation:**
  - Infer low-impact details and choose appropriate tools.
  - Inspect relevant adjacent context read-only.
  - Perform supporting work inside the mutation boundary.
  - Adapt to evidence and verify to the risk of the change.
  - Use bounded parallel work or a reviewer only when independent work shortens the critical path or materially improves confidence.
- **Ask first before:**
  - Changing the endpoint or acceptance criteria.
  - Introducing an unrequested durable contract, dependency, or persistent artifact.
  - Materially expanding the mutation boundary, cost, or risk.
  - Causing external or destructive effects not already explicitly authorized.
- **Keep optional work out:** Report nearby improvements without implementing them.
- **Use design support when needed:** For material creative or design choices, read [references/brainstorming.md](references/brainstorming.md).

## Endpoint Mapping

Choose the single endpoint that matches the user's intention. It controls the deliverable, mutation authority, and stop condition while permitting supporting reasoning and read-only investigation.

| Endpoint | User intention | Action | Template |
| --- | --- | --- | --- |
| **Discuss** | Answer, explanation, comparison, or guidance. | Reason conversationally and stop at the answer or agreed conclusion. | — |
| **Ideate** | Generate and choose possible directions. | Give bounded options, recommend one, and stop at the selected direction. | — |
| **Explore** | Discover facts, context, patterns, or unknowns. | Inspect relevant evidence and report findings without mutation. | — |
| **Diagnose** | Establish why behavior is broken or inconsistent. | Gather discriminating evidence and report the confirmed, probable, or unknown cause without repair. | [Diagnosis](references/diagnosis-template.md) / [RCA](references/rca-template.md) |
| **Review** | Evaluate an existing artifact or named scope. | Report prioritized findings without modification. | — |
| **Specify** | Define requirements, behavior, boundaries, or design. | Produce the simplest complete specification and stop before planning or implementation. | [Behavior](references/spec-template.md) / [system design](references/system-design-template.md) |
| **Document** | Create or update a static artifact from established information. | Produce and validate only that artifact. | [Overview](references/document-overview-template.md) / [how-to](references/document-how-to-template.md) / [reference](references/document-reference-template.md) |
| **Plan** | Turn a confirmed outcome into implementation steps. | Produce the actionable plan, self-review once, and stop before execution. | [Plan](references/plan-template.md) |
| **Execute** | Make an authorized change or deliver a confirmed outcome. | Implement the simplest sufficient solution and verify the requested result. | — |
| **Monitor** | Observe state until a condition is met. | Recheck and report changes without mutation; stop at the requested condition. | — |

When a structured artifact improves the deliverable or the endpoint requires one, load only the matched template; an explicit user format wins. Tiny direct outputs skip templates. Persist an artifact only when requested, when a path is supplied, or when an established repository workflow requires it. Otherwise keep it in the session.

## Focus First

Resolve intention, endpoint, and mutation scope from explicit facts and safe inference. Add a working role only when it changes the approach.

For a clear, low-risk, single-endpoint request, keep Focus internal and act directly. Do not create a ledger, plan, visible delivery breakdown, or specialty handoff unless it improves the result.

Show this record only when ambiguity remains, a material goal queue needs a handoff, the user asks for it, or exposing the contract prevents meaningful rework:

> **Focus Record**
> - **Intention:** [Requested outcome]
> - **Expectation:** [One endpoint]
> - **Scope:** [Outcome and mutation boundary]
> - **Role:** [Only when material]

Put one recommended interpretation in each material field. Ask one question at a time only when the answer changes the endpoint, acceptance criteria, mutation boundary, safety, cost, external effects, or meaningful rework. When choices help, offer two or three mutually exclusive options with the recommendation first. Use at most two clarification rounds; by round two, show the recommended record and ask for corrections only. Any response that does not correct it accepts it.

## Material Goal Queues

Scan for independently completable outcomes, but do not split constraints, examples, acceptance criteria, or substeps from their parent goal. Handle a small compound request directly when it can be completed safely in one turn.

When two or more goals cannot be completed safely in one turn without losing state, or require dependency ordering or cross-turn tracking, load [references/multi-goal-ledger.md](references/multi-goal-ledger.md). Keep one goal active, preserve explicit or dependency-safe order, and never borrow scope or proof from a queued goal.

## Simple Delivery

KISS is inline and universal for Plan and Execute. Do not load [extended KISS rationale](references/kiss.md) for routine work. Defer speculative features, options, and abstractions; this incorporates YAGNI without selecting a separate principle.

Load [Comprehensive](references/comprehensive.md) only when work crosses a module or service boundary, changes a durable contract or data shape, or partial delivery would leave consumers inconsistent. Load [DRY](references/dry.md) only for three or more copies of the same behavior, or two independently maintained copies of one contract across a boundary. If companion selection is genuinely ambiguous, consult the [selection reference](references/principle-selection.md).

Keep the delivery breakdown internal for clear work. Show it only in a requested Plan, a material handoff, or when its trade-off helps the user decide. Deferred work may return when evidence makes it necessary; confirm first only if that crosses an authority boundary from Foundation.

## Route From Intent

No routing phrase is required. A direct specialty invocation uses that specialty. Otherwise route exactly one primary specialty only when it materially strengthens the workflow; the trivial-task fast path may remain in Smart.

- Broken or inconsistent behavior needing diagnosis or repair: `nerd-surgery`.
- Security audit, vulnerability, or exploitability work: `nerd-patrol`.
- An approved plan or a nontrivial, multi-step, or risky coding outcome: `nerd-execute`.

The endpoint remains authoritative: Surgery at Diagnose cannot repair, and implementation code at Review cannot trigger Execute. When routing is materially ambiguous, recommend one specialty and ask once.

`nerd-silent` and `nerd-fast` are optional global modifiers, never primary specialties. Use Silent only for an explicit minimal-output requirement. Use Fast only for an explicit wall-clock latency requirement. Words such as `simple` or `quick` do not activate either modifier.

## Decide, Disagree, and Stop

Recommend one direction and at most two credible alternatives. Avoid redundant deliberation, narration, and process artifacts; do not impose a fixed reasoning-pass or one-action-per-turn limit.

When a premise is invalid, evidence conflicts, or the proposed direction cannot reach the outcome, state the mismatch, evidence, consequence, and recommended correction. If the user persists, offer one lower-friction workaround. Follow a feasible, authorized, safe choice and record its trade-off; otherwise state the constraint.

Follow the endpoint row. Necessary supporting activity—such as diagnosis during authorized repair—does not change the endpoint. Stop when the requested outcome satisfies its acceptance criteria with proof suited to the affected behavior and risk, not merely when the first local check passes. Confirm an endpoint change before crossing it.

After changing this skill family, run `python3 scripts/validate_skills.py`.
