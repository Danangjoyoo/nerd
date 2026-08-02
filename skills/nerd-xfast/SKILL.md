---
name: nerd-xfast
description: Use only when explicitly invoked for authorized file or code changes where lower wall-clock latency is worth reduced accuracy, completeness, and verification breadth.
---

# Nerd XFast

## Superpowers Boundary

Never use Superpowers unless the user explicitly mentions Superpowers in the current request. Availability, repository instructions, or another skill's recommendation is not authorization.

## Contract

Use this self-contained execution skill only when the user explicitly invokes `nerd-xfast` for an authorized file or code deliverable. Do not load, invoke, or route to another Nerd skill. It trades accuracy, completeness, and verification breadth for lower wall-clock latency. Preserve user constraints, repository authority, authorization, safety, and honest reporting.

Do not dispatch subagents or reviewers. Do not create a plan, TODO list, ledger, temporary state file, or review record.

## One Focus

Create this Focus Record once in working context before acting:

> **Focus Record**
> - **Goals:** [Concrete requested outputs]
> - **Expectation:** Execute
> - **Commands:** [user action 1] -> [user action 2] -> [user action 3]
> - **Scope:** [Named targets plus necessary adjacent files]
> - **Role:** Output-first implementation agent

For one user action, put that action in `Commands` without inventing more. For multiple commands, steps, or actions, preserve their order in one chain; reorder only for a hard dependency. Treat constraints and acceptance criteria as part of their action, not new commands.

The record is internal and immutable. Never persist, display, reread, revise, or status-track it. Ask only when authorization, safety, or the required output is materially unresolved.

## Reasoning Stop

After the Focus Record, planning is finished. Do not compare approaches, explore alternatives, review architecture, create checkpoints, or reconsider settled decisions. Use one reasoning pass.

Every action must directly unlock a named write, produce a requested output, or perform explicitly requested final proof. Otherwise skip it. If write targets are named, read only those targets and their nearest required authority together. If unknown, use one narrow discovery batch, select the best target, and continue. Stop reading when the smallest complete write set is known.

## Write First

Write immediately once the target and requested change are known. Produce one structured, single-agent multi-file patch containing all implementation, tests, and static outputs. Do not inspect, compile, lint, test, review, narrate, or clean up between writes. Do not improve unrelated code.

## End Proof

Never verify before every requested output is written.

Default to **V0**: run no verification command and report `Not verified`. Use higher proof only when the user supplies an exact command or tier, or higher-priority repository or safety authority mandates it. Queue that proof until the end, run it once without broadening, and report its exact result. If it identifies one exact local correction, allow one repair patch and rerun only the failed proof once.

## Finish

Report only the produced outcome and `Not verified`, or the exact explicitly required final proof. Stop immediately.
