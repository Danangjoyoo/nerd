# Iteration Control: Research

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Iteration Control router](index.md) and load it only for its named trigger.

## Research Basis

- [Receding Horizon Task and Motion Planning](https://arxiv.org/abs/2009.03139): plan over a future action window, execute only the first action, re-observe, and add newly discovered infeasibility predicates before replanning.
- [D* Lite](https://aaai.org/papers/00476-aaai02-072-d-lite/): incremental replanning reuses valid prior search effort instead of restarting similar planning problems.
- [HTN planning complexity and expressivity](https://aaai.org/papers/01123-aaai94-173-htn-planning-complexity-and-expressivity/): compound and primitive task decomposition, process constraints, and the need to bound recursive task networks.
- [A systematic approach to partial-order planning](https://cdn.aaai.org/AAAI/1991/AAAI91-099.pdf): causal support, open prerequisites, and threat resolution without unnecessary total ordering.
- [Planning landmarks](https://doi.org/10.1613/JAIR.1492): partially ordered facts that every valid solution must achieve provide global scaffolding without prescribing every low-level action.
- [The options framework](https://doi.org/10.1016/S0004-3702(99)00052-1): temporally extended actions defined by initiation conditions, a bounded policy, and termination conditions.
- [Principles of intention reconsideration](https://doi.org/10.1145/375735.376326): commitment to a plan should be reconsidered dynamically when the environment changes, rather than fixed only at design time.
- [Anytime Dynamic A*](https://auld.aaai.org/Papers/ICAPS/2005/ICAPS05-027.pdf) and [ARA*](https://papers.nips.cc/paper/2382-ara-anytime-a-with-provable-bounds-on-sub-optimality.pdf): retain a usable incumbent, improve it as budget permits, and reuse prior planning work.
- [Kubernetes controllers](https://kubernetes.io/docs/concepts/architecture/controller/): continuously reconcile observed state with desired state instead of trusting an open-loop script.
- [Airflow tasks and scheduler](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html): make dependencies explicit and schedule task instances only when their upstream conditions are satisfied.
- [LangGraph Pregel runtime](https://docs.langchain.com/oss/python/langgraph/pregel): each super-step plans eligible actors, executes selected work, publishes updates, and repeats.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence): checkpoint state, pending next tasks, lineage, interrupts, parallel writes, and recovery at step boundaries.
- [LangGraph subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs): give subgraphs isolated checkpoint namespaces and choose per-invocation, per-thread, or stateless persistence deliberately.
- [OpenHands conversation persistence](https://docs.openhands.dev/sdk/guides/convo-persistence): separate auto-saved base state from incrementally appended event history and restore by unique conversation ID.
- [OpenHands task tracker](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-tools/openhands/tools/task_tracker/definition.py): maintain visible task states and a single in-progress focus, while noting that prompt-only invariants still need runtime enforcement.
- [AutoGen Magentic-One orchestrator](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py): combine an outer facts-and-plan loop with an inner progress ledger and replan after repeated stalls.
- [SWE-agent trajectories](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/trajectories.md): persist action-observation trajectories and model-visible history separately so audit history survives context processing.
- [OpenAI Agents SDK RunState](https://openai.github.io/openai-agents-python/ref/run_state/): serialize the active agent, generated items, approvals, interruptions, usage, and current step for durable pause and resume.
- [ReAct](https://arxiv.org/abs/2210.03629): interleave reasoning, action, and environment observations so plans can be tracked and updated through execution.
- [Voyager](https://arxiv.org/abs/2305.16291): automatic curriculum, reusable skill memory, and iterative refinement from execution feedback and self-verification.
- [Reflexion](https://arxiv.org/abs/2303.11366): retain bounded evaluator-grounded episodic lessons across trials rather than rediscovering the same failure.
- [MemGPT](https://arxiv.org/abs/2310.08560): use explicit memory tiers and control flow instead of assuming the full long-horizon history remains in the active context window.
- [Temporal workflow history architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md): reconstruct workflow state from an ordered event history while using snapshots and fenced ownership for efficient durable execution.
- [Temporal Workflow ID policies](https://api-docs.temporal.io/): distinguish stable workflow identity from physical executions and prohibit two active executions with the same logical ID.
- [Microsoft event-sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing): immutable event history, derived projections, replay, audit, optimistic concurrency, and the complexity cost of the pattern.
- [SQLite isolation and WAL](https://www.sqlite.org/isolation.html): transactional local persistence with serialized writers; do not treat WAL as unrestricted multi-writer or network-filesystem coordination.
- [RFC 9562 UUIDs](https://www.rfc-editor.org/info/rfc9562/): UUIDv7 supplies standardized time-ordered identifiers with random bits for distributed uniqueness.
- [Lamport on event ordering](https://www.microsoft.com/en-us/research/publication/time-clocks-ordering-events-distributed-system/): concurrent events form a causal partial order; wall-clock timestamps alone do not establish happens-before.
- [The Chubby lock service](https://research.google.com/archive/chubby.html): coarse-grained distributed ownership requires reliable lock and lease semantics.
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/): distinguish persistent application state from disposable runtime coordination.
- [Python tempfile](https://docs.python.org/3/library/tempfile.html): create ephemeral directories with secure unique-name primitives when durability is not required.

Treat these as transferable mechanisms, not a requirement to build a full workflow platform for every task. Choose the lightest implementation that still preserves the task's authority, recovery, concurrency, evidence, and forgetting risks.
