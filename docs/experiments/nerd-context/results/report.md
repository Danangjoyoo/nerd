# Nerd Context POC evidence

The current deterministic retrieval prerequisite passes. Production remains
blocked: no complete, valid live experiment has passed both phases, short
controls, and adversarial safety. The tracked `verdict.json` is a current-source
**preflight**, with `verdict=inconclusive` and `retrieval_design=unselected`.

## Current retrieval and protocol

All 48 long cases retain 100% of required facts and 100% of mandatory boundaries
and decisions. Packs use 1,840–1,974 UTF-8 bytes under the unchanged 2,048-byte
ceiling. FTS5 and normalized scan produce byte-identical packs. The ranker uses
binary-term BM25 with fixed `k1=1.2`, `b=0.75`, then discounts optional relevance
by maximum Jaccard similarity to already packed optional records. Generic
specificity, rarity, and duplicate-crowding regressions established these changes.
The historical 64.2857% recall failure is no longer the current result.

Current preflight evidence SHA-256:
`e8b39f61824c7bbcf3b2c756237cbe6196e208f36d9bb68f9b75468203053cc4`.

Independent 10,000-record checks after the ranker froze observed p95 retrieval
of 120.755 ms for FTS5 and 159.344 ms for normalized scan, with byte-identical
1,961-byte packs. These are local performance observations, not a full live
experiment verdict.

The current shared protocol explicitly requests every active fact in the
current scope and complete observation text, with generic kind definitions.
Both capture arms and all long continuations receive this same reconstruction
contract. Free-form summaries supply each embedded source observation and its
original reference separately; the summary wrapper is not treated as one fact.
Scoring remains strict exact-source reconstruction; truthful paraphrases can
receive zero credit. The corrected protocol has not run live.

The schema-v4 harness now includes the originally required answer-quality and
stale-influence ablation alternatives alongside retrieval recall. Each actual
ledger also supplies a mandatory-plus-recency pack (C0), measured in full and
used in four fresh continuations paired with the existing lexical C calls.
All three mean improvements receive separate case-clustered paired 95%
intervals; at least one must be wholly above zero, with complete paired evidence
and unchanged safety, parity, and latency gates. Missing C0 calls cannot establish
materiality. Its 1,728 extra measurement/continuation calls increase the complete
workload to 7,359 calls, fully reported in experiment spend and excluded from
primary A/B/C lifecycle economics. No C0 live observations are available yet.

## Archived 40-call diagnostic

- Run: `diagnostic-20260905T202235-f2237f3d`
- Manifest SHA-256: `e27a0dae60b17b9ba14761b0790ce7707e8820443a160e245c20a97b1526e2f7`
- Model: `gpt-5.6-terra`, reasoning effort `low`, `codex-cli 0.153.4`
- Workload: `resumption-01` once per phase, four fresh resumptions each, and one short control.
- Completed calls: 40/40, all exit 0; wall time 115.53 seconds.
- Call latency: median 5.627 seconds; p95 7.395 seconds.
- Total billable tokens including measurement calls: 698,783.

The ignored local evidence root is
`benchmarks/results/nerd-context/diagnostic-20260905T202235-f2237f3d/`.
Its raw calls, observations, aggregate summary, and original manifest remain
unchanged. `source-snapshot/` preserves the nine measured source files, each
verified against the original manifest fingerprint. `diagnostic-selection.json`
identifies this pilot; it is not a production selection.

| Recorded measure | Gold-record diagnostic | Generated-capture diagnostic |
| --- | ---: | ---: |
| Full-history total billable tokens | 101,857 | 101,855 |
| Summary total, including capture | 97,839 | 97,946 |
| Structured total, including capture | 58,937 | 97,478 |
| Structured capture billable tokens | 0 | 40,236 |
| Structured four-continuation tokens | 58,937 | 57,242 |
| Structured savings versus full history | 42.14% | 4.30% |
| Observed cumulative break-even | 1 resumption | 4 resumptions |
| Actual structured pack bytes / measured tokens | 1,899 / 446 | 311 / 77 |
| Recorded required-fact pack recall | 100% | 0% |
| Recorded mandatory pack recall | 100% | 0% |
| Recorded lexical recall improvement | +42.86 points | 0 points |
| Recorded exact-source score: full / summary / structured | 25% / 0% / 33.33% | 25% / 0% / 0% |

The generated capture's recorded fidelity precision and required-fact recall
were both zero under the original strict full-sentence/type scorer. This is an
**ambiguous-task diagnostic**, not evidence of complete semantic information
loss: the request asked for two specific facts while the rubric expected seven,
and instructions allowed exact answer phrases while the scorer required whole
observation sentences. The captured source-linked phrases retained the migration
choice and corrected next step; one next-step observation also had a different
record kind. The current symmetric protocol repairs that mismatch without
changing corpus labels, expected values, scoring thresholds, or prior evidence.
No corrected-quality result is inferred from this pilot.

The short control preserved its answer, added 49 billable tokens, created one
fresh empty Context, made no capture, and took 1.20 ms for creation/recall.
There were no observed ordinary action or stale incidents. Dedicated model-facing
adversarial controls did not run in this diagnostic, so those observations do
not certify safety. One case and one repetition cannot supply phase confidence
intervals or a complete phase pass/reject verdict.

## Conditional cost bound and stopping decision

The generated diagnostic spent 39,795 input tokens in its two capture calls.
Its four continuation inputs were 14,209, 14,188, 14,209, and 14,216 tokens.
Removing the measured 77-token pack from each and assigning zero cost to every
capture and continuation output gives the optimistic frozen-pipeline cost:

`39,795 + (14,209 + 14,188 + 14,209 + 14,216) - 4 × 77 = 96,309 tokens`.

Compared with the observed full-history total of 101,855 tokens, even that
counterfactual saves only **5.45%**, with the earliest cumulative crossing still
at resumption 4. This conditional calculation retains the measured input shells;
it is not a guarantee about another model, client, prompt, or architecture.

More generally, with shell cost `S`, source-history cost `H`, two capture calls
that consume the history once in total, four resumptions, and zero pack/output
cost, costs are `A = 4(S + H)` and `C = 6S + H`. Reaching 40% savings requires
`H ≥ 18S / 7`; break-even by two resumptions requires `H ≥ 2S`. At the observed
roughly 14,000-token shell, those conditions require about 36,000 and 28,000
history tokens respectively. Fixed client overhead is charged to every arm;
it is not subtracted from the economics to manufacture a pass.

The original 5,631-call complete run was therefore held. Its 7,359-call extension
remains held for the same primary-economics constraint. No live run or production
implementation follows without a newly preregistered, faithful, feasible design.
A generated capture containing only the few required facts may fit entirely in
2,048 bytes, giving recency the same recall as lexical ranking. Equal recall
does not resolve the independent answer-quality or stale-influence alternatives;
those require actual paired continuations. The experiment must not force
irrelevant captures to create an ablation improvement.

## Verification

- `python3 docs/experiments/nerd-context/test_experiment.py -q`: 77 tests pass.
- `python3 docs/experiments/nerd-context/test_adversarial.py -q`: 14 tests pass.
- `python3 -m unittest tests.test_benchmark_adapters -q`: 23 tests pass.
- Prior repository verification: `python3 -m unittest discover -s tests -q`, all 410 tests passed before this isolated ablation extension.
- `bench.py preflight --output .../verdict.json`: exit 0; current retrieval prerequisite passes.
- `bench.py check --result .../verdict.json --require valid-evidence`: verifies the current-source preflight.
- `bench.py check --result .../verdict.json --require typed-ledger-pass`: remains blocked by absent complete live evidence.

README.md was preserved. Its tests now verify public skill discovery through
the linked skills directory and retain archived UFast factual assertions against
the historical result artifact, without requiring obsolete homepage placement.
Public skill registry, installer, runtime, and research gates remain unchanged.
