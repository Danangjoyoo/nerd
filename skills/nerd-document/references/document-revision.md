# Document Revision Guide

Use the requested mode below. Simplification reduces reading difficulty;
compaction reduces length; comprehensive revision increases supported coverage.
Splitting changes file boundaries; orchestration coordinates a document set.
None changes established requirements or product behavior.

## Shared Editing Rules

- Read the source and identify its reader, purpose, authoritative facts, and
  requested boundary. Reuse known answers; ask only about material uncertainty.
- Preserve obligations, prohibitions, defaults, exceptions, numbers, units,
  conditions, ordering, evidence, and unresolved questions. Keep qualifications
  beside their rules; preserve identifiers and anchors used by other documents.
- Compare the revision against the source for changed or lost meaning. A shorter
  or longer document is not proof of correctness. Mark unsupported material
  `Unknown` with its impact; route new requirements or design choices through Smart.
- Follow explicit length, format, and location requests. Do not silently drop
  required content to meet a size limit; report an unresolved conflict.

## Simplify

**Aim:** Make the same information easier for its reader to understand and use.

1. Put the reader's main answer or action first. Group related ideas under
   descriptive headings and separate prerequisites from steps and explanations.
2. Replace unnecessary jargon, abstract nouns, and tangled sentences with
   familiar words and direct verbs. Define technical terms the reader needs;
   retain exact API names, commands, field names, and normative wording.
3. Explain one idea at a time. Use a short example when it resolves ambiguity;
   keep important exceptions and causal reasoning visible.

**Check:** The reader can find the purpose and next action from the opening and
headings, and follow the explanation without reconstructing omitted reasoning.
Simplification may retain or increase length; do not force compression.

## Compact

**Aim:** Say the necessary information in less space without losing meaning.

1. Remove filler, repeated background, redundant summaries, and examples that
   add no distinct rule or insight. Merge repetition without erasing differences.
2. Give each maintained fact one authoritative home; link other uses when useful.
   Use concise prose, parallel lists, or lookup tables where they improve scanning.
3. Retain actionable steps, boundary conditions, contracts, evidence, and required
   examples. Do not replace precise instructions with vague shorthand, unexplained
   acronyms, or dense tables. Keep a summary's stated scope distinct from a full revision.

**Check:** Compare before/after coverage and readability, then report a size
change when useful using the same measure and scope. Do not claim token savings
from a line or word count. Keep content moved to references in the total.

## Make Comprehensive or Detailed

**Aim:** Fill documented coverage or explanation gaps for the reader's task.

1. Compare the source with its purpose: identify missing prerequisites, terms,
   inputs/outputs, steps, rationale, examples, exceptions, failure/recovery paths,
   constraints, and evidence. Add only categories relevant to the document type.
2. Use supplied or verified sources for additions. Distinguish established facts,
   illustrative examples, and unknowns; never invent decisions, owners, dates,
   behavior, or exhaustive coverage. Obtain needed evidence within authorized scope.
3. Keep the main path concise. Put deeper explanations, edge cases, or evidence
   in clearly labeled sections or linked references; define terms consistently.

**Check:** Each material gap is supported and filled or marked Unknown with its
impact. Examples agree with rules; detail adds information rather than repetition.
Stop at the reader's purpose, not every conceivable topic.

## Split

**Aim:** Give independently useful topics coherent homes and navigable boundaries.

1. Split by reader task, topic, responsibility, or change frequency. Avoid arbitrary
   equal-size files; obey explicit limits and existing document-layout contracts.
2. Map each original section to one destination. Keep context and prerequisites
   needed to use each part; place shared definitions in one authoritative source.
3. Create or update an entry document with purpose, part links, and reading order.
   Move content, repair relative links/assets and references within scope, and
   preserve existing anchors or redirects where supported.
4. Replace superseded content with navigation or remove it when the requested
   reorganization requires it. Keep unrelated material; disclose inbound links
   outside accessible scope that could not be checked or repaired.

**Check:** Every retained source section has a destination, links resolve, parts
have enough context, and no duplicate authoritative bodies or orphan parts remain.

## Orchestrate

**Aim:** Make multiple documents function as one coherent information system.

1. Inspect only the requested set and direct dependencies. Identify each document's
   audience, purpose, authoritative content, inputs, and downstream consumers;
   record existing owners or update triggers only when established and useful.
2. Assign clear roles such as entry/overview, procedure, reference, or evidence.
   Choose a canonical source for shared facts; cross-link consumers instead of
   maintaining competing copies. Surface contradictions rather than silently
   choosing which conflicting requirement wins.
3. Arrange reading and update order by dependency. Update the requested documents,
   entry navigation, and affected references together; add a concise map or index
   only when it helps readers find or maintain the set.
4. Keep each document usable for its purpose. Avoid creating a coordination
   framework, workflow automation, new approval process, or ownership assignments
   merely to organize documentation.

**Check:** Readers can locate the right document and its authority; shared facts,
terms, and links agree; dependencies have a usable order; conflicts and inaccessible
sources remain explicit. Coordination never authorizes publishing or delegation.
