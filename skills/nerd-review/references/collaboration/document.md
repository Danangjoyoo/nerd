# Document Review Collaboration

Use for accuracy, usability, consistency, and presentation of an existing
document. A request to judge product choices also needs the product guide.

## Companion Sequence

| Step | Skill | Bounded task | Return to Review |
| --- | --- | --- | --- |
| Identify reader contract | `nerd-document` | Match audience, purpose, document type, and destination | Relevant reader needs and content/presentation criteria |
| Check source claims | `nerd-explore` | Verify one consequential claim against named authoritative material | Source location, supported/contradicted/unknown, version limits |
| Evaluate | Review | Compare the document with criteria and verified facts | Located defect and reader consequence |
| Challenge | `nerd-document` | Test whether context or an explicit format already resolves the concern | Concrete omission/error or harmless editorial preference |

Read the matching document-type guide from nerd-document, such as PRD, TRD,
runbook, or reference, plus a platform guide only when presentation matters.
Use its human-friendly writing guide for readability questions. These provide
criteria, not permission to draft replacements or require every template field.

## Review Lenses

| Level | Check | Finding evidence |
| --- | --- | --- |
| 1 | Facts, examples, links, terminology, tables, procedural order | Exact contradiction, broken target, incorrect example, or impossible step |
| 2 | Agreement with source contracts, audience needs, prerequisites | A reader lacks or receives incorrect information needed for the stated task |
| 3 | Information structure, ownership, decision visibility | Organization or conflicting authorities cause a specific wrong action/decision |

Trace important assertions to their actual sources and versions. For a runbook,
follow the stated prerequisites through the recovery procedure read-only. For
native documents, inspect rendered layout when supported; report unavailable
rendering as a limitation and never claim visual validation from extracted text.
Use page/heading/table/row anchors when file line numbers do not exist.

## Proof and Completion

For example, a runbook that tells operators to restart before preserving the
only diagnostic evidence may have a concrete recovery consequence. A preferred
heading style alone does not. Distinguish an inaccurate claim from an unavailable
source. Report a source conflict with its decision impact rather than inventing
an authoritative version. Finish with consolidated Review findings; do not edit,
comment on, publish, or rewrite the reviewed document without a new user request.
