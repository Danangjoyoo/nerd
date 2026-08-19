# Research Basis

Use this reference when changing the memory architecture or evaluation. It
records verified design influences; it does not add runtime dependencies and
no source code is copied from these projects.

## Adopted Ideas

| Source | Verified mechanism | Adopt in Nerd Memory |
| --- | --- | --- |
| [OpenAI Codex skill metadata](https://developers.openai.com/codex/skills#optional-metadata) | Skills support explicit and description-matched implicit invocation; `policy.allow_implicit_invocation` defaults to true. | Keep implicit invocation enabled, but use the user-installed lifecycle hook for deterministic per-request activation because description matching alone is discretionary. |
| [OpenAI Codex hooks](https://developers.openai.com/codex/hooks) | User-level lifecycle hooks can add context on `UserPromptSubmit` and `SessionStart`, and Codex requires review and trust for non-managed command hooks. | Install one global reviewed hook that explicitly activates Memory for the current request while preserving every proposal and action gate. |
| [OpenAI Codex MCP](https://developers.openai.com/codex/mcp) | Local Codex clients share MCP configuration; stdio servers run from a configured command, and app or extension configuration changes require a restart before the new registry is active. | Treat the callable session registry as live truth, ask before registration changes, and require a restarted host instead of manually launching the server. |
| [Claude Code skill invocation controls](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill) | By default, Claude may invoke a skill automatically; `disable-model-invocation: true` blocks that path. | Keep the shared skill model-invocable and let the user-installed prompt hook provide deterministic activation. |
| [Cursor Agent Skills](https://cursor.com/docs/skills#disabling-automatic-invocation) | Cursor can discover shared Agent Skills and run `sessionStart` hooks. | Keep the skill model-invocable and let the user-installed session hook provide deterministic activation. |
| [OpenAI local memories](https://learn.chatgpt.com/docs/customization/memories?surface=app) | Background extraction and consolidation, supporting evidence, separate use/generation controls, and optional exclusion of web/MCP-tainted chats. Memory is a recall layer rather than the sole source of mandatory rules. | Keep memory opt-in, evidence-backed, delayed, and lower-authority than current instructions or checked-in guidance. Reject external-context evidence and secrets. |
| [MemGPT](https://arxiv.org/abs/2310.08560) and [Letta](https://github.com/letta-ai/letta) | Tiered working and archival memory with interrupt-driven control. | Keep the active safety contract small and read-only; search a larger local evidence store; interrupt before use. |
| [LangMem](https://github.com/langchain-ai/langmem) | Semantic, episodic, and procedural memory; active/background formation; namespaces; pure transformation separated from persistence. | Store typed observations, consolidate across tasks, namespace by user/project, and keep persistence deterministic. |
| [MemPrompt](https://arxiv.org/abs/2201.06009) | Retrieves prior misunderstood-intent cases paired with direct user correction. | Treat explicit corrections as the strongest evidence for future proposals. |
| [Ripple-Down Rules](https://doi.org/10.1017/S0269888909000241) | Refines a maintained rule base from naturally occurring misclassified cases, using the case context to add a distinguishable exception while preserving previously correct cases. | Treat denial as a cornerstone case, not an automatic correction. Draft a strict contextual child exception, keep the recorded parent visible as fallback, and activate the child only after exact user review. |
| [Agent Workflow Memory](https://arxiv.org/abs/2409.07429) and its [reference implementation](https://github.com/zorazrw/agent-workflow-memory) | Induces reusable workflows while abstracting example-specific details. | Represent action patterns declaratively with applicability, exclusions, boundaries, stop conditions, and verification. |
| [ExpeL](https://arxiv.org/abs/2308.10144) | Consolidates insights from multiple trajectories and retrieves task-similar experience. | Consolidate independent task episodes; never auto-promote the derived insight. |
| [Graphiti](https://github.com/getzep/graphiti) | Episode provenance, temporal validity, supersession, and multi-signal retrieval. | Preserve lineage and versions, suspend conflicts, and invalidate stale proposals without adding a graph database. |
| [Generative Agents](https://arxiv.org/abs/2304.03442) | Observation, reflection, and planning with relevance, recency, and importance retrieval signals. | Keep observations separate from derived patterns; make reflections inert candidates and base importance on user evidence. |
| [Reflexion](https://arxiv.org/abs/2303.11366) | Uses verbal feedback from completed trials as episodic guidance. | Record explicit feedback and verified outcomes; never treat self-reflection as user authority. |
| [Voyager](https://github.com/MineDojo/Voyager) | Retrieves skills and improves them from environment errors and verification. | Close the loop with verification evidence; reject learned executable code and autonomous curriculum. |
| [CoALA](https://arxiv.org/abs/2309.02427) | Separates working, semantic, episodic, and procedural memory, and planning from internal/external actions. | Construct one typed endpoint first, then pass it to the existing Nerd workflow only after confirmation. |
| [Semantic Router](https://github.com/aurelio-labs/semantic-router) | Named routes, exemplars, thresholds, and a valid no-match result. | Prefer exact context and trigger matches; abstain rather than force the nearest route. |
| [A2A specification](https://github.com/a2aproject/A2A/blob/main/docs/specification.md) | Agent Cards associate an agent's identity, skills, capabilities, interfaces, and authentication requirements; clients validate current capability support before use. | Remember only stable local registry aliases in one agent-bound route profile. Resolve identity, capability, and authorization live; never persist remote endpoints or credentials as preference memory. |
| [OpenAI Agents SDK tools](https://openai.github.io/openai-agents-python/tools/) and [handoffs](https://openai.github.io/openai-agents-js/guides/handoffs/) | An agent is configured with tools, agents can be exposed as tools, capabilities may be conditionally enabled, and handoffs are explicit orchestration operations. | Treat the agent plus its selected skill/tool surface as one ordered orchestration profile. A remembered handoff or agent-as-tool route remains a suggestion behind the Memory gate and ordinary host approval. |
| [MCP tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) | Tool inventories are discovered from servers, may change, and tool annotations are untrusted unless the server is trusted; human denial must remain possible. | Store normalized registry aliases rather than invocations or arguments, re-resolve the complete MCP/tool route at use time, and fail closed without silent substitution when inventory or authorization changed. |
| [LongMemEval](https://github.com/xiaowu0162/LongMemEval) | Tests extraction, multi-session reasoning, knowledge updates, temporal reasoning, and abstention across long histories. | Cover updates, context drift, conflict, and abstention in deterministic tests. |
| [MemoryAgentBench](https://arxiv.org/abs/2507.05257) | Separates accurate retrieval, test-time learning, long-range understanding, and selective forgetting. | Evaluate lifecycle operations separately rather than hiding them behind one aggregate score. |

## Security Basis

- [CaMeL](https://arxiv.org/abs/2503.18813) separates trusted control flow from
  untrusted data and uses capabilities. Treat retrieved memories as data and
  bind one capability to one exact proposal.
- SQLite's [application-defined function](https://www.sqlite.org/appfunc.html)
  registration is connection-local, while ordinary [database
  triggers](https://www.sqlite.org/lang_createtrigger.html) persist in the
  schema and can abort writes with `RAISE()`. Use that asymmetry to fence
  already-open older runtimes after an exclusive schema migration: a stale
  connection either lacks the version function or returns the wrong version.
- The [OWASP Transaction Authorization Cheat
  Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html)
  requires users to see significant transaction data, a final execution-time
  authorization check, limited validity, and unique credentials. Bind approval
  to the endpoint digest, task, pattern versions, expiry, and one use.
- [AgentPoison](https://arxiv.org/abs/2407.12784) demonstrates targeted steering
  through fewer than 0.1% poisoned records in its evaluated settings, while
  query rephrasing and perplexity filtering were inadequate. Never make
  semantic similarity, anomaly scanning, or corpus majority sufficient for
  activation. Its [NeurIPS reference
  implementation](https://github.com/AI-secure/AgentPoison) is useful as an
  adversarial fixture source, not as a runtime dependency.
- [PoisonedRAG](https://www.usenix.org/system/files/conference/usenixsecurity25/sec24winter-prepub-1468-zou.pdf)
  demonstrates high targeted success from a handful of poisoned documents in
  databases containing millions of benign documents. A large history is not a
  trust boundary. Use its [USENIX reference
  implementation](https://github.com/sleeepeer/PoisonedRAG) to inspire joint
  retrieval tests.
- [MINJA](https://arxiv.org/abs/2503.03704) demonstrates memory injection
  through ordinary progressive interactions rather than direct database
  access. Count independent task roots and require direct-user authority; do
  not let gradual repetition create activation. Its [NeurIPS reference
  implementation](https://github.com/dsh3n77/MINJA) is useful as an attack
  corpus.
- [Environment-injected memory
  poisoning](https://arxiv.org/abs/2604.02623) demonstrates cross-session,
  cross-site compromise from a contaminated observation. Reject web, tool,
  repository, attachment, quoted, assistant, and subagent content as evidence
  of user guidance.
- [Sleeper memory poisoning](https://arxiv.org/abs/2605.15338) shows that false
  user memories planted through external context can remain dormant and later
  reactivate. Preserve provenance, quarantine conflicts, and make forgetting
  cascade.
- [MemoryGraft](https://arxiv.org/abs/2512.16962) shows why a
  successful-looking prior workflow is still unsafe authority when it came
  from repository content. Keep result evidence separate from user guidance.
- [STALE](https://arxiv.org/abs/2605.06527) evaluates stale and propagated
  preferences and reports poor overall handling even when newer evidence is
  retrieved. A correction must suspend the old pattern deterministically;
  leave no last-write or model-judgment decision.
- [Vec2Text](https://aclanthology.org/2023.emnlp-main.765/) demonstrates exact
  reconstruction of many evaluated text embeddings. Treat embeddings as
  sensitive representations, not anonymization; the initial runtime avoids
  them entirely.
- The [OWASP MCP Security Cheat
  Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)
  and [RAG Security Cheat
  Sheet](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html)
  reinforce least privilege, provenance, input isolation, and authorization at
  the action boundary. Use them as system-level checks around the memory gate.
- [RFC 8785](https://www.rfc-editor.org/info/rfc8785) defines a JSON
  canonicalization scheme suitable for portable proposal digests. The initial
  standard-library implementation uses deterministic sorted compact JSON;
  migrate to full RFC 8785 compatibility before interoperating across
  runtimes.

## Explicit Rejections

- Do not copy current [Mem0](https://github.com/mem0ai/mem0) ADD-only behavior
  or give assistant-generated facts the same trust as user statements. Its
  hybrid retrieval and open benchmarks are useful; its trust choice is not.
- Do not use last-write-wins updates, raw chat transcripts, model-assigned
  confidence, or repetition within one task as proof.
- Do not store executable learned skills, permissions, credentials, hidden
  reasoning, or external-action authorization.
- Do not make a skill prompt, hook, embedding, or memory provider the sole
  enforcement boundary. Keep a deterministic persisted proposal/grant state
  machine.
- Do not assume a large benign corpus dilutes poison, or let two individually
  harmless memories bypass review when their combined endpoint is material.
- Do not treat signed provenance as trusted meaning: a signature may faithfully
  authenticate attacker-controlled or externally sourced content.

## Cross-Agent Validation Note

Codex uses `agents/openai.yaml` for implicit-invocation policy, while Claude
Code and Cursor use the shared skill metadata plus their native lifecycle hook
formats. Nerd Memory intentionally remains model-invocable on all three hosts;
the reviewed user-level hook makes activation deterministic. Package discovery,
copy-install, and hook tests must verify both the shared frontmatter and the
host-specific event wiring. A loaded skill body may remain in conversation
context after activation, so the request-scoped inert rule remains necessary.
