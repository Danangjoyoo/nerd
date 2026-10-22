# Writing for Google Slides

## Use When

The audience needs a presentation to understand a finding, evaluate a proposal,
make a decision, or follow a briefing. A slide deck selects the most important
ideas from a document; it does not distribute every paragraph across slides.
Read the relevant document-type guide for the established content.

## Build the Story

1. Identify the audience's decision or takeaway.
2. State the conclusion before supporting detail when the audience can assess it.
3. Give each slide one main message, expressed in its title.
4. Support the message with a few bullets, a small comparison table, or a useful
   chart or diagram. Use numbered points for sequence or priority.
5. End with the requested decision or next actions when those are established.

Separate the visible slide from speaker notes. Put secondary explanation,
sources, and presenter prompts in notes or an appendix; keep required caveats
on the slide where they change the message. An asynchronous deck must remain
understandable without a speaker, so retain essential reasoning on-slide.

## Example: Export Release Decision

Fictional slide-by-slide draft:

| Slide | Message title | Visible content | Notes / appendix |
| --- | --- | --- | --- |
| 1 | Hold the export release until isolation review is complete | Decision requested; reviewer assignment needed | Scope and review history |
| 2 | The request and download flows passed staging checks | Three checked flows; tested build/environment | Links to actual evidence in a real deck |
| 3 | Cross-account isolation still lacks approval | Risk, missing review, release consequence | Review criteria |
| 4 | One reviewer assignment unblocks the next decision | Requested owner decision and next checkpoint | Detailed follow-up register |

Example slide text:

```text
Title: Cross-account isolation still lacks approval

- Risk: an account could retrieve another account's export.
- Evidence gap: the security review has not been completed.
- Release condition: confirm isolation before granting approval.

Speaker notes: No exposure has been established by this example. The risk
statement describes the review concern, not a confirmed production incident.
```

Compare with a weak title such as “Security Update”: the message title tells
the audience what matters before they read the slide.

## Make Slides Readable

- Keep tables narrow enough to read at presentation size; put the full register
  in an appendix or linked Sheet.
- Prefer a chart when a numerical comparison matters; label units, time window,
  sample, and source. Do not invent a graph from unsupported numbers.
- Use a diagram only when relationships are clearer visually. Explain its key
  meaning in text and provide an accessible description when supported.
- Use whitespace and consistent hierarchy. Avoid dense paragraphs, tiny sources,
  or decorative breaks that separate a claim from its evidence.
- Spell out status as words as well as color. Review reading order and contrast
  when the tooling supports layout inspection.

## Delivery Check

Verify every message title against its evidence, the slide order, the requested
decision, notes, links, and any charts. For a deck file, use the presentation
artifact skill and inspect rendered slides when available. For authorized native
creation, return the confirmed Slides link.

When native or file tooling is unavailable, deliver a slide-by-slide draft with
separate visible content and speaker notes. Label it as a draft rather than a
finished presentation. Do not claim layout validation from an outline.

## Platform Reference

Google documents [presenter views](https://support.google.com/docs/answer/1696787?hl=en)
and [speaker notes](https://developers.google.com/workspace/slides/api/guides/notes).
Use current help for exact UI or integration instructions.
