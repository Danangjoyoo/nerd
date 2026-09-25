# Native Smart/Memory 2.0 and Context batching diagnostic

Status: implemented offline; no live execution authorized or observed for this protocol.

Run `python3 docs/experiments/nerd-context/batching_probe.py plan` to obtain the
source digest for independent review. The proposed smoke schedule is exactly two
fresh GPT-5.4-mini / low Codex processes: exact-ID resume baseline, then Context.
The runner requires that reviewed digest, never retries, and stops the schedule
on provider rejection, cancellation, or failed native hook registration.

Both arms receive identical private copies of every repository skill and its
dependencies, the unchanged Smart prompt hook, the unchanged Memory 2.0 MCP
server, and the separate three-tool Context MCP server. The private installation
uses the supported trusted-project configuration and existing authentication;
it changes no user installation. Native startup, skill reads, discovery, tool
schemas, replies, receipts, and any actual Memory recording remain observable
and charged. The baseline receives the same source observations inline and has
Context disabled. Treatment receives only the exact current ID and must obtain
the observations through native Context recall.

The explicit experimental ordering is current Focus → independent native reads
→ validate/apply Memory advice → validate/use Context facts → answer. This
revises sequential retrieval. Smart retains its actual Intention, Expectation,
Scope, and Role fields, with Discuss as the endpoint and a distinct role. Memory
cannot supply Context's selector, query, fixed 2,048-byte budget, or authority.
There is no combined wrapper, direct model database access, hidden pack injection,
or forced baseline call beyond the installed workflow. Actual skill consumption
must appear in native output or the private rollout to support workflow validity.

Both private Memory databases begin empty. This tests genuine fresh-install
abstention only. Existing exact-resume observations are seeded identically before
the measured process; that setup is not generated capture or lifecycle economics.
Creation, unknown-ID isolation, argument independence, malformed/unsafe attempts,
timeouts, and raw-evidence tampering have offline tests. Those tests do not prove
model resistance to malicious advice. Additional live guard cases require a new
reviewed schedule and authorization.

Evidence includes raw native events, Context's separate JSON-RPC journal, real
Memory recall audit rows, before/after private database contents, source/config
hashes and snapshots, skill-read evidence, stdout/stderr, rollouts, and supported
OTel logs/traces. Failed behavior remains valid negative evidence. A manifest
binds the complete artifact set; aggregate scores replay from raw observations.
Raw traces and private state stay under ignored benchmark results.

Native registration and exposed skill text do not by themselves prove hook
execution. Exact injected hook instructions in the private native rollout are
reported separately when present; otherwise hook execution remains unknown.
The launcher and verifier bind the complete command, detected client version,
tool configuration, private installation, and collector endpoint.

The probe reports native call interval overlap separately. It does not claim
that overlap, one CLI process, or a shared trace parent proves one model response.
The current native event schema does not establish that binding. CLI usage and
rollout token updates remain observations, not proof of full billable usage.
Supported OTel traces retain `websocket.warmup` and hashed correlation identifiers
where emitted. There is no network proxy or undocumented warmup switch.

The existing original experiment, native activation, hook, and allocation
archives are unchanged. This two-process diagnostic cannot clear any original
quality, safety, token, latency, lexical-materiality, or production gate.

Offline proof: `python3 docs/experiments/nerd-context/test_batching_probe.py -v`.
