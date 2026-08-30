# Transport Preflight

At each activation, after Smart has fixed the memory-blind Focus Record and
endpoint, check the current callable MCP registry once for
`nerd-memory-tools`. The live server must expose exactly `memory_recall`,
`memory_record`, and `memory_inspect`.

When all three are callable, routine work may use at most one recall and one
record. Do not add transport ceremony or start a manual stdio process.

When any tool is absent, or a routine call returns a transport or domain error,
continue memory-free silently. Do not retry, prompt, or delay the task. There
is no automatic CLI fallback and no recovery gate.

For an explicit inspect or forget request only, report that MCP is unavailable
and use the documented local CLI only for that direct request:
`python3 <skill-root>/scripts/memory.py`. Inspection uses `inspect`; deletion
uses the two-step CLI workflow in [correct and forget](correct-and-forget.md).
Do not change host configuration without separate direct authorization.
