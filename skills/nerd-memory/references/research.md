# Research and Experiment Basis

Read this reference only when changing architecture or evaluation. It records
design evidence; it adds no runtime dependency.

## Adopted Principles

- [MemPrompt](https://arxiv.org/abs/2201.06009) motivates pairing prior intent
  failures with direct corrections.
- [Agent Workflow Memory](https://arxiv.org/abs/2409.07429) motivates reusable
  declarative workflow structure rather than raw traces.
- [ExpeL](https://arxiv.org/abs/2308.10144) and
  [Reflexion](https://arxiv.org/abs/2303.11366) motivate verified episodic
  feedback while leaving current instructions authoritative.
- [Semantic Router](https://github.com/aurelio-labs/semantic-router) motivates
  thresholds and a valid abstention result.
- [LongMemEval](https://github.com/xiaowu0162/LongMemEval) and
  [MemoryAgentBench](https://arxiv.org/abs/2507.05257) motivate separate tests
  for recall, correction, abstention, and forgetting.
- [CaMeL](https://arxiv.org/abs/2503.18813) and the
  [OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)
  motivate treating retrieved memory as untrusted data and preserving action
  authority outside the store.

## Local Experimental Evidence

H8 established shared availability across agents and repositories with a
global corpus plus contextual applicability. Its result digest is
`sha256:1e317c5e3dc4001bf2be322ea0c26b02ff27b30acb2904af8df2ab18b0c5357d`.

H9 used one verified teacher and five matched memory/control pairs. Memory
achieved 5/5 exact outputs versus 0/5, averaged 63.73 seconds versus 80.39
seconds, and was faster in four of five rounds. Its result digest is
`sha256:03fdc50d5eba5dd7b1b057517bfbb9d137e1b62d930bdf2892e04bc0f074de62`.
The observable lexical proxy increased 17.78%. Actual billed model tokens were
unavailable, so the result makes no billed-token claim. These findings are
bounded to the tested task pattern and motivate further natural-task trials.

## Rejected Designs

Do not store raw transcripts, embeddings as anonymization, executable learned
skills, credentials, permissions, hidden reasoning, or external-action
authority. Do not let corpus size, similarity, or repetition establish trust.
Do not make memory the endpoint selector or sole enforcement boundary.
