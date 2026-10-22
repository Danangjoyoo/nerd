# Collaboration Orchestration

## Choose the Review Question

Start from Smart's resolved Review Focus Record. Keep the artifact, revision or
baseline, intended reader/user, accepted criteria, and decision being supported
in context. Reuse supplied facts; ask only when an unresolved choice changes
what would count as a defect. “Review this PRD” is product review with document
checks; “check this PRD's wording” is document review. A hotfix PR is hotfix
review under the pull request delta boundary.

Choose the matching context guide from the skill entrypoint. For mixed scope,
use the primary artifact's guide and add another only for an actual dependency:
a PRD's acceptance criteria may require test review; a hotfix may require code
and regression-test review. Do not review every linked artifact in full.

## Orchestrate One Evidence Cycle

| Stage | Owner | Input | Return / next decision |
| --- | --- | --- | --- |
| Frame | Review | Named artifact and agreed purpose | Specific review questions and relevant sources |
| Establish criteria | Matching companion | Accepted requirements, audience, constraints | Applicable criteria, their authority, unresolved assumptions |
| Inspect | Review; Explore for factual gaps | One criterion and exact scope | Located claim, behavior, contradiction, or evidence gap |
| Challenge | Matching companion | Candidate defect and supporting evidence | Strongest counterexample, trade-off, or missing causal link |
| Synthesize | Review | Candidate plus challenge result | Keep, downgrade, merge, discard, or obtain one discriminating fact |
| Finish | Review | Surviving evidence | Prioritized findings and material verification limitations |

Companions are skills applied within this review, not instructions to spawn
agents. Read their SKILL.md before using them. Their Review Support mode takes
precedence over their normal writing, ideation, diagnosis, or repair workflow.
Explore returns sourced facts; it does not decide findings. Review alone applies
severity and the Plain or Pull request finding boundary.

## Bounded Handoff

Pass only what changes the companion's answer:

- **Question:** One concrete criterion, factual uncertainty, or causal claim.
- **Scope:** Exact artifact/revision, section/symbol, and permitted source boundary.
- **Criteria:** Accepted goals and constraints; label assumptions separately.
- **Evidence:** Exact source locations, observed behavior, and known limitations.
- **Return:** Requested facts, challenge, or criteria, with sources and unknowns.
- **Boundary:** Advisory Review; no edits, publication, repair, or endpoint change.

Use the return before requesting another pass. Revisit only when new evidence
changes the judgment; do not cycle companions for consensus. If a companion or
source is unavailable, use accessible evidence and disclose the material limit.
Do not silently substitute invented criteria or claim the collaboration ran.

## Resolve Disagreements and Stop

Established requirements govern intended behavior; observed implementation
establishes actual behavior, not product intent. Respect explicit source
precedence. When sources conflict without a clear authority, report the exact
conflict and consequence; do not choose a new requirement for the user.

A concern becomes a finding only with a located defect, supported trigger or
reader action, and concrete consequence. A missing template section, an
unselected alternative, or absent evidence alone does not establish failure.
For a claimed pass or readiness decision, show whether missing evidence makes
that claim unsupported. Keep ordinary unknowns in verification limitations.

Deliver findings through chat or the explicitly requested platform comments,
using the entrypoint's matching tool guide. This delivery does not authorize
rewriting reviewed content.

Stop when each material review question is supported or explicitly limited and
candidate findings survive challenge. Return the entrypoint's findings format,
not separate companion reports, a rewritten artifact, or an implementation plan.
