# Nerd Eight-Model Benchmark Plan

**Goal:** Benchmark the four Nerd comparisons on four GPT targets here and four Claude targets through a reproducible handoff, then aggregate only validated evidence into README charts.

## Targets

- GPT 5.6 Sol `xhigh`: `gpt-5.6-sol`
- GPT 5.6 Terra `xhigh`: `gpt-5.6-terra`
- GPT 5.6 Luna `xhigh`: `gpt-5.6-luna`
- GPT 5.5 `xhigh`: `gpt-5.5`
- Claude Fable 5 `xhigh`: `claude-fable-5`
- Claude Opus 4.8 `xhigh`: `claude-opus-4-8`
- Claude Sonnet 5 `xhigh`: `claude-sonnet-5`
- Claude Haiku 4.5: `claude-haiku-4-5`

## Constraints

- Use five cases and three repetitions for Smart, Surgery, Execute, and Silent.
- Keep each pair's two arms sequential; independent target shards may run concurrently.
- Record target ID, exact requested model, reasoning effort, resolved provider model when available, CLI version, commits, and seed.
- Use one pinned blinded judge configuration across every target.
- Never pool targets into one accuracy or latency headline.
- Accuracy bars use the 0–100 score. Latency bars show seconds and are scaled only within one comparison; shorter is better. Silent token bars use eligible provider-reported output tokens.
- Do not publish or chart smoke, incomplete, malformed, substituted-model, or insufficient evidence.
- Use explicit result paths during parallel work; never rely on `LATEST`.

## Work

- [ ] Add target and reasoning-effort identity to configs, run specs, adapters, records, pairing, and reports.
- [ ] Pin the blinded judge model and reasoning effort.
- [ ] Add four GPT configs and four Claude configs; each plan must contain 120 measured runs.
- [ ] Add regression tests for command flags, unique run IDs, pairing identity, and result-directory isolation.
- [ ] Add a Claude handoff prompt that produces sanitized, mergeable artifacts without changing README or Git state.
- [ ] Run four GPT smoke shards and audit exits, tokens, judging, and report reproducibility.
- [ ] Run four GPT release shards concurrently, keeping arms sequential inside each shard.
- [ ] Seal GPT evidence and create a target-to-result index with hashes.
- [ ] Receive and validate the Claude index and evidence.
- [ ] Aggregate all valid target summaries and generate README charts mechanically.

## Resume Gate

Claude execution happens outside this session. Do not complete the final two steps until the user returns with the Claude index and result directories. If an exact model or effort is unavailable, record that target as blocked rather than substituting it.
