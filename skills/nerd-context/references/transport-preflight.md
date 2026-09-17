# Context Transport Preflight

Nerd Context runs over an MCP adapter first; a CLI fallback exists but is
gated. Search the callable registry for **all three** of `context_recall`,
`context_capture`, and `context_inspect` on every activation.

## States

- **live** — All three tools respond to `tools/list` within the activation
  budget. Proceed with MCP.
- **registered_not_live** — The server is registered but the process is
  not reachable. Report `context transport registered but not reachable`
  once and continue Context-free unless the user explicitly opts into the
  CLI recovery below.
- **disabled** — The three tools are absent from the callable registry.
  Report `context transport disabled for this session` once and continue
  Context-free.
- **missing** — No `nerd-context-tools` registration exists. Continue
  Context-free silently on routine hook activation; report only on an
  explicit user invocation.
- **unknown** — Registry probe raised. Report the domain-error class and
  continue Context-free.

Never launch a server manually. Never persist the transport choice.

## Guarded CLI fallback

CLI use is permitted only when:

1. The user is invoking Context explicitly for inspect or forget, and
2. The MCP transport has been reported unavailable in this session, and
3. The user authorizes the CLI recovery for this session (an existing
   current-session authorization satisfies this condition without another
   prompt).

The CLI reads a single JSON object from stdin and writes a single JSON
response to stdout. It never spawns background processes and never touches
Memory.

## Separation from Memory

Memory has its own transport-preflight rule and continues memory-free
silently on any failure. This document applies to Context only; do not
copy its language into Memory.
