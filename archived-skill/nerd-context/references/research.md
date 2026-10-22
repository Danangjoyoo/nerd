# Research Basis

Nerd Context builds on public deterministic-retrieval research and prior
Nerd experiments; it introduces no third-party runtime dependency.

## Design influences

- **BM25 ranking.** The Context-local scorer follows the standard BM25
  formulation with `k1=1.2`, `b=0.75`, and positive IDF derived only from
  active records in the exact Context. Binary term presence prevents
  duplicate-value inflation.
- **SQLite FTS5.** The default index mode uses the `ascii` tokenizer with
  `tokenchars '-_'` so whole punctuated identifiers survive
  tokenization. The `normalized_scan` fallback ports the identical
  scorer for FTS-unavailable hosts.
- **Append-only typed ledger.** Records are one of six kinds
  (`goal`, `boundary`, `decision`, `evidence`, `open_question`,
  `checkpoint`). Corrections use explicit `supersedes_id`, preserving
  audit trail without in-place edits.
- **Mandatory-plus-recency baseline (C0).** The plan's C0 arm captures the
  minimum viable pack from the same persisted ledger without lexical
  ranking; lexical value must beat C0 on at least one preregistered
  metric with a paired 95% interval excluding zero.
- **Bounded pack economy.** The `2,048` UTF-8 byte and 2,048 measured
  model-token ceilings mirror the deployable POC's tested capacity.

## Evaluation evidence (as of 2026-09-18)

- The deterministic POC preflight passes `valid-evidence` and records
  100% required recall with the historical four-field pack.
- The bounded lexical (identifier-token) candidate reaches 100% required
  recall on the 48 gold fixtures with mode parity and 100% mandatory
  recall.
- The corrected full 7,359-call live experiment (token savings, quality
  delta, adversarial, break-even, latency, generated capture) remains
  **unrun**. `typed-ledger-pass` still exits nonzero. Production is
  **not** unlocked.

## Explicitly out of scope for v1

- Embeddings, semantic retrieval, and nearest-ID fallback.
- Fuzzy or partial-ID lookup, Context enumeration, or listing.
- Remote sync, third-party persistence, or a shared datastore.
- Raw transcript storage or hidden reasoning capture.
- MCP-exposed deletion (destructive `forget` is CLI-only).

Any change to the retrieval design, byte ceiling, capture cap, response
envelope, tokenization, or authority label invalidates prior evidence and
requires fresh preregistration.
