---
name: nerd-explore
description: Use when discovering codebase facts, context, patterns, constraints, or unknowns through focused, incremental, read-only investigation without diagnosing a failure or modifying state.
---

# Nerd Explore

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

<INHERITANCE>
- Use `nerd-smart` first and consume its resolved Focus Record.
- Accept only the **Explore** endpoint.
- If the record is missing, unresolved, or names another endpoint, return to Smart before continuing.
</INHERITANCE>

## Focus Record

- Keep the resolved Focus Record as the exploration boundary.
- Track only: **Confirmed**, **Hypotheses**, **Unknowns**, and **Next evidence**.
- Attach a path, symbol, line, command result, or other source to each confirmed fact.
- Keep one active question and one smallest useful next read.

## Exploration Loop

1. **Start direct**
   - Open the exact file, path, symbol, error, or artifact named by the user first.
   - Read the relevant region or outline before reading the whole file.
2. **Read related evidence**
   - Follow direct imports, callers, callees, types, tests, config, schemas, or sibling implementations one hop at a time.
   - Prefer targeted keyword/symbol searches and narrow line ranges.
   - Do not inventory or read whole folders or the project unless the focus requires it.
3. **Guess, then verify**
   - Infer the likely stack or framework from the first evidence.
   - Verify the guess with focused keywords in manifests, imports, config, or scripts.
   - Keep guesses labeled as hypotheses until verified.
4. **Expand incrementally**
   - After each read, update the Focus Record and choose the next smallest evidence gap.
   - Expand only when current evidence cannot answer the active question.
5. **Stop on sufficiency**
   - Stop when the requested fact, pattern, constraint, or unknown is supported.
   - Report **Facts**, **Inferences**, **Unknowns**, and exact **Sources** when useful.

## Boundaries

- Do not modify files or external state.
- Do not prescribe a repair, conduct a review, or advance into specification, planning, or implementation.
- Return to Smart before crossing to another endpoint.
