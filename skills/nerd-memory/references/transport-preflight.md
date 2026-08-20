# Transport Preflight

At the start of every activation — direct invocation, Nerd Smart auto-enable,
or user-installed hook event — run this preflight before any Memory operation,
including namespace status or `enable`. Search the current host MCP state first.
Do not reuse an earlier activation's transport choice. Do not persist the
transport choice as Memory data or evidence.

## Step 1 — Search MCP state

Inspect the current callable tool registry for `nerd-memory-tools`: `memory_recall`,
`memory_settle`, `memory_learn`, `memory_experience`, and `memory_inspect`. All
five callable means
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

For every non-live state, present the detected state and the concrete recovery.
Encourage the MCP path: recommend the user enable or turn on the server for
`enable-required` or `restart-required`, registering it for
`registration-required`, and installing it for `install-required`. Obtain fresh
direct-user confirmation before changing host configuration or proceeding with
the recovery. Invocation, hooks, Memory consent, and prior installation grant
no such authority.

- **Approved:** make only the confirmed change, or ask the user to restart or
  reopen the host when that is the required recovery. Wait for a new activation
  and fresh preflight before claiming `mcp-live` or performing Memory work. Do
  not use CLI fallback while activation is pending.
- **Rejected:** set the current activation's transport to `cli-fallback` and
  continue. A later invocation or automatic activation starts a new preflight
  and may prompt again.

**`setup-unknown`:** Run read-only setup diagnosis. Re-classify the result as
one of the sub-states above and apply its resolution.

## CLI fallback

The local Memory CLI script is always approved as a mechanism, but fallback is
not preferable. Only after the user rejects the recommended MCP recovery may
the current activation select it. Do not use the CLI while confirmation or
activation is pending, and do not select it merely because MCP is not live.
Operations documented as CLI-only use it directly and are not transport
fallback. Never launch a stdio server manually; the host starts it.

On `mcp-live` transport failure, invalidate the result and return to Step 1.
Recommend restoring MCP and ask for fresh confirmation; use CLI fallback only
if the user rejects that recovery. Domain errors are not transport failures.
