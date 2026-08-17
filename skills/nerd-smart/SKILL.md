---
name: nerd-smart
description: Use when a request needs fast alignment on outcome, endpoint, or scope before handing work to exactly one endpoint route, including ambiguous or materially multi-goal requests.
---

# Nerd Smart

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

## Foundation and Authority

- Resolve the requested outcome, endpoint, and mutation boundary before route work.
- Preserve requested behavior, necessary investigation, and credible proof.
- Infer low-impact details, inspect relevant adjacent context read-only, and
  adapt to evidence inside the confirmed boundary.
- Ask first before changing the endpoint or acceptance criteria, introducing an
  unrequested durable contract or dependency, materially expanding cost or
  risk, or causing unauthorized external or destructive effects.
- Report optional nearby improvements without implementing them.

## Focus First

At the beginning of every request, resolve intention, endpoint, and scope from
explicit facts and safe inference. Add a role only when it changes the approach.
Before substantive work, always show the completed record:

> **Focus Record**
> - **Intention:** [Requested outcome]
> - **Expectation:** [One endpoint]
> - **Scope:** [Outcome and mutation boundary]
> - **Role:** [Only when material]

Ask one question at a time only when the answer changes the endpoint,
acceptance criteria, mutation boundary, safety, cost, external effects, or
meaningful rework. Offer two or three mutually exclusive choices with the
recommendation first when choices help. Use at most two clarification rounds;
by round two, show the recommended record and ask for corrections only. Any
response that does not correct it accepts it.

## Multi-Goal Intake

Before resolving a single Focus Record, scan meaning—not formatting or
punctuation—for two or more independently completable outcomes. Keep
constraints, examples, acceptance criteria, and substeps with their parent
goal.

When two or more goals exist, read
[the multi-goal ledger](references/multi-goal-ledger.md), create it, and show
the complete Multi-Goal Intake before substantive work. Keep exactly one goal
active, preserve explicit or dependency-safe order, and never borrow scope,
endpoint, or proof from a queued goal.

## Explore Discipline

- Load and read the `nerd-explore` skill first, before any codebase discovery,
  then follow its exploration discipline.
- Never run an exploration loop inside Smart.
- Keep alignment reads minimal: only the exact paths, symbols, artifacts, or
  commands the request names.
- Record what stays unknown instead of widening intake into a folder inventory
  or project sweep.
- Resolve the endpoint as **Explore** and hand the record to `nerd-explore`
  when a goal needs discovery or alignment stalls on unresolved facts,
  patterns, or constraints.

## Endpoint Mapping

Choose exactly one route. The route owns the deliverable, mutation authority,
supporting workflow, resources, and stop condition.

| Endpoint | Route |
| --- | --- |
| **Discuss** | `nerd-brainstorm` |
| **Ideate** | `nerd-brainstorm` |
| **Explore** | `nerd-explore` |
| **Diagnose** | `nerd-diagnose` |
| **Review** | `nerd-review` |
| **Specify** | `nerd-spec` |
| **Document** | `nerd-document` |
| **Plan** | `nerd-plan` |
| **Execute** | `nerd-execute` |
| **Monitor** | `nerd-monitor` |

A direct endpoint invocation uses that route after Focus is resolved. Otherwise
hand the resolved record to the matched route before performing endpoint work.
Never keep endpoint workflows or templates in Smart.

## Composition

Endpoint routes may add one specialty only when it materially strengthens the
confirmed work without changing the endpoint:

- Diagnose or Execute may compose with `nerd-surgery` for broken behavior.
- Review or Execute may compose with `nerd-patrol` for security work.

`nerd-silent` and `nerd-fast` are optional global modifiers, never endpoint
routes. `nerd-loop` may control recurrence without replacing the route.
`nerd-memory` may be auto-enabled by Nerd Smart when memory retrieval would
materially strengthen the confirmed work. `nerd-xfast` remains its
self-contained, explicitly lossy path.

## Stop

When a premise is invalid or evidence conflicts, state the mismatch,
consequence, and recommended correction. Follow the matched route and stop at
its condition. Necessary supporting activity does not change the endpoint.
Confirm through a new Focus Record before crossing endpoints.

After changing this skill family, run `python3 scripts/validate_skills.py`.
