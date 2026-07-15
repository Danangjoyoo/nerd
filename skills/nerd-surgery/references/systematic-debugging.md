# Systematic Debugging Knowledge

## Investigate the Cause

1. Read the complete error, stack trace, paths, and status codes.
2. Reproduce the symptom consistently. When it is intermittent, collect more evidence rather than guessing.
3. Inspect recent code, configuration, dependency, and environment changes.
4. At each component boundary, record what enters, what leaves, and which configuration is active.
5. Trace a bad value or state backward through callers until its source is found.

## Compare Patterns

- Find the nearest working implementation in the same repository.
- Read the relevant reference completely.
- List every meaningful difference between working and failing paths.
- Identify hidden dependencies and environmental assumptions.

## Test One Hypothesis

State one active hypothesis and the evidence supporting it. Change one variable with the smallest discriminating experiment. If the experiment rejects the hypothesis, return to evidence and form a new one; do not stack fixes.

## Correct the Source

At an authorized repair endpoint, reproduce the failure in an automated test, correct the root cause once, and run the same proof plus relevant regression checks.

After two failed correction attempts, stop. Reassess evidence and whether the architecture or boundary is wrong before making another change.

When no local cause can be confirmed, distinguish environmental or external behavior from incomplete investigation. Document what was ruled out and add only handling justified by evidence.
