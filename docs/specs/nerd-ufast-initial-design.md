# UFast — Ultra Fast Execution Mode
Version: v0.1

## Philosophy

UFast is NOT a smarter execution mode.

UFast is a deterministic execution mode.

Its goal is to reduce:

- LLM reasoning
- Tool round trips
- Context loading
- Output verbosity

The fastest token is the one never generated.

---

# Primary Goal

Minimize total wall-clock latency.

Priority order:

1. Eliminate work
2. Reuse work
3. Batch work
4. Automate work
5. Reason only when unavoidable

Never optimize prompts before optimizing execution.

---

# Activation and Eligibility

UFast activates only when the user explicitly invokes `nerd-ufast`.

The task is eligible only when every condition is true:

1. The required outcome is concrete and observable.
2. Every mutation target is known.
3. The applicable implementation pattern is already known or directly available.
4. The work fits one continuous mutation chain.
5. A focused verification command is available.
6. No material design, ownership, safety, or authorization question remains.
7. The task does not involve security, authentication, migration, data-loss,
   concurrency, or distributed-system risk.

Reject an ineligible task before mutation. Recommend XFast only when outcome
and scope remain resolved but bounded inference is required. Recommend the
accuracy-preserving workflow for uncertainty, broad scope, or high-risk work.
Never load or invoke another Nerd skill automatically.

---

# Execution Pipeline

Follow this order and skip a step only when it is irrelevant.

1. Apply the eligibility gate.
2. Reuse valid current context.
3. Reuse a current project map or cache entry when available.
4. Perform at most one exact-navigation batch when needed.
5. Read only the complete mutation surface and nearest required authority.
6. Perform one mutation chain.
7. Execute one focused verification wave.
8. If proof identifies one exact local correction, repair once and rerun only
   the failed check.
9. Return immediately.

No planning artifact, exploratory search, intermediate review, optional
cleanup, or second implementation pass is permitted.

---

# Context Rules

Reuse existing context only while its freshness is established.

Never reread unchanged files.

Never reread previous tool output.

Refresh context ONLY if:

- file changed
- command failed
- conflicting evidence appears
- output is incomplete or truncated

---

# Project Map

The canonical project map is:

.nerd/project-map.json

Optional derived caches live under `.nerd/cache/`.

The map should contain:

- architecture
- module ownership
- important entrypoints
- test locations
- commands
- conventions

Treat a current project map as primary navigation.

UFast never generates or refreshes the project map. If required navigation
data is missing or stale, use one exact lookup or reject the task.

---

# Search Policy

Never perform exploratory searching.

Allowed:

- exact symbol search
- exact filename search
- indexed lookup

Forbidden:

- recursive curiosity searches
- "maybe this file"
- architecture discovery
- repeated equivalent queries

If the project map contains the target:

jump directly.

---

# Read Policy

Read minimum possible.

Preferred order:

symbol
↓

function

↓

class

↓

file

↓

directory

↓

repository

If the complete mutation surface is not known after one navigation batch,
reject the task before editing.

---

# Tool Policy

Always batch independent operations.

Bad

search A

search B

search C

Good

batch_search(A,B,C)

Bad

read A

read B

Good

batch_read(A,B)

Bad

edit

test

edit

test

Good

edit

single verification

---

# Mutation Policy

Perform one continuous, structured mutation chain.

Do not stop for:

- planning
- explanation
- intermediate summaries
- TODO generation

If blocked, fail before partial or speculative work.

---

# Existing Pattern Policy

Never invent a new repository pattern in UFast.

Always clone nearest existing implementation.

Priority:

1. Existing implementation
2. Existing test
3. Existing convention
4. New implementation

If no applicable pattern exists, reject the task instead of reaching item 4.

---

# Verification Policy

Run lowest proof level that validates the claim.

Examples

rename

↓

compile

formatter

↓

format

business logic

↓

targeted unit test

API

↓

affected endpoint

Never run repository-wide verification. A request that requires it is
ineligible for UFast.

Never report `PASS` without naming a fresh successful check.

---

# Output Policy

Maximum verbosity: LOW

Never narrate execution.

Never explain obvious changes.

Never summarize every file.

Output format:

Completed.

Verification:
PASS — <focused check>

or

Completed.

Verification:
NOT RUN — <reason>

or

Blocked:
<reason>

Escalation:
<XFast, accuracy-preserving workflow, or user decision>

Nothing else.

---

# Deterministic Tasks

These categories are deterministic only when every eligibility condition is
already satisfied:

- rename
- formatting
- imports
- typo
- lint fix
- dependency bump
- CRUD
- simple refactor
- config edits

Task category alone never establishes eligibility.

---

# Escalation

Recommend XFast when the outcome and scope remain resolved but execution needs
bounded inference, multiple related operations, or broader end proof.

Recommend the accuracy-preserving workflow when work involves:

- architecture or ownership uncertainty
- multiple subsystems or repository-wide impact
- design decisions or trade-off analysis
- security or authentication
- migrations or data-loss risk
- concurrency
- distributed systems

Block for a user decision when authorization, safety, or required outcome is
unresolved.

---

# Cache Rules

Consume current entries from:

.nerd/cache/

Possible files:

project-map.json

symbol-index.json

commands.json

conventions.json

dependency-map.json

test-map.json

Never regenerate caches inside UFast. Skip an optional stale cache; reject the
task when stale navigation data is required.

---

# Tool Preference

Prefer specialized tools over shell.

Priority:

rename_symbol()

find_references()

ast_edit()

batch_read()

batch_search()

targeted_test()

Only use shell when no dedicated tool exists.

---

# Failure Strategy

One repair retry maximum.

Retry only after acquiring NEW evidence.

Never repeat identical operations or retry without new evidence.

---

# Golden Rule

Every additional LLM call must justify its latency.

Every additional tool call must justify its existence.

Every additional token must justify its cost.

If not, remove it.
