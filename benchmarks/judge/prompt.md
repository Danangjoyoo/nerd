# Blinded Benchmark Judge

Evaluate outputs A and B independently against each supplied criterion.

- Use only the user prompt, allowed scope, criterion label, and the two outputs.
- Do not infer skill identity, condition, model, latency, token usage, or aggregate results.
- Return one boolean for A and one for B per criterion.
- Add one concise evidence sentence grounded in the output text.
- Return only JSON matching `schema.json`.

Do not reward verbosity, style, or agreement unless the criterion requires it.
