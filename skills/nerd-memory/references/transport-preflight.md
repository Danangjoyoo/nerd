# Transport Preflight

Run once per host session before the first MCP-capable Memory operation.
Keep the result in current conversation state; recheck only after a reported
restart or explicit request. Do not persist the transport choice as Memory data
or evidence.

## Step 1 — Check active

Inspect the current callable tool registry for `nerd-memory-tools`: `memory_recall`,
`memory_settle`, `memory_learn`, and `memory_inspect`. All four callable means
`mcp-live`. Configuration proves registration, not live availability.

**If `mcp-live` → transport resolved. Continue session.**

## Step 2 — Detect sub-state

Use the host's read-only MCP status, get, or list command:

- `restart-required`: registered but absent from the callable registry.
- `enable-required`: registration is disabled.
- `install-required`: the MCP server package or command is missing.
- `registration-required`: the MCP server is not registered with the host.
- `setup-unknown`: no decisive probe result.

## Step 3 — Resolve by sub-state

**`restart-required` or `enable-required` (activation — always approved):**
Perform the activation automatically. Ask the user to restart or reopen the
host, then wait for the new session before claiming `mcp-live`.
No approval gate. Continue session using CLI fallback until MCP is live.

**`install-required` or `registration-required` (install/register — ask approval):**
Present the required action and obtain fresh direct-user approval before
making any change. Invocation, hooks, Memory consent, and prior installation
grant no such authority.

- **Approved:** make only the approved changes. Require a new or restarted
  session before claiming `mcp-live`. Continue session using CLI fallback.
- **Rejected:** set session transport to `cli-fallback`. Continue session.
  Do not recheck or re-prompt for this session.

**`setup-unknown`:** Run read-only setup diagnosis. Re-classify the result as
one of the sub-states above and apply its resolution.

## CLI fallback

Using the local Memory CLI script is always approved and requires no additional
confirmation. When MCP is not live or approval was rejected, use the CLI
automatically for every Memory operation in this session. Do not present it as
a choice or ask permission to use it. Never launch a stdio server manually; the
host starts it.

On `mcp-live` transport failure mid-session, invalidate the result, ask the
user to restart or reopen the host, and switch to CLI automatically until MCP
is live again. Domain errors are not transport failures.
