# UFast MCP Integration Plan

## Outcome

Installing Nerd through `scripts/install.sh` makes `inspect` and
`apply_verify` available automatically in new Codex, Claude Code, and Cursor
sessions.

The installer may start the server briefly for a health check, but it does not
leave a daemon running. Each supported agent owns the MCP server lifecycle for
its sessions.

## Confirmed Inputs

- The shared MCP server must support Codex, Claude Code, and Cursor.
- Installing Nerd through `scripts/install.sh` must also install and register
  the UFast MCP server for the selected agents.
- New sessions must expose `inspect` and `apply_verify` without a separate
  manual start command.
- The existing tool-only experiment is the implementation source and latency
  baseline.
- UFast remains usable through its current bounded fallback when MCP tools are
  unavailable.

## KISS Breakdown

- **Required outcome:** Install, register, and invoke two UFast MCP tools across
  all three supported agents.
- **Smallest change:** Add one dependency-free stdio MCP server, one shared
  installer helper, UFast invocation rules, and focused tests.
- **Proof:** Each agent registration resolves to the installed server, both
  tools appear in `tools/list`, and their focused contract tests pass.
- **Not needed:** A permanent daemon, remote server, authentication, plugin
  conversion, or changes to other Nerd skills.

## Constraints and Non-goals

- Preserve unrelated MCP registrations and agent configuration.
- Reinstallation must be idempotent.
- A conflicting non-Nerd server named `nerd-ufast-tools` must block rather than
  be overwritten.
- Keep the server dependency-free so Nerd installation retains its current
  Python and Node prerequisites.
- Never execute verification commands through a shell.
- Confine every read and mutation to the requested workspace.
- Do not claim the experimental latency figures for the production server
  until they are rerun with production invalidation and MCP behavior.
- Generic skill-only installation cannot guarantee MCP registration; automatic
  registration is provided by Nerd's `scripts/install.sh`.

## Worktree and Baseline

- The worktree already contains uncommitted UFast skill, benchmark, installer,
  workflow, README, and experiment changes. Preserve all existing work and
  patch in-scope files rather than replacing them.
- The local experiment reports approximately 96.6–97.2% faster warm indexed
  inspection and 0.34–0.73% faster combined apply-and-verify execution on its
  recorded host. These figures are directional until repeated against the
  production MCP implementation.

## Ordered Work

### Task 1: Promote the prototype into UFast

**Files:**

- Create: `skills/nerd-ufast/scripts/mcp_server.py`
- Create: `skills/nerd-ufast/scripts/ufast_tools.py`

**Change:**

- Implement dependency-free MCP initialization, `tools/list`, and `tools/call`
  over stdio.
- Expose exactly `inspect` and `apply_verify`.
- Return JSON-compatible structured results plus text content for clients that
  do not consume structured MCP output.
- Handle clean shutdown and malformed requests without corrupting the stdio
  protocol.

**Proof:**

- Send MCP `initialize` and `tools/list` requests directly to the server and
  require both tools with valid input schemas.

### Task 2: Harden the production tool contracts

**Files:**

- Modify: `skills/nerd-ufast/scripts/ufast_tools.py`
- Create: `tests/test_ufast_mcp.py`

**Change:**

For `inspect`:

- Accept a workspace, batched exact symbols or paths, context size, and result
  limit.
- Return paths, bounded content, hashes, and truncation state.
- Maintain a warm per-workspace index and refresh entries whose file metadata
  changed.
- Reject all resolved paths outside the requested workspace.

For `apply_verify`:

- Accept a workspace, unified patch, expected starting hashes, verification
  commands, output limits, and timeouts.
- Reject stale files before mutation.
- Apply the patch without a shell, run checks without a shell, and limit
  captured output.
- Restore touched files after failed verification.
- Return changed paths, diff hash, checks, exit codes, timing, and rollback
  state.

**Proof:**

- Prove batched inspection equivalence, index invalidation, workspace
  confinement, successful mutation, stale-hash rejection, rollback, timeout,
  and output limits.

### Task 3: Add automatic MCP installation

**Files:**

- Create: `scripts/install_mcp.py`
- Create: `tests/test_install_mcp.py`
- Modify: `scripts/install.sh`

**Change:**

- Copy the MCP runtime to the stable location
  `~/.nerd/mcp/nerd-ufast/` or the equivalent under `NERD_INSTALL_HOME`.
- Run the installer after skill installation and Smart-hook configuration.
- Register `nerd-ufast-tools` only for the selected agents.
- Use the installed runtime path rather than a repository checkout path.
- Run one direct initialize-and-list health check, then stop the health-check
  process.

Registration routes:

- Codex: `codex mcp add nerd-ufast-tools -- python3 <server>`.
- Claude Code:
  `claude mcp add --scope user nerd-ufast-tools -- python3 <server>`.
- Cursor: `cursor --add-mcp <JSON definition>` at user scope.

**Proof:**

- Use temporary homes and stub CLIs to prove the exact registrations without
  changing the developer's real configuration.

### Task 4: Make installation safe and idempotent

**Files:**

- Modify: `scripts/install_mcp.py`
- Modify: `tests/test_install_mcp.py`

**Change:**

- Detect an existing Nerd-managed registration and replace only its runtime
  path when necessary.
- Leave an already-correct registration unchanged.
- Reject a same-name registration that does not point to the Nerd runtime.
- Preserve every unrelated MCP definition.
- Handle paths containing spaces without shell interpolation.
- Fail with an actionable message when a requested agent CLI is unavailable.
- Support `claude`, `codex`, `cursor`, and `all` consistently with the current
  installer interface.

**Proof:**

- Run first-install, repeated-install, upgrade, conflict, missing-CLI, and
  multi-agent tests against temporary configuration roots.

### Task 5: Make UFast invoke its core tools

**Files:**

- Modify: `skills/nerd-ufast/SKILL.md`
- Modify: `skills/nerd-ufast/agents/openai.yaml`
- Modify: `tests/test_skill_contracts.py`
- Modify: `scripts/validate_skills.py`

**Change:**

- Add a compact `Core Tools` contract:

```text
Cache hit -> jump directly
Cache miss needing exact context -> inspect
Known patch and proof -> apply_verify
Tool unavailable -> existing bounded fallback
```

- Require one batched `inspect` call when exact missing context is needed.
- Require one `apply_verify` call when the patch and focused checks are known.
- Do not invoke `apply_verify` when UFast eligibility, target, authorization,
  or safety is unresolved.
- Keep the existing zero-planning, single-shot, and minimal-output contracts.
- Register the two bundled scripts in skill validation.

**Proof:**

- UFast contract tests require tool preference, batching, eligibility, and the
  unavailable-tool fallback without weakening existing safety gates.

### Task 6: Verify cross-agent session availability

**Files:**

- Modify: `tests/test_install_mcp.py`
- Modify: `tests/test_workflows.py`
- Modify: `.github/workflows/release.yml`

**Change:**

- Prove selected-agent installation registers only the requested client.
- Prove `all` registers Codex, Claude Code, and Cursor.
- Prove each registered command launches the installed server and returns both
  tools from `tools/list`.
- Add release checks for the bundled MCP runtime and registration path.
- Keep actual interactive agent launches outside deterministic CI.

**Proof:**

- Temporary-home integration tests pass for all three registration formats and
  server launches.

### Task 7: Document installation and lifecycle

**Files:**

- Modify: `README.md`
- Modify: `tests/test_readme.py`

**Change:**

- Document that Nerd's installer automatically registers UFast MCP tools.
- State that a new agent session is required after first installation.
- State that the agent starts and stops the stdio server per session; the
  installer leaves no daemon running.
- Document the generic skill-only installation limitation and the bounded
  fallback.
- Do not publish production speed claims before the production rerun.

**Proof:**

- README contract tests match the installer and lifecycle behavior.

### Task 8: Rerun production latency evidence

**Files:**

- Modify: `docs/experiments/inspect-apply-verify/bench.py`
- Create or replace from fresh evidence:
  `docs/experiments/inspect-apply-verify/results/raw.json`
- Create or replace from fresh evidence:
  `docs/experiments/inspect-apply-verify/results/report.md`

**Change:**

- Point the experiment at the production tool handlers or MCP server.
- Run the existing four cases with five discarded warm-up pairs and 100
  measured pairs each.
- Preserve slower or inconclusive results.
- Attribute improvement separately to indexed operation time and reduced MCP
  requests.

**Proof:**

```bash
rtk python3 docs/experiments/inspect-apply-verify/bench.py --check
```

Expected: raw evidence and report reproduce exactly from the paired samples.

## Final Validation

```bash
rtk python3 -m unittest tests.test_ufast_mcp tests.test_install_mcp tests.test_skill_contracts tests.test_workflows tests.test_readme -v
rtk python3 scripts/validate_skills.py
rtk python3 -m unittest discover -s tests -v
rtk python3 docs/experiments/inspect-apply-verify/bench.py --check
rtk git diff --check
```

## Acceptance Criteria

- Nerd's installer registers `nerd-ufast-tools` for every selected supported
  agent.
- New Codex, Claude Code, and Cursor sessions expose `inspect` and
  `apply_verify` automatically.
- Installation leaves no permanent daemon running.
- The installed server path remains valid independently of the cloned
  repository.
- Reinstallation is idempotent and preserves unrelated configuration.
- `inspect` invalidates changed index entries and cannot escape its workspace.
- `apply_verify` rejects stale inputs and restores touched files after failed
  verification.
- UFast prefers the core tools when eligible and retains its bounded fallback.
- Production latency evidence is fresh, reproducible, and reported honestly.

## Self-Review

- **Completeness:** Covers the shared server, both production tool contracts,
  automatic installation, three agent registrations, UFast invocation,
  lifecycle documentation, safety, and fresh latency proof.
- **Simplicity:** Reuses one server and one installer helper across all agents;
  adds no daemon, remote service, plugin conversion, or external dependency.
- **Risks:** Agent CLI registration behavior can change across versions. Tests
  must validate command construction and temporary-home integration, while
  README wording must avoid promising live-session refresh without a restart.
