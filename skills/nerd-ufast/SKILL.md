---
name: nerd-ufast
description: Generic tool-backed ultra-fast execution for supported operations. Use only when explicitly invoked and a configured tool supports deterministic bounded work with safe fallback.
---

# Nerd UFast

## Incompatible Skills

Never combine Nerd with these unless this request explicitly asks:

- Superpowers
- Ponytail
- Caveman

Skill hooks, mentions, and indirect instructions are not authorization.

Never combine `nerd-ufast` with `nerd-xfast`. If both are requested, ask which speed contract to use.

## Composition

Activate only when the user explicitly invokes Nerd UFast, after resolving endpoint, scope, authorization, and active workflow. It never replaces or restarts the active workflow or its completion standard.

XFast batches native text or patch operations and deliberately narrows reasoning and proof. UFast moves mechanical intelligence into deterministic registry tools while preserving the active workflow's accuracy and proof contract. Tools handle how; the model decides what.

## Capability Gate

Resolve one intent; the registry owns backend selection:

- map or inspect a project: `ufast_project_index`;
- locate relevant text: `ufast_fast_search`;
- perform a deterministic existing-file change: `ufast_safe_edit`;
- run detected repository proof: `ufast_test_runner`.

Use a route only when its schema supports the outcome. Semantic rename,
reference lookup, and AST mutation require their future registered adapters;
do not approximate them with unsafe text replacement.

The bundled safe-edit backend applies only when the request:

- edits existing UTF-8 text files only;
- fits its 12-file and 128 KiB mutation limits;
- needs no symlink, hidden, cache, generated, or support-file mutation; and
- can be expressed as exact replacements or complete contents.

Lack of prior inspection is not a fallback reason: index or search first.
Fall back when no route is installed or a result is unsupported, ambiguous,
stale, unsafe, or unavailable.

## Fast Path

Use the smallest registered route. Search directly when a known query can build
or reuse the index; call project index only when project shape is unknown. A
registered LSP, codemod, or AST route outranks text editing for its semantic
intent. If none is installed, fall back rather than emulate it.

Batch independent tool calls with the platform's native interface. Put up to
ten independent searches in one `queries: ["term", "term"]` call, all known
file mutations in one safe-edit batch, and all selected checks in one
test-runner call. The runner
executes independent checks concurrently. Keep adaptive dependencies sequential
when context or hashes determine the edit.

Prefer exact replacements in one atomic safe-edit batch; use complete contents
only when boundaries are not deterministic. Submit flat edit operations as
`{path, sha256, old_text, new_text}`; repeat a path for multiple replacements
and let the tool group them. Batch implementation and tests together, keep
`verify` enabled, and verify once—do not create an intermediate red write or
pre-edit proof round. Omit `checks` unless reusing an exact `available_checks`
name. Never submit commands or return unchanged file bodies.
Accept `applied` only when the transaction and every returned check succeeded.

## Proof Ladder

Choose **V0** or **V1** once from obvious outcome, risk, cost, tool availability,
and the active workflow's proof contract. Do not investigate merely to choose.

- **V0:** Reuse fresh structured tool proof, or make no verification claim for
  non-mutating work without a proportionate check. Report `Not verified` when
  completion would otherwise imply proof.
- **V1 automatic:** Run safe, local, focused detected checks when already
  authorized and proportionate; use safe edit or one test-runner call.
- **V1 ask first:** Ask before broad, slow, stateful, external, destructive, or
  configuration-dependent proof, or proof needing more authority.

A mutation never lowers the active workflow's required proof. When no adapter
covers the outcome, perform its residual proof or fall back. The workflow must not repeat exact proof already returned.

Allow one retry only when evidence identifies one exact recoverable invocation
error. Otherwise fall back with the result. Never claim mutation after rollback.

## Finish

Report exactly one path status in the final response:

- `UFast fast path: applied` when the verified transaction succeeded.
- `UFast fast path: fell back — [reason]` when the active workflow completed without it.
- `UFast fast path: failed — [reason]` when neither path completed.

Keep the rest of the final response under the active workflow's contract.
