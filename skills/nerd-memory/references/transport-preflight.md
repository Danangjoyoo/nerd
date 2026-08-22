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

**`setup-unknown`:** Run read-only setup diagnosis. Re-classify the result as
one of the other sub-states before showing a gate.

For every other non-live state, start with exactly this one-sentence gate:

`Want to use fallback instead?`

Include no state or recovery explanation in this first gate. Do not ask the
user to restart, reopen, or resend before they answer it.

- **Yes:** treat the answer as rejection of the recommended MCP recovery, set
  the current activation's transport to `cli-fallback`, and continue. A later
  invocation or automatic activation starts a new preflight and may prompt
  again.
- **No:** present the detected state and the concrete recovery. Recommend the
  user enable or turn on the server for `enable-required` or
  `restart-required`, register it for `registration-required`, or install it
  for `install-required`. Obtain fresh direct-user confirmation before changing
  host configuration or proceeding with the recovery. Invocation, hooks,
  Memory consent, and prior installation grant no such authority. Make only
  the confirmed change, or ask the user to restart or reopen the host when that
  is the required recovery. Wait for a new activation and fresh preflight
  before claiming `mcp-live` or performing Memory work. Do not use CLI fallback
  while activation is pending.

## CLI fallback

The local Memory CLI script is always approved as a mechanism, but fallback is
not preferable. Only after the user rejects the recommended MCP recovery may
the current activation select it. Do not use the CLI while confirmation or
activation is pending, and do not select it merely because MCP is not live.
Operations documented as CLI-only use it directly and are not transport
fallback. Never launch a stdio server manually; the host starts it.

On `mcp-live` transport failure, invalidate the result and return to Step 1.
After reclassification, use the same short fallback gate. Domain errors are not
transport failures.
