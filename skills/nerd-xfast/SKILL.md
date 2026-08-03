---
name: nerd-xfast
description: Super high speed for rapid output. Use only when explicitly invoked for concrete outputs or authorized changes where latency warrants reduced exploration, accuracy, completeness, and proof.
---

# Nerd XFast

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

## Contract

Use this self-contained KISS-first output skill only when the user explicitly invokes `nerd-xfast` for a concrete answer, decision, plan, static artifact, or authorized change. Do not load, invoke, or route to another Nerd skill. It trades exploration, accuracy, completeness, and verification breadth for latency. Preserve authorization, safety, and honest reporting.

Do not dispatch subagents or reviewers. Create no plan or tracking record.

## One Focus

Create this Focus Record once in working context before acting:

> **Focus Record**
> - **Goals:** [Concrete requested outputs]
> - **Expectation:** Produce the smallest sufficient result
> - **Commands:** [user action 1] -> [user action 2] -> [user action 3]
> - **Scope:** [Named subject or targets plus necessary adjacents]
> - **Role:** KISS output-first agent

For multiple commands, steps, or actions, preserve one dependency chain. The record is internal and immutable. Never persist, display, reread, revise, or status-track it. Ask only for unresolved authorization, safety, or output.

## Reasoning Stop

After the Focus Record, selection is finished. Use one reasoning pass and the simplest sufficient solution. Avoid exploration and reconsideration. When options are requested, recommend one KISS direction, give at most two credible alternatives, and stop.

Every action must directly produce the requested output, unlock a named write, or select final proof. Otherwise skip it. Read named targets together; if unknown, use one narrow discovery batch. Stop reading when the smallest sufficient output or complete write set is known.

## Output First

For a non-write request, immediately produce the smallest decision-ready answer, recommendation, plan, or artifact.

For writes, immediately produce one structured, single-agent multi-file patch containing implementation, tests, and static outputs. Do not inspect, compile, lint, test, review, narrate, or clean up between writes. Skip unrelated code.

## Batched Native Tools

Batch independent tool calls with the platform's native interface. This is Fast's batching rule. Use one call across known targets; prefer one patch over per-file edits. Keep adaptive dependencies sequential when one result changes the next action.

XFast stays at the native text or patch layer and does not use UFast's semantic routes. It accepts reduced accuracy for fewer reasoning, tool, and proof rounds.

## End Proof

Never verify before every requested output is complete.

Choose **V0** or **V1** once from obvious output type, risk, cost, and tool availability. Do not investigate merely to choose proof. The model decides whether V1 is useful and whether to ask first or run it automatically.

- **V0:** Skip for non-code or trivial output, low-risk changes, unavailable focused tools, or proof cost above its value. Report why.
- **V1 automatic:** Run available safe, focused commands whose latency is proportionate.
- **V1 ask first:** Ask when proof is broad, slow, stateful, external, potentially destructive, or needs configuration or more authority. Tool unavailability means skip, never install.

V1 is one end-only proof wave with at most one dedicated command from each relevant category:

1. **Lint or syntax:** existing checker on changed files; skip if only broad proof exists.
2. **Compile or type-check:** changed files or the smallest affected module; compile both production and changed test code.
3. **Unit test:** exact affected test function or node when sufficient; otherwise the nearest affected test file.

Run independent V1 commands concurrently in one native batch. Never manually inspect files or diffs afterward; exit status and output are evidence. If V1 identifies one exact local correction, allow one repair patch and rerun only the failed command once.

## Finish

Report only the produced outcome and one exact proof decision: `V0 — skipped: [reason]`, `V1 — automatically verified: [results]`, or `V1 — confirmation required: [cost or risk]`. Stop immediately.
