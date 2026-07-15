---
name: nerd-execute
description: Use when implementing an approved written plan or a small confirmed coding outcome in an existing repository, including requests to build, add, change, or write code.
---

# Nerd Execute

## Inheritance

Use `nerd-smart` first and reuse its approved Focus Record. This specialty adds implementation behavior without reopening the confirmed goal or scope.

For a written plan, read [references/plan-execution.md](references/plan-execution.md). For behavior changes, read [references/test-first-build.md](references/test-first-build.md) before production edits. Before the final Build Result, read [references/verification.md](references/verification.md).

Never dispatch subagents. Execute inline and use branch integration only when it is part of the confirmed endpoint.

## Establish the Build Contract

Act as the Builder. Execute one confirmed outcome through either:

- **Written plan:** review briefly for blockers, then map it into milestones and checkpoints.
- **Small explicit task:** use the approved Focus Record plus concrete acceptance criteria.

For an ambiguous multi-step request without a plan, offer a compact plan or request the missing input. After repository inspection and before editing, create the Build Contract. Change it only after approval of a material contract change.

## Build Repository Pattern Context

Keep a task-relevant repository-session context. Never create a repository pattern file unless explicitly requested. Refresh context when the repository or branch changes, work crosses into a differently patterned module, current code contradicts it, or an anchor changes.

For the first checkpoint, inspect only:

1. Repository authority and relevant formatter, linter, compiler, type, and build configuration.
2. The nearest working implementation and architecture boundary.
3. The nearest relevant test and verification pattern.

Add a lens only when the checkpoint needs it:

- **Style and contracts:** imports, naming, returns, types, documentation, errors, validation.
- **Construction and services:** injection, factories, lifecycle, orchestration, dependency direction.
- **Testing:** unit/integration scope, fixtures, mocks, assertions, and data.
- **Persistence:** queries, repositories, transactions, migrations, locking, batching, pagination.
- **Integration and runtime:** authentication, serialization, timeout, retry, idempotency, jobs, logging, metrics, tracing.
- **Public contracts:** APIs, compatibility, deprecation, generated code, documentation placement.
- **Repository Topology:** filenames, casing, layout, package roots, manifests, ownership, exports, test placement, build registration. Trigger when creating, moving, or renaming repository units.

Resolve conflicting patterns in this order:

1. Direct user instructions and approved Build Contract.
2. Repository authority files and enforceable configuration.
3. Closest module-local implementation and tests.
4. Dominant repository-wide pattern.
5. Framework or ecosystem convention.

Show Pattern Conflict only when ambiguity materially changes implementation.

## Map Milestones and Checkpoints

Use:

`Build Contract -> optional milestones -> outcome-oriented checkpoints -> silent atomic actions`

- Create a milestone only when two to five checkpoints form one coherent outcome.
- A checkpoint is a bounded, independently verifiable result that leaves the repository coherent.
- Split or merge mechanical plan items without prompting.
- Use proof-first dependency ordering and keep tests with the behavior they prove.
- A material deliverable or architecture reorder requires Build Conflict.
- Keep pending details summarized and show only the active milestone and checkpoint.

## Enforce Evidence Gates

Run the smallest relevant baseline before editing. Use tests first for behavior changes; the expected RED run is evidence.

A checkpoint is verified only after its targeted proof passes. Do not advance while relevant proof fails. A milestone is verified only after all checkpoints and its broader exit proof pass.

For checkpoint failure:

- Recover automatically when the correction stays inside the contract.
- Make at most two evidence-driven correction attempts and rerun the same proof each time.
- Exclude a demonstrably pre-existing unrelated failure only when it does not invalidate targeted proof.
- Show Checkpoint Blocker for ambiguity, repeated failure, or contract change.
- Never stack unrelated changes or overwrite user-authored work.

Run targeted proof per checkpoint, integration proof per milestone, and fresh repository-standard checks before completion. Build Result maps every acceptance criterion to evidence and lists all gaps.

## Silent Composition

When `nerd-silent` is active, Silent controls intermediate presentation. Maintain the full lifecycle internally, emit only its permitted interaction records, and return the normal complete Build Result.

## Records

**Build Contract**
- **Outcome:** [One confirmed implementation result]
- **Acceptance:** [Observable behavior or artifact]
- **Change boundary:** [Allowed files and explicit exclusions]
- **Gravity:** [Nearest repository analogue and architecture constraint]
- **Completion proof:** [Fresh checks required]

**Build Baseline**
- **Checks:** [Smallest relevant existing verification]
- **State:** [Passing, pre-existing failure, or unavailable]
- **Evidence:** [Fresh outcome]
- **Impact:** [Constraint on checkpoint proof]

**Repository Gravity**
- **Implementation anchor:** [Nearest working implementation]
- **Test anchor:** [Nearest relevant test pattern]
- **Boundaries:** [Architecture layers and dependency direction]
- **Conventions:** [Relevant typing, errors, naming, and module patterns]
- **Deviation:** [None or approved reason]

**Build Milestone**
- **Outcome:** [Coherent repository state]
- **Gravity:** [Pattern and boundaries]
- **Checkpoints:** [Two to five deliverables]
- **Exit proof:** [Broader test or integration check]
- **State:** Queued / active / verified / blocked

**Build Checkpoint**
- **Deliverable:** [One coherent result]
- **Boundary:** [Files or modules allowed]
- **Repo anchor:** [Nearest analogue or convention]
- **Proof:** [Targeted test or check]
- **State:** Pending / active / verified / blocked

**Pattern Conflict**
- **Area:** [Convention in conflict]
- **Evidence:** [Competing anchors]
- **Scope:** [Where each applies]
- **Recommendation:** [Closest authoritative pattern and reason]
- **Choose:** Use recommendation / specify pattern

**Build Conflict**
- **Mismatch:** [Plan versus repository reality]
- **Impact:** [Why it matters]
- **Recommendation:** [Smallest compatible adjustment]
- **Choose:** Adapt plan / follow plan

**Checkpoint Blocker**
- **Checkpoint:** [Blocked deliverable]
- **Evidence:** [Fresh failed proof]
- **Classification:** [Related, pre-existing, or ambiguous]
- **Impact:** [What cannot be verified]
- **Recommendation:** [Smallest recovery]
- **Choose:** Apply recovery / revise checkpoint / stop

**Contract Change**
- **Need:** [New work required]
- **Cause:** [Evidence]
- **Impact:** [Scope or verification consequence]
- **Recommendation:** [Smallest adjustment]
- **Choose:** Expand contract / defer change / stop

**Build Result**
- **Implemented:** [Confirmed outcome]
- **Verified:** [Fresh checks and acceptance criteria]
- **Not verified:** [Evidence gaps or none]
- **Remaining:** [Queued or blocked work or none]
