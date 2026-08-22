# Sub-Agent Model Mapping Framework

This framework governs model selection and execution parameters for delegated sub-agents. 

### Fundamental Delegation Rules

1. **Least-Cost Execution:** Choose the least expensive current model that can complete the task without likely rework.
2. **Invariance:** A model choice **never** changes the task's Focus Record, skills, tools, permissions, proof requirements, or mutation boundary.
3. **No Over-Compensating:** When a task is not independently completable, keep it with the parent agent rather than compensating with a stronger sub-agent model.
4. **Context Overhead Awareness:** A full-history `inherit` carries the parent conversation's prompt token overhead. For bounded sub-tasks, prefer a fresh context fork with an explicit tier over an unnecessary `inherit`.
5. **No Hallucinated Slugs:** Never write a guessed model slug into a task plan. Model names and effort levels must be validated against the runtime registry prior to delegation. Do not silently degrade or substitute models without explicit fallback rules.

---

# Codex

A model override requires a context fork that permits overrides; full-history forks inherit the parent configuration. Resolve model and effort names against the active Codex registry before delegation.

| Task Signal / Scope | Model | Reasoning Effort | Recommended Use Case |
| :--- | :--- | :--- | :--- |
| **Context-bound / Ambiguous state** | Inherit (omit `model` & `reasoning_effort`) | Inherit | Parent fits, full conversation is required, or sub-agent model availability is uncertain. |
| **Narrow / Mechanical** | `gpt-5.6-luna` | `low` or `medium` | Lookup, formatting, mechanical edits, or deterministic checks. Small scope, explicit acceptance, cheap failure. |
| **Routine Implementation** | `gpt-5.6-terra` | `medium` | Balanced default for normal delegated repository work: documentation, unit tests, code review, or focused features. |
| **Complex / Architecture** | `gpt-5.6-sol` | `high` | Multi-file implementation, ambiguous diagnosis, systemic architecture, or difficult code reviews requiring synthesis. |
| **Critical / High-Risk** | `gpt-5.6-sol` | `xhigh` or `max` | Security-critical, migration-critical, or repeatedly failed complex work. Quality and precision outweigh cost and latency. |

*Note: Verify that the target model variant supports extended reasoning effort parameters before dispatching.*

---

# Claude

Prefer family aliases for rolling capability tiers. Specify a full model ID only when exact execution reproducibility is an explicit requirement. Claude Code accepts `inherit`, `haiku`, `sonnet`, `opus`, `fable`, or an explicit allowed model ID.

| Task Signal / Scope | Model | Extended Thinking / Effort | Recommended Use Case |
| :--- | :--- | :--- | :--- |
| **Context-dependent / Default** | `inherit` (or omit `model`) | Inherit | Parent model fits, task requires shared context, or sub-agent status is unverified. Safest default. |
| **Bounded / High-Volume** | `haiku` | `low` or `medium` | Bounded search, classification, formatting, and high-volume straightforward tasks where speed matters. |
| **Balanced Engineering** | `sonnet` | `medium` or `high` | General delegated repository tasks: routine coding, data analysis, docs, unit tests, and focused reviews. |
| **Complex / Autonomous** | `opus` | `high` or `xhigh` | Complex agentic coding, multi-file refactoring, difficult diagnosis, or high correctness pressure. |
| **Long-Horizon / Research** | `fable` | Host-supported default | Deep research or quality-first tasks. Use only when exposed by the active registry and justified by ROI. |

*Note: Verify that the selected model supports the requested thinking/effort parameter in the active runtime environment.*

---

# Cursor

Cursor sub-agents can inherit parent models or accept exact runtime model IDs. Treat model names in this section as capability tiers rather than durable hardcoded strings—resolve allowed IDs via the current environment picker or `GET /v1/models`.

| Task Signal / Scope | Model Tier | Example Registry Targets | Recommended Use Case |
| :--- | :--- | :--- | :--- |
| **Context-bound / Default** | `inherit` (or omit `model`) | Parent Selection | Avoids stale/disallowed pins; preserves parent context and behavior. |
| **Fast / Fast-Feedback** | Fast / Efficient | GPT-5.6 Luna, Gemini Flash, or active fast model | Narrow lookup, mechanical edit, formatting, or deterministic check. Failure is cheap to detect. |
| **Balanced / General** | Balanced | Composer, GPT-5.6 Terra, Claude Sonnet, or active standard model | Routine implementation, tests, documentation, or focused review requiring reliable tool use. |
| **Frontier / High-Reasoning**| Frontier | GPT-5.6 Sol, Claude Opus, Gemini Pro, or active frontier model | Complex diagnosis, multi-file refactoring, systemic architecture, or high-risk review. |
| **Peak / Autonomous** | Highest Available | Active apex model exposed by workspace | Long-running, maximum-capability work with explicit proof criteria. Accuracy outweighs usage and latency. |

---

# Runtime Resolution & Fallback Protocol

When invoking a sub-agent with explicit model or effort parameters, executors must execute the following validation chain:

1. **Registry Check:** Query the active model catalog (`GET /v1/models`, runtime CLI, or local environment picker).
2. **Capability Validation:** Confirm the selected model supports the requested reasoning effort or thinking budget parameters.
3. **Fallback Handling:**
   - **Non-Critical Tasks (Format, Docs, Low-risk Tests):** If the specified model or effort tier is unavailable or rate-limited, fall back to `inherit` and log a warning.
   - **Critical Tasks (Security, Architecture, Multi-file Refactor):** If the requested model/effort tier is unavailable, **fail fast** and return execution to the parent agent rather than running high-risk work on an unverified or downgraded model.