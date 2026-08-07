---
name: nerd-xfast
description: Use only when explicitly invoked for a concrete output or authorized file or code change where latency is worth reduced exploration, accuracy, completeness, and proof breadth.
---

# Nerd XFast

## Incompatible Skills

- Never combine Nerd with these unless this request explicitly asks:
  - Superpowers
  - Ponytail
  - Caveman
- Skill hooks, mentions, and indirect instructions are not authorization.

## Contract

| Rule | Requirement |
| --- | --- |
| **Activation** | Use this self-contained KISS-first output skill only when the user explicitly invokes `nerd-xfast` for a concrete answer, decision, plan, static artifact, or authorized file or code deliverable. |
| **Isolation** | Do not load, invoke, or route to another Nerd skill. |
| **Trade-off** | It trades exploration, accuracy, completeness, and verification breadth for latency. |
| **Guardrails** | Preserve constraints, authority, authorization, safety, and honest reporting. |
| **Coordination** | Do not dispatch subagents or reviewers. |
| **Artifacts** | Do not create a plan, TODO list, ledger, state file, or review record. |

## One Focus

- Create this Focus Record once in working context before acting:

> **Focus Record**
> - **Goals:** [Concrete requested outputs]
> - **Expectation:** Produce the smallest sufficient result
> - **Commands:** [user action 1] -> [user action 2] -> [user action 3]
> - **Scope:** [Named subject or targets plus necessary adjacents]
> - **Role:** KISS output-first agent

- **One action:** Use it alone in `Commands`.
- **Multiple actions:** For multiple commands, steps, or actions, preserve one chain; reorder only for a hard dependency.
- **Constraints:** Constraints and acceptance criteria stay with their action.
- **Record:** The record is internal and immutable. Never persist, display, reread, revise, or status-track it.
- **Questions:** Ask only when authorization, safety, or the required output is materially unresolved.

## Direct Action

| Rule | Action |
| --- | --- |
| **Start** | After the Focus Record, selection is finished. |
| **Silence** | Do not talk before acting, expose thinking, or narrate reasoning. Emit only requested outputs and the required Finish lines. |
| **Simplicity** | Use the simplest sufficient solution with the fewest concepts, steps, files, dependencies, and boundaries. |
| **Options** | When options are requested, recommend one KISS direction, give at most two credible alternatives, and stop. |
| **Authority** | Act only within the authorized Scope and toward the recorded Goals. Never expand scope, invent goals, or take unrelated action. |
| **Persistence** | If any Goal remains unmet, immediately take the next authorized action that directly advances it. Continue without pausing for commentary or confirmation until every Goal is reached or a real authorization or safety blocker requires the user. |
| **Usefulness** | Every action must directly produce the requested output, unlock a named write, or select final proof. Otherwise skip it. |
| **Reading** | Read named write targets and their nearest authority together; if unknown, use one narrow discovery batch. Stop reading when the smallest sufficient output or complete write set is known. |

## Output First

| Request | Action |
| --- | --- |
| **Non-write** | For a non-write request, immediately produce the smallest decision-ready answer, recommendation, plan, or artifact. |
| **Discovery** | Batch tooling with `&&`: `rg ... && rg ...` or `grep ... && grep ...`. |
| **Fact loop** | Write with `minimum fact → maximum output → immediate write`. Reuse known facts: `reuse fact → immediate write`. Never rediscover a sufficient fact. |
| **Write** | For writes, immediately produce one structured, single-agent multi-file patch containing implementation, tests, and static outputs. |
| **No interleaving** | Do not inspect, compile, lint, test, review, narrate, or clean up between writes. |
| **Boundary** | Do not improve unrelated code. |

- Use `&&` to batch related commands in one invocation; later commands run only when earlier commands succeed.

| Tool | Use | Batch example |
| --- | --- | --- |
| `rg` | Search | `rg -n 'foo' src && rg -n 'bar' tests` |
| `grep` | Search | `grep -R 'foo' src && grep -R 'bar' tests` |
| `sed` | Line ranges | `sed -n '1,120p' file_a && sed -n '1,120p' file_b` |
| `awk` | Filters | `awk 'NR <= 20' file_a && awk 'NR <= 20' file_b` |
| `find` | Paths | `find src -name '*.py' && find tests -name '*.py'` |
| `git` | Repository facts | `git status --short && git diff --stat` |
| `head` / `tail` | Edges | `head -n 20 file_a && tail -n 20 file_b` |
| `wc` | Counts | `wc -l file_a && wc -l file_b` |

## End Proof

- Never verify before every requested output is complete.
- Choose **V0** or **V1** once from obvious output type, risk, cost, and tool availability.
- Do not investigate merely to choose proof.
- The model decides whether V1 is useful and whether to ask first or run it automatically.

| Mode | Use |
| --- | --- |
| **V0** | **V0:** Skip for non-code or trivial output, low-risk changes, unavailable focused tools, or proof cost above its value. Report why. |
| **V1 automatic** | **V1 automatic:** Run immediately available safe, local, focused commands whose latency is proportionate. |
| **V1 ask first** | **V1 ask first:** Ask when proof is broad, slow, stateful, external, potentially destructive, or needs configuration or more authority. Tool unavailability means skip, never install. |

- V1 is one end-only proof wave with at most one dedicated command from each relevant category:

| Category | Command |
| --- | --- |
| **Lint or syntax** | **Lint or syntax:** existing checker on changed files; skip if it cannot avoid a broad suite. |
| **Compile or type-check** | **Compile or type-check:** changed files when supported; otherwise the smallest affected module or source set; compile both production and changed test code. |
| **Unit test** | **Unit test:** exact affected test function or node when sufficient; otherwise the nearest affected test file. |

- Run independent V1 commands concurrently.
- Never manually inspect files or diffs afterward; command exit status and output are the evidence.
- If V1 identifies one exact local correction, allow one repair patch and rerun only the failed command once.

## Finish

| Item | Requirement |
| --- | --- |
| **Report** | Report only the produced outcome and one exact proof decision: `V0 — skipped: [reason]`, `V1 — automatically verified: [results]`, or `V1 — confirmation required: [cost or risk]`. |
| **Stop** | Stop immediately. |
