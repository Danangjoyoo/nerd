# Transport Preflight

Run this once per host session before the first MCP-capable Memory operation.
Keep the result in current conversation state; recheck only after a reported
restart or explicit request. Do not persist the transport choice as Memory data
or evidence.

1. Inspect the current callable tool registry for `nerd-memory-tools`:
   `memory_recall`, `memory_settle`, `memory_learn`, and `memory_inspect`. All
   four callable means `mcp-live`; configuration proves registration, not live
   availability. Do not open the store.
2. Otherwise use the host's read-only MCP status, get, or list command:

- `restart-required`: registered but absent from the callable registry.
- `install-required`: registration missing.
- `enable-required`: registration disabled.
- `setup-unknown`: no decisive probe.

3. Resolve once:
   - `restart-required`: offer **Restart or reopen the host** or **Use CLI for
     this session**.
   - `install-required` or `enable-required`: obtain fresh direct-user approval
     before changing configuration, or offer **Use CLI for this session**.
     Invocation, hooks, Memory consent, and prior installation grant no such
     authority. Require a new or restarted session before claiming MCP is live.
   - `setup-unknown`: offer setup diagnosis or **Use CLI for this session**.

A CLI choice lasts this session and suppresses later hook or Nerd Smart prompts;
new sessions inherit nothing. Never launch a stdio server manually; the host
starts it. On `mcp-live` transport failure or `restart_required`, invalidate the
result and ask once to restart or use CLI. Domain errors are not transport
failures.
