# Sub-Agent Model Mapping

## Selection Rules

- Choose the least expensive current model likely to finish without rework.
  Model choice never changes Focus, skills, tools, permissions, proof, or scope.
- Keep work with the parent when it is not independently completable; a stronger
  model does not fix the boundary. Full-history `inherit` carries conversation
  overhead; prefer a fresh bounded fork with an explicit tier when selection is authorized.
- Never guess model slugs. Validate names and effort against the active runtime;
  never silently substitute or downgrade without the fallback rules below.

## Codex

Overrides require an override-capable context fork; full-history forks inherit.
Resolve these model/effort targets against the active Codex registry first.

| Task | Model | Effort | Use |
| --- | --- | --- | --- |
| Context-bound / ambiguous | Inherit; omit model and effort | Inherit | Full context needed, parent fits, or availability uncertain |
| Narrow / mechanical | `gpt-5.6-luna` | low / medium | Lookup, formatting, mechanical edits, deterministic checks; cheap failure |
| Routine implementation | `gpt-5.6-terra` | medium | Docs, tests, focused reviews/features |
| Complex / architecture | `gpt-5.6-sol` | high | Multi-file work, ambiguous diagnosis, systemic design/review |
| Critical / high risk | `gpt-5.6-sol` | xhigh / max | Security, migration, repeatedly failed complex work |

## Claude

Prefer rolling family aliases; pin full IDs only for explicitly requested
reproducibility. Accepted targets: `inherit`, `haiku`, `sonnet`, `opus`, `fable`,
or an explicitly allowed ID. Verify thinking/effort support in the active runtime.

| Task | Model | Effort | Use |
| --- | --- | --- | --- |
| Context-dependent / default | inherit or omit | Inherit | Parent fits, shared context needed, availability unverified |
| Bounded / high volume | haiku | low / medium | Search, classification, formatting, straightforward bulk work |
| Balanced engineering | sonnet | medium / high | Repository work, coding, analysis, docs, tests, focused review |
| Complex / autonomous | opus | high / xhigh | Multi-file refactors, difficult diagnosis, high correctness pressure |
| Long horizon / research | fable | Host-supported default | Deep research/quality-first work; registry-exposed and justified by ROI |

## Cursor

Inherit parent configuration or use exact active runtime IDs. These are capability
tiers, not durable pins; resolve through the picker or `GET /v1/models`.

| Task | Tier | Example targets | Use |
| --- | --- | --- | --- |
| Context-bound / default | inherit or omit | Parent selection | Preserve context; avoid stale/disallowed pins |
| Fast feedback | Efficient | GPT-5.6 Luna, Gemini Flash, active fast model | Narrow/mechanical work; cheap detectable failure |
| General | Balanced | Composer, GPT-5.6 Terra, Claude Sonnet, active standard model | Routine code, tests, docs, focused reviews |
| High reasoning | Frontier | GPT-5.6 Sol, Claude Opus, Gemini Pro, active frontier model | Complex diagnosis, refactors, architecture, high-risk review |
| Peak / autonomous | Highest available | Active workspace apex model | Long-running work with explicit proof; accuracy over cost/latency |

## Runtime Validation and Fallback

Before explicit model/effort dispatch:

1. Query the active catalog via `GET /v1/models`, runtime CLI, or environment picker.
2. Confirm support for the selected reasoning effort/thinking budget.
3. If unavailable or rate-limited: for non-critical formatting, docs, or low-risk
   tests, fall back to `inherit` and log a warning; for security, architecture,
   or multi-file refactors, fail fast and return work to the parent.
