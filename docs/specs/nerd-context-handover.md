# Nerd Context Handover

## Purpose and authority

This is the working handover for the next agent continuing `nerd-context` on
branch `feature/nerd-context`. It summarizes the current repository state,
decisions, evidence, blockers, and the safest continuation order as of
2026-09-18.

The authoritative sources remain:

1. [Nerd Context brainstorm](nerd-context-brainstorm.md) for the product and
   experiment contract.
2. [Implementation plan](../plans/2026-08-27-nerd-context.md) for task order and
   production scope.
3. [POC evidence report](../experiments/nerd-context/results/report.md) and
   [tracked verdict](../experiments/nerd-context/results/verdict.json) for the
   current tracked evidence.
4. [Full response contract](../experiments/nerd-context/response-contract.md)
   for the later deployability findings that are not represented by the old
   four-field preflight serializer.

When this handover conflicts with a source-bound artifact, preserve the
artifact and resolve the discrepancy explicitly. Do not rewrite prior evidence
to match a newer interpretation.

## Current decision

**Production is blocked. Tasks 2–7 have not been implemented and must remain
blocked until Task 1 produces a complete fresh `verdict=pass` with
`retrieval_design=typed_lexical`.**

The tracked verdict is a deterministic preflight with
`verdict=inconclusive`, `live_status=not_run`, and
`production_unlocked=false`. The corrected full empirical protocol has not run.
Software tests and deterministic checks are useful prerequisites; they do not
unlock production.

No commit, push, tag, deployment, publication, or change to the user's installed
Nerd configuration was performed in this workstream. Obtain current authority
before doing any of those actions.

## Working-tree snapshot

The branch is intentionally dirty. Preserve all existing work and inspect the
diff before editing overlapping files.

Tracked modifications at handover:

- `README.md`
- `benchmarks/nerdbench/adapters.py`
- `docs/plans/2026-08-27-nerd-context.md`
- `docs/specs/nerd-context-brainstorm.md`
- `tests/test_benchmark_adapters.py`
- `tests/test_readme.py`

Untracked work:

- `docs/experiments/nerd-context/`
- this handover

Raw model output, SQLite files, traces, private homes, and immutable run
archives belong only under the ignored
`benchmarks/results/nerd-context/` root. Do not add them to version control.
`README.md` was also being revised outside the original Context work; preserve
its current content and the updated discoverability tests.

## Product contract that remains fixed

- One opaque runtime-generated `context_id` is the only public identity.
- An exact ID in the current activation or intentional delegated handoff resumes
  only that Context. Omission always creates a fresh Context. Unknown or lost
  IDs return `not_found`; there is no inference, search, listing, or replacement.
- Records are append-only typed facts: `goal`, `boundary`, `decision`,
  `evidence`, `open_question`, and `checkpoint`. Corrections use explicit
  supersession.
- Context is untrusted evidence. It cannot choose Smart's endpoint, grant
  authority, confirm Memory, or authorize an ordinary action.
- Nerd Memory and Nerd Context remain separate stores and workflows.
- Production capture is capped at 20 records. The POC's historical 30-record
  allowance is not production authority.
- Ordinary hydration must include the complete response schema, provenance,
  record IDs, conflicts, authority labels, and bounded size metadata. Anchored
  facts must be revalidated before use.
- No embeddings, semantic retrieval, fuzzy ID lookup, remote sync, Context
  enumeration, raw transcript storage, hidden reasoning, or MCP deletion is in
  the approved v1 scope.

## Gates that cannot be weakened

Every gate must pass independently in both the gold-record and generated-capture
phases. A gold oracle pass cannot compensate for generated capture failure.

| Gate | Required result |
| --- | --- |
| Median capture-plus-continuation token savings | at least 40% |
| Lower 95% savings bound | at least 30% |
| Quality-delta lower 95% bound | no worse than -3 percentage points |
| Active/required fact recall | at least 95% |
| Boundary and current-decision recall | 100% |
| Stale influence | at most 2%, with zero boundary or permission incidents |
| Identity and authority safety | zero wrong-ID, missing-ID reuse, enumeration, or stored-authority failures |
| Break-even | median at most 2 resumptions; p90 at most 4 |
| Retrieval latency | p95 at most 200 ms with 10,000 records in both index modes |
| Hydration budget | every pack within 2,048 UTF-8 bytes and 2,048 measured model tokens |
| Value over equal-budget summary | at least +5 quality points or at least 50% fewer stale errors |

Each short control must preserve all full-history rubric items, add at most 192
billable tokens, create exactly one fresh empty Context, make no capture, persist
zero records, and never reuse a prior ID. Across 36 controls, create/recall p95
must be at most 200 ms.

Lexical C must also materially beat mandatory-plus-recency C0 on recall, answer
quality, or stale influence with a paired 95% interval excluding zero, without
a safety regression. If C0 passes the product gates without material lexical
value, stop and redesign the simpler checkpoint capsule. If lexical misses keep
recall below 95%, return inconclusive and brainstorm before any semantic study.

## Evidence already established

### Deterministic POC

The tracked schema-v4 preflight uses the historical four-field pack
(`kind`, `value`, `source`, `source_ref`). Across 48 long cases it reports 100%
required recall, 100% mandatory recall, 1,840–1,974 bytes, and byte-identical
FTS5/normalized-scan output. The 10,000-record check observed p95 120.755 ms for
FTS5 and 159.344 ms for scan. Its source-bound evidence SHA-256 is
`e8b39f61824c7bbcf3b2c756237cbe6196e208f36d9bb68f9b75468203053cc4`.

This result is valid only for that incomplete serializer. It must not be quoted
as proof that the production response fits or recalls 95%.

### Archived 40-call diagnostic

Run `diagnostic-20260905T202235-f2237f3d` completed 40/40 calls on
`gpt-5.6-terra`, low reasoning, Codex CLI 0.153.4. The manifest SHA-256 is
`e27a0dae60b17b9ba14761b0790ce7707e8820443a160e245c20a97b1526e2f7`.

- Gold structured: 58,937 versus 101,857 full-history tokens, or 42.14%
  savings, with break-even at one resumption.
- Generated structured: 97,478 versus 101,855 tokens, or 4.30% savings, with
  break-even at four resumptions.
- Even a frozen-pipeline optimistic bound that removes pack/output cost reaches
  only 5.45% generated savings.
- The diagnostic quality prompt and exact-source rubric were mismatched. Its
  quality scores cannot be promoted to corrected live evidence.
- Dedicated live adversarial controls did not run.

This diagnostic made the original 5,631-call run economically implausible. The
corrected protocol, including C0 quality/stale controls, now totals 7,359 calls
and remains held pending a feasible preregistered mechanism.

### Deployable full response

The prospective full response counts the decoded native MCP output text,
including a 53-byte worst-case Codex 0.153.4 prefix reservation. Transport JSON
is reported separately, while all actual token charges still count. Capture
prevalidation uses the production 20-record limit and a private 256 KiB ceiling
for canonical capture-argument JSON. These are prospective contracts, not a
production implementation.

On the unchanged 48 gold cases, the full response is 1,824–1,966 reserved bytes
with FTS5/scan parity and 100% mandatory recall, but required recall falls to
**86.6071%** (minimum 71.4286%; 12/48 cases complete). Forty-five required facts
are displaced by 57 non-required selections across 36 cases. No omitted record
fits the remaining capacity, so this is not a packing arithmetic defect.

An independent recomputation found C0 macro recall 51.7857%; lexical C wins all
48 paired cases by 34.8214 points on average, but neither reaches 95%. That
recomputation is review evidence rather than a tracked selected-run verdict and
should be rerun from source before publication.

The negative source-bound archive is
`budgeted-response-20260905T221355`, manifest SHA-256
`d634edc7b28ca45695c6858b2ff9a1aa1f2d85589898b6eb2d150bde927dfc33`.
Keep it unchanged.

The main cause is a contract mismatch: ranking receives a narrow immediate
request such as “migration strategy and verified next step,” while the
continuation rubric requires every active current-scope fact, including facts
not lexically named in that query. Intentional historical archive records are
part of the gold stress corpus and cannot simply be filtered out. A secondary
generic issue is that normalization loses exact punctuated identifiers, making
siblings such as `service-1` and `service-1-archive-9` hard to distinguish.

A bounded candidate was approved for investigation only: retain whole
punctuated identifier terms alongside existing unigrams, keep BM25/novelty
parameters unchanged, test unrelated confusable scopes and genuinely requested
history, then evaluate the frozen cases once. Do not use evaluator labels,
filter archives, tune repeatedly to the fixtures, or claim this resolves the
broader query/rubric mismatch. The candidate was not implemented at handover.

### Native mechanism probes

These probes establish narrow client behavior. None clears product gates.

| Probe | Established | Limitation |
| --- | --- | --- |
| MCP activation v1 | Three real MCP tools initialized on Terra | Context was never called; negative/inconclusive |
| MCP activation v2 | GPT-5.4-mini discovered and called Context with the exact ID | Large observed overhead, incomplete billing, and a baseline Focus presentation defect |
| Prompt/Stop hook | Trusted private hooks fired and a prompt receipt reached the model | No Context allocation or lifecycle proof in the first observation |
| Empty allocation smoke | One fresh empty Context and retry mapping were committed; zero records/captures | One pair only; incorrect Smart field use and undelimited receipt in the archived run |
| Smart/Memory/Context batching | Real Context exact-ID recall worked | Memory is optional and its recall was denied under the native policy, so no valid shared-cost comparison |
| Native trace probe | Two native recalls can be bound to one scripted inference response offline | Internal trace changes metadata/timing and does not cover authenticated billing or warmup attribution |
| Response wire/capacity | Structured content is projected once on the pinned native path | No model token, quality, or full lifecycle proof |

Tracked summaries are available in the experiment `results/` directory.
Immutable raw archives and their manifests remain under the ignored result root.

### Post-Focus hydration prototype

`post_focus_hydration.py` and `test_post_focus_hydration.py` are a private,
incomplete adapter experiment. The intended narrow path hydrates only after a
completed current Smart Focus and during an independently required direct read
of the selected Discuss skill. It must positively bind the current activation,
Context ID, Focus, direct native call, path, work directory, and complete tool
result; ambiguous, stale, quoted, truncated, nested, or already-exposed cases
must abstain before database access. Context text must be visibly marked as
quoted untrusted data and the entire hook-visible wrapper must fit the response
budget.

No real-provider live proof or production integration was completed. Do not
generalize this exact-version Discuss-only prototype to all endpoints or use it
to manufacture baseline reads.

## Unresolved prerequisites

1. **Query and recall alignment.** Define one visible current request that gives
   retrieval enough legitimate scope while remaining identical across A/B/C/C0.
   Never expose rubric labels or future questions to capture or ranking.
2. **Full response retrieval.** Reach the unchanged 95% recall and 100%
   mandatory gates with production metadata and the actual wrapper counted.
3. **Equal durable storage comparator.** Summary B and structured C must receive
   equal durable storage and hydration budgets. B needs competent query-time
   selection/compression, and every capture/update/retrieval call must count.
4. **Faithful capture lifecycle.** Capture only observations produced by
   genuinely necessary initial work. Compact generated contexts may legitimately
   make lexical ranking unnecessary; preserve that outcome.
5. **Complete accounting.** Bind every inference attempt, retry, error,
   response ID, usage record, missing-usage marker, and warmup path. Do not assume
   zero-output warmups are free. Where billing remains unknown, report bounds
   rather than a point estimate.
6. **Native critical-path latency.** Measure dispatch through receipt before
   ordinary work. Python/SQLite component time alone is not the 200 ms gate.
7. **Integrated safety.** Run the exact-ID, unknown-ID, omitted-ID, ambiguous
   continuation, stored-authority, stale-boundary, and enumeration controls
   against actual proposed behavior in both phases.
8. **Fresh preregistration.** Freeze source hashes, model/client versions,
   task schedule, abort rules, scoring, evidence replay, and all wrapper/capture
   contracts before another real-provider pilot.

## Recommended continuation order

1. Reproduce the current deterministic and full-response results without
   changing source. Preserve the 86.6071% failure as the baseline.
2. Resolve the query/rubric contract. Evaluate the bounded identifier-token
   candidate once with generic regressions and both backends. If lexical recall
   remains below 95%, return to Brainstorm before considering semantics.
3. Settle equal durable storage and complete inference accounting on paper and
   in offline replay tests.
4. Finish independent review of the post-Focus adapter. Use synthetic-provider
   native A/C processes only to establish ordering and delivery; they cannot
   establish quality, billing, or economics.
5. Compose the smallest honest end-to-end generated-capture pilot. It must use
   meaningful source work, future held-out continuation tasks, the production
   response, a competent summary, actual capture costs, and all safety evidence.
6. Run a small frozen feasibility pilot. Preserve failure. Scale to the full
   7,359-call study only if that pilot can plausibly meet every unchanged gate.
7. Start plan Tasks 2–7 only after the tracked check below exits zero:

   ```sh
   python3 docs/experiments/nerd-context/bench.py check \
     --result docs/experiments/nerd-context/results/verdict.json \
     --require typed-ledger-pass
   ```

Do not continue producing isolated live probes unless each one closes a named
prerequisite and composes into the end-to-end protocol.

## Verification commands

Run the cheapest source-bound checks first:

```sh
python3 docs/experiments/nerd-context/test_experiment.py -q
python3 docs/experiments/nerd-context/test_adversarial.py -q
python3 -m unittest tests.test_benchmark_adapters -q
python3 -m unittest discover -s docs/experiments/nerd-context -p 'test_*response*.py' -v
python3 -m unittest discover -s docs/experiments/nerd-context -p 'test_*probe.py' -v
python3 -m unittest discover -s docs/experiments/nerd-context -p 'test_hook*.py' -v
python3 docs/experiments/nerd-context/budgeted_response_audit.py
```

Then validate the repository:

```sh
python3 -m compileall -q scripts skills benchmarks tests docs/experiments/nerd-context
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests -q
python3 benchmarks/run.py plan --config benchmarks/config.json
git status --short
git check-ignore benchmarks/results/nerd-context/
```

The following distinction is intentional:

```sh
# Expected to validate current source-bound preflight evidence.
python3 docs/experiments/nerd-context/bench.py check \
  --result docs/experiments/nerd-context/results/verdict.json \
  --require valid-evidence

# Expected to remain nonzero until a complete fresh empirical pass exists.
python3 docs/experiments/nerd-context/bench.py check \
  --result docs/experiments/nerd-context/results/verdict.json \
  --require typed-ledger-pass
```

At the last broad verification before this handover, the repository suite had
410 passing tests; focused counts recorded in the evidence report were 77 POC,
14 adversarial, and 23 adapter tests. Treat these as historical reference counts
and report the fresh counts from the current tree.

Handover validation on 2026-09-18 passed 77 POC tests, 14 adversarial tests,
23 adapter tests, 31 response tests, 75 probe tests, and 38 hook tests. The hook
suite emitted four Python `ResourceWarning` messages for unclosed test SQLite
connections but completed successfully; follow up if those fixtures are reused
for production code. All five linked source files resolved locally.

## Handover completion condition

The next agent should report one of three honest outcomes:

- a source-bound full empirical pass that unlocks Tasks 2–7;
- a preserved inconclusive result plus the smallest choice-changing unknown;
- a registered reject caused by the preregistered cost, quality, or safety rule.

“All software tests pass” is not equivalent to “Nerd Context passed.”
