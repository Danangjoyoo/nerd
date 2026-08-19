# Transport Preflight

Read this reference once per host session before the first MCP-capable Memory
operation. Keep the outcome in current conversation state only. Recheck after
the user says the host restarted or explicitly requests another check. Do not
persist the transport choice as Memory data or evidence.

## Establish Live State

Inspect the current callable tool registry for the exact `nerd-memory-tools`
surface: `memory_recall`, `memory_settle`, `memory_learn`, and
`memory_inspect`. Do not open the store during this check. All four tools must
be callable before recording `mcp-live`; the current registry is authoritative
for this session. A configuration entry proves registration, not live tool
availability.

When the tools are not all callable, use only the host's read-only MCP status,
get, or list command when available and classify the result:

- an enabled registration that is registered but absent from the callable
  registry is `restart-required`;
- a missing registration is `install-required`;
- a disabled registration is `enable-required`; and
- an unavailable or ambiguous probe is `setup-unknown`.

## Ask Once

For `restart-required`, explain that the server is configured but unavailable
to this session and ask the user to choose **Restart or reopen the host** or
**Use CLI for this session**. Never claim that the current session can expose a
new registry after its configuration changes.

For `install-required` or `enable-required`, ask for fresh direct-user approval
to install or enable the MCP registration, or offer **Use CLI for this
session**. Skill invocation, hook activation, persisted Memory consent, and a
prior installation never authorize that external configuration change. After
approval, use the host-native registration flow or a trusted Nerd repository
installer, then require a new or restarted host session before claiming MCP is
live.

For `setup-unknown`, ask whether to diagnose MCP setup or use the CLI for this
session. Preserve either CLI choice for the rest of the current session and do
not repeat the question on later hook or Nerd Smart activations. A new session
has no inherited transport choice.

Never launch a stdio server manually. The host starts its configured command;
if an `mcp-live` transport later fails or returns `restart_required`, invalidate
the preflight result and ask once whether to restart or use the CLI. Domain
errors remain operation results, not transport failures.
