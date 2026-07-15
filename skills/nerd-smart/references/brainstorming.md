# Focused Brainstorming Knowledge

Use this reference only when the request needs a material design or exploration decision.

## Establish Context

- Inspect existing repository state, documentation, and recent changes that could constrain the decision.
- Separate independent subsystems before refining details.
- Ask one material question at a time about purpose, constraints, and success.
- Prefer a recommended multiple-choice answer when it reduces ambiguity.

## Compare Directions

- Recommend one direction and explain the decisive trade-off.
- Include at most two credible alternatives.
- Remove features that do not serve the confirmed outcome.
- Respect existing architecture and avoid unrelated refactoring.

## Present Enough Design

Scale detail to risk and complexity. Cover only the relevant architecture, boundaries, data flow, error handling, and proof strategy. Keep each component small enough to explain through its responsibility, interface, and dependency.

Confirm material choices before implementation. For a tiny change, a few sentences can be enough; for a cross-boundary change, record the design in a repository document.

## Endpoint

Stop at the requested endpoint. Brainstorming does not authorize implementation. When design is approved and implementation is requested, hand the confirmed outcome and constraints to the active build workflow.
