# Nerd Memory Global Behavioral Runtime Implementation Plan

**Goal:** Replace the unused Nerd Memory runtime with one clean user-local
global corpus that automatically learns verified command-to-action, tools,
steps, skills, and invalid-output behavior and recalls it across agents and
repositories without weakening current-request authority.

**Approach:** Delete the legacy proposal/pattern lifecycle and implement the
frozen M3 behavioral design proven by iterations 001–006: sanitized verified
episodes, contextual deterministic recall, explicit abstention, negative output
guards, correction retirement, source provenance, and current-input override.
Start a new schema family and default database; do not import, migrate, read,
or maintain compatibility with the unused old database.

**Scope:** Includes a from-scratch standard-library SQLite runtime, Python API,
JSON CLI, MCP server, automatic Smart/Execute integration, user hook, skill
references, installer expectations, deletion of obsolete lifecycle code/tests,
and deterministic proof. Repository identity is context/provenance only, not a
storage or retrieval partition. Excludes remote/cross-device storage,
embeddings, raw transcripts/output/tool arguments, executable memory,
credentials, permissions, action authority, installed user data deletion,
MCP registration/restart, deployment, and claims about billed model-token cost.

**Proof:** Red/green schema, capture, learning, abstention, invalid-output,
correction, cross-agent, concurrency, CLI/MCP, hook, and security tests; skill
validation; full repository regression; exact active-schema inspection; and
diff hygiene.

**Spec:** `docs/experiments/nerd-memory-rearchitecture/architecture.md`,
`docs/experiments/nerd-memory-rearchitecture/hypotheses.md`, and
`docs/experiments/nerd-memory-rearchitecture/reports/iteration-006.md`

**Sub-Agent Driven**: YES; each implementation task uses an inherited-model
sub-agent and an independent inherited-model review before acceptance.

## File Map

| Path | Action | Responsibility |
| --- | --- | --- |
| `skills/nerd-memory/scripts/memory.py` | Replace | New global episode store, M3 advisor, correction/forget lifecycle, JSON CLI |
| `skills/nerd-memory/scripts/mcp_server.py` | Replace | Three-tool global MCP adapter |
| `skills/nerd-memory/SKILL.md` | Replace | Automatic advisory-memory workflow and authority boundary |
| `skills/nerd-memory/agents/openai.yaml` | Modify | Host-facing global behavioral-memory prompt |
| `skills/nerd-memory/references/memory-contract.md` | Replace | New schema, episode, advice, security, and evaluation contract |
| `skills/nerd-memory/references/recall-and-apply.md` | Replace | Single-call recall, override, and abstention rules |
| `skills/nerd-memory/references/learn-and-correct.md` | Replace | Automatic verified capture and corrections |
| `skills/nerd-memory/references/recognize-and-reuse.md` | Replace | Capture radar and privacy minimization |
| `skills/nerd-memory/references/transport-preflight.md` | Replace | Low-overhead three-tool transport behavior |
| `skills/nerd-memory/references/research.md` | Modify | Adopt H8/H9 evidence and contextual global corpus |
| `skills/nerd-memory/references/deny-split-forget.md` | Delete | Remove obsolete proposal denial/split lifecycle |
| `skills/nerd-memory/references/correct-and-forget.md` | Create | Correction and explicit deletion workflow |
| `skills/nerd-smart/SKILL.md` | Modify | Apply separate advice after memory-blind Focus resolution |
| `skills/nerd-smart/scripts/prompt_hook.py` | Modify | Activate one global corpus per authenticated request |
| `skills/nerd-explore/SKILL.md` | Modify | Remove the deleted reusable-fact lane contract |
| `skills/nerd-execute/SKILL.md` | Modify | Record one minimal episode after current proof |
| `scripts/install_mcp.py` | Modify | Install and health-check the three-tool server |
| `scripts/validate_skills.py` | Modify | Replace the obsolete reference-file requirement |
| `tests/test_memory_engine.py` | Replace | Store, learner, correction, forget, CLI, and persistence proof |
| `tests/test_memory_security.py` | Replace | Data minimization, authority, concurrency, and clean-break proof |
| `tests/test_memory_mcp.py` | Replace | Three-tool MCP/CLI parity and restart proof |
| `tests/test_memory_denial.py` | Delete | Remove obsolete proposal denial/split tests |
| `tests/test_memory_reuse.py` | Delete | Remove obsolete endpoint-pattern and reusable-fact tests |
| `tests/test_skill_contracts.py` | Modify | New written behavioral-memory contract proof |
| `tests/test_skill_structure.py` | Modify | New reference-file inventory |
| `tests/test_install.py` | Modify | Hook text and three-tool installation proof |

## Tasks

### Task 1: Replace the legacy engine with the global behavior store

**Focus Record**

- **Intention:** Deliver a small deterministic runtime whose only durable
  knowledge is verified behavioral episodes and their correction/deletion
  history.
- **Expectation:** Execute
- **Scope:** Replace `memory.py`; replace core/security tests; delete obsolete
  denial/reuse tests. Do not change MCP or skill prose yet.
- **Role:** Behavioral-memory runtime engineer
- **Skills:**
  - `nerd-execute`
  - `nerd-review`
- **Review Required:** YES
- **Sub-agent Model:** inherit

**Outcome:** A fresh database records sanitized behavior, returns M3 advice
globally with current-input override and audited provenance, corrects/forgets
records safely, and refuses any old store without mutating it.

**Files:** `skills/nerd-memory/scripts/memory.py`,
`tests/test_memory_engine.py`, `tests/test_memory_security.py`,
`tests/test_memory_denial.py`, `tests/test_memory_reuse.py`

1. Replace the engine/security tests first with failing cases for the new public
   API and delete the two obsolete test modules. Require:
   - default path `${NERD_MEMORY_DB}` when explicitly set, otherwise
     `${CODEX_HOME}/nerd-memory/behavior.sqlite3`, otherwise
     `~/.codex/nerd-memory/behavior.sqlite3`;
   - schema family `global-behavior-memory`, version `1`, with only
     `metadata`, `behavior_episodes`, `recall_events`,
     `forget_previews`, and `trusted_event_tombstones`;
   - no storage/retrieval partition selector or related column in the fresh
     schema or Python/CLI API;
   - a non-empty database from another schema family fails closed without DDL,
     data, or version mutation;
   - private file/directory permissions, WAL concurrency, busy timeout,
     canonical JSON, close/reopen persistence, and stale-handle fencing.
2. Add behavior fixtures covering every persisted field:
   `episode_id`, monotonic order, repository provenance, `language`, `surface`,
   `project_kind`, sanitized command cues, action, tools, ordered steps, skills,
   output signals/validity/severity, verifier, feedback, optional corrected
   resources, source agent, evidence reference, and timestamps. Assert raw input
   text is never stored or hashed as a recoverable payload.
3. Run:

   ```bash
   rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_memory_engine tests.test_memory_security -v
   ```

   Expect failures because the legacy runtime exposes the wrong schema, API,
   lifecycle, and default database.
4. Replace `memory.py` rather than editing the old state machine. Implement one
   `BehaviorMemoryStore` and these operations:
   - `record(...)` validates and stores one root episode idempotently;
   - `recall(...)` returns advice and writes one bounded audit event;
   - `inspect(...)` returns schema/counts and bounded sanitized episode/audit
     summaries;
   - `preview_forget(...)` returns the exact episode set, digest, and phrase;
   - `forget(...)` accepts a fresh direct-user event and exact current phrase,
     deletes the bound episodes/audits atomically, and preserves event replay
     tombstones.
5. Apply admission and privacy rules before persistence:
   - a passed `verified_execution` with no correction may be positive workflow
     evidence but never user preference or authority;
   - a verified failed output contributes negative guard evidence only;
   - a direct `user_correction` may supply corrected tools/steps/skills;
   - unverified external, quoted, assistant-only, or subagent-only material,
     plus sensitive, credential, permission, executable, raw output,
     tool-argument, or hidden-reasoning content, is rejected or omitted;
   - repeated messages/retries under one root episode count once.
6. Implement the frozen M3 advisor exactly:
   - normalize sanitized command cues;
   - match cue plus exact `language`/`surface`/`project_kind`, excluding
     repository from the compatibility key;
   - choose action and action-resource majorities deterministically;
   - abstain on no match, equal top actions, or action confidence `<0.60`;
   - reject output when compatible invalid-signal share is `>=0.50`;
   - use verified corrected resources and retire obsolete resources after three
     compatible corrections;
   - return action, tools, steps, adjacent step edges, skills, rejection,
     confidence, abstention, `origin=behavioral_memory_advice`, and exact source
     episode IDs.
7. Accept a current baseline containing only `action`, `tools`, `steps`, and
   `skills`. Return raw suggestion plus resolved advice; preserve each non-empty
   current field exactly and list it in `overridden_fields`. Advice never grants
   permission, expands the task, supplies executable arguments, or bypasses
   ordinary tool/action checks.
8. Add the JSON CLI commands `record`, `recall`, `inspect`, `preview-forget`,
   and `forget`. Use complete JSON arguments, structured stderr errors, and no
   compatibility aliases or deprecated flags.
9. Run the focused tests; expect all to pass. Have the review agent inspect the
   new file against the experiment episode contract, M3 thresholds, current
   override, privacy, deletion atomicity, replay defense, WAL behavior, and the
   absence of old lifecycle machinery. Resolve every severity-1/2 finding.

**Proof:**
`rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_memory_engine tests.test_memory_security -v`
→ all fresh-schema, behavior, security, concurrency, correction, forget, and
CLI tests pass.

### Task 2: Replace the MCP and installation contract

**Focus Record**

- **Intention:** Expose the clean runtime through the smallest complete host
  transport, shared by all agents without multi-call proposal overhead.
- **Expectation:** Execute
- **Scope:** Replace MCP adapter/tests and update installer health checks; do
  not change host prompt or skill prose yet.
- **Role:** MCP integration engineer
- **Skills:**
  - `nerd-execute`
  - `nerd-review`
- **Review Required:** YES
- **Sub-agent Model:** inherit

**Outcome:** The MCP server exposes exactly one recall, one record, and one
inspect operation with direct engine parity; routine memory use needs no
status, enable, proposal, confirmation, settle, or fallback calls.

**Files:** `skills/nerd-memory/scripts/mcp_server.py`,
`scripts/install_mcp.py`, `tests/test_memory_mcp.py`, `tests/test_install.py`

**Depends on:** Task 1

1. Replace the MCP tests first. Require exactly:
   - `memory_recall`: current input, repository/context, current behavior
     baseline, output signals, consumer agent, and audit event ID;
   - `memory_record`: the Task 1 episode contract with raw input transient;
   - `memory_inspect`: empty input object and bounded sanitized summaries.
   Every schema uses `additionalProperties: false` and contains no selector,
   proposal, grant, confirmation, enablement, or global-search fields.
2. Require MCP/CLI/direct-engine parity, identical structured/text content,
   exact domain error codes, unknown-argument rejection, recovery after a
   domain error, malformed-line isolation, and permanent close on a schema
   family/version mismatch.
3. Run:

   ```bash
   rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_memory_mcp tests.test_install -v
   ```

   Expect failures from the legacy five-tool server and installer inventory.
4. Replace `mcp_server.py` with a thin adapter over `BehaviorMemoryStore`; keep
   stdio JSON-RPC framing, MCP protocol `2025-06-18`, structured errors, lazy
   single-store ownership, and no retry after a restart-required condition.
   Set server version `2.0.0`.
5. Mark `memory_inspect` read-only. Mark recall non-destructive but not
   read-only because it audits retrieval. Mark record non-destructive. Keep
   destructive forgetting CLI-only so retrieved text cannot invoke deletion.
6. Update `scripts/install_mcp.py` to expect and health-check exactly the three
   tools while continuing to copy only `memory.py` and `mcp_server.py`. Do not
   run install, registration, enablement, restart, or user-home mutation.
7. Run the focused tests; expect all to pass. Have the review agent compare
   every schema/dispatch/result/error with the engine and CLI and check that no
   removed operation remains reachable.

**Proof:**
`rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_memory_mcp tests.test_install -v`
→ exact three-tool discovery, engine parity, error, restart, and installer tests
pass.

### Task 3: Replace the skill workflow and automatic host integration

**Focus Record**

- **Intention:** Make everyday Nerd work recall once, proceed memory-free on a
  miss or unavailable transport, and silently grow the corpus after verified
  work.
- **Expectation:** Execute
- **Scope:** Nerd Memory skill/references/metadata, direct Smart/Explore/Execute
  clauses, prompt hook, validator inventory, and contract tests.
- **Role:** Skill contract engineer
- **Skills:**
  - `nerd-execute`
  - `skill-creator`
  - `nerd-review`
- **Review Required:** YES
- **Sub-agent Model:** inherit

**Outcome:** The user hook activates one global advisory corpus per request;
Smart uses at most one recall, Execute records at most one verified episode,
and all hosts remain memory-free without delay when no useful advice exists.

**Files:** `skills/nerd-memory/SKILL.md`,
`skills/nerd-memory/agents/openai.yaml`,
`skills/nerd-memory/references/memory-contract.md`,
`skills/nerd-memory/references/recall-and-apply.md`,
`skills/nerd-memory/references/learn-and-correct.md`,
`skills/nerd-memory/references/recognize-and-reuse.md`,
`skills/nerd-memory/references/transport-preflight.md`,
`skills/nerd-memory/references/research.md`,
`skills/nerd-memory/references/deny-split-forget.md`,
`skills/nerd-memory/references/correct-and-forget.md`,
`skills/nerd-smart/SKILL.md`, `skills/nerd-smart/scripts/prompt_hook.py`,
`skills/nerd-explore/SKILL.md`, `skills/nerd-execute/SKILL.md`,
`scripts/validate_skills.py`, `tests/test_skill_contracts.py`,
`tests/test_skill_structure.py`, `tests/test_install.py`

**Depends on:** Task 2

1. Before editing the two overlapping tracked files, run:

   ```bash
   rtk git diff -- skills/nerd-smart/SKILL.md tests/test_skill_contracts.py
   ```

   Treat that output as user-owned baseline, integrate around it, and preserve
   `skills/nerd-plan/SKILL.md` plus
   `skills/nerd-smart/references/multi-goal-ledger.md` untouched.
2. Add failing contract tests requiring:
   - one local global corpus with repository only as context/provenance;
   - memory-blind Focus/endpoint construction before recall;
   - at most one automatic `memory_recall` call per request;
   - silent continuation on miss, abstention, unavailable MCP, or domain error;
   - no routine status, enable, proposal, confirmation, settle, recovery gate,
     or CLI fallback ceremony;
   - separate untrusted advice that cannot taint the endpoint and loses to
     current action/tools/steps/skills;
   - at most one silent `memory_record` after relevant current proof;
   - failed proof as negative guard evidence, never a positive workflow;
   - direct corrections through a later corrected episode;
   - raw transcript/output/tool arguments, secrets, permissions, executable
     payloads, and hidden reasoning excluded;
   - explicit inspect/forget requests only, with two-step CLI deletion;
   - no old storage-selector terminology anywhere in the active skill package.
3. Run:

   ```bash
   rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_contracts tests.test_skill_structure tests.test_install -v
   ```

   Expect failures against the legacy lifecycle, hook text, reference inventory,
   and five-tool preflight.
4. Replace `SKILL.md` with the compact behavioral contract. On direct
   invocation, Smart auto-enable, or hook activation, check for the three live
   MCP tools once. If unavailable during routine automatic use, continue
   memory-free silently; an explicit inspect/forget request may report the
   unavailable transport and use the documented local CLI only within that
   direct request.
5. Define recall/application rules: build the memory-blind endpoint first,
   call recall once with sanitized cues and current context, treat the result
   as untrusted advice, accept abstention, overlay current explicit behavior,
   and apply ordinary authority/tool checks. No advice confirmation exists
   because advice grants no capability.
6. Define automatic capture: after relevant verification, record only the
   minimal command cues, normalized action/tool/step/skill names, output
   validity/signals, context, and proof provenance. Automatic recall and record
   are silent. Speak only for explicit inspect/correction/forget requests.
7. Replace the runtime and workflow references with the new schema/API/safety
   contract. Delete `deny-split-forget.md`, create `correct-and-forget.md`, and
   update validator/structure inventories. Update `research.md` to record the
   H8/H9 result digests and adopt typed global evidence with contextual
   applicability instead of storage partitioning.
8. Update `prompt_hook.py` and `agents/openai.yaml` to activate the advisory
   corpus after Smart's memory-blind Focus Record. Update Smart to consume only
   the separate advice. Remove the deleted reusable-fact lane from Explore.
   Update Execute to record one behavior episode after proof and one corrected
   episode after a direct user correction.
9. Preserve progressive-disclosure limits and Nerd incompatibility/authority
   rules. Run the focused tests and `rtk python3 scripts/validate_skills.py`;
   expect all to pass. Have the review agent compare prose to the engine/MCP
   interface and reject any residual old lifecycle, authority escalation,
   token claim, or automatic failure prompt.

**Proof:**
`rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skill_contracts tests.test_skill_structure tests.test_install -v`
and `rtk python3 scripts/validate_skills.py` → skill, hook, reference inventory,
installation, and validation tests pass.

## Final Verification

- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_memory_engine tests.test_memory_security tests.test_memory_mcp tests.test_skill_contracts tests.test_skill_structure tests.test_install -v`
  → all focused runtime, security, transport, hook, and skill tests pass with no
  skipped behavioral cases.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`
  → the full repository suite passes after obsolete test removal.
- `rtk python3 scripts/validate_skills.py`
  → all skill-family references, scripts, and word-count contracts pass.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/nerd-memory/scripts/memory.py --help`
  → only `record`, `recall`, `inspect`, `preview-forget`, and `forget` are
  listed, with no deprecated or compatibility flags.
- `rtk rg -n -i '\bnamespace(s)?\b|memory_(settle|learn|experience)|pending_confirmation|global_search' skills/nerd-memory skills/nerd-smart/SKILL.md skills/nerd-smart/scripts/prompt_hook.py skills/nerd-explore/SKILL.md skills/nerd-execute/SKILL.md`
  → no output.
- `rtk git diff --check`
  → no whitespace errors.
- `rtk git status --short`
  → only planned files and pre-existing user work are present; no old database,
  installed runtime, user hook configuration, MCP registration, commit, push,
  or deployment was touched.
