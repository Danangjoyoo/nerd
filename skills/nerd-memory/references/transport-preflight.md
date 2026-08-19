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
- `install-required`: the MCP server package or command is missing.
- `registration-required`: the MCP server is not registered with the host.
- `enable-required`: registration disabled.
- `setup-unknown`: no decisive probe.

3. Resolve once:
   - `restart-required`: ask the user to restart or reopen the host before claiming MCP is live.
   - `install-required`, `registration-required`, or `enable-required`: obtain
     fresh direct-user approval before installing the MCP server or changing
     host registration or enablement. If approved, make only the approved
     setup changes and require a new or restarted session before claiming MCP
     is live.
     Invocation, hooks, Memory consent, and prior installation grant no such
     authority.
   - `setup-unknown`: run read-only setup diagnosis. If it resolves to an
     installation, registration, or enablement change, obtain fresh
     direct-user approval before making that change.

Using the local Memory CLI script is always approved and requires no additional
confirmation. When MCP is not live, use the CLI automatically for the current
Memory operation; do not present it as a choice or ask permission to use it.
Never launch a stdio server manually; the host starts it. On `mcp-live`
transport failure or `restart_required`, invalidate the result, ask the user to
restart or reopen the host, and use the CLI automatically until MCP is live.
Domain errors are not transport failures.
