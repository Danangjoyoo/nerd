"""Bounded lexical candidate: whole punctuated identifier tokens.

Investigation only. Approved by docs/specs/nerd-context-handover.md to test
whether retaining whole hyphen/underscore identifiers alongside the existing
unigrams closes the required-recall gap on the 48 gold cases without altering
BM25/novelty parameters.

The baseline ``structured.py`` module is unchanged; its source hash and its
tracked verdict evidence remain valid. This module wraps the baseline ledger
and swaps only:

- ``_terms`` — return unigrams PLUS whole punctuated identifiers.
- FTS5 tokenizer — treat ``-`` and ``_`` as token characters so
  punctuated identifiers survive tokenization.

Nothing else changes: BM25 exponents, novelty (Jaccard) discount, byte budget,
mandatory ordering, deployable pack framing, and stop-word/single-digit
filters on plain unigrams are all preserved.
"""

from __future__ import annotations

import re

import structured
from structured import (
    STOP_WORDS,
    StructuredLedger,
    TERM_RE,
)


IDENTIFIER_TERM_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)+")


def _candidate_terms(value: str) -> frozenset[str]:
    """Baseline unigrams plus whole hyphen/underscore identifiers."""
    folded = value.casefold()
    unigrams = {
        term
        for term in TERM_RE.findall(folded)
        if term not in STOP_WORDS and not (term.isdigit() and len(term) == 1)
    }
    identifiers = set(IDENTIFIER_TERM_RE.findall(folded))
    return frozenset(unigrams | identifiers)


class CandidateStructuredLedger(StructuredLedger):
    """Ledger identical to ``StructuredLedger`` except for identifier tokens."""

    def _initialize_fts5(self) -> None:
        exists = self._connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'poc_record_terms'"
        ).fetchone()
        # ``ascii`` tokenizer with '-' and '_' as tokenchars keeps whole
        # punctuated identifiers intact through FTS5.
        self._connection.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS poc_record_terms USING fts5(
                terms, content='records', content_rowid='sequence',
                tokenize="ascii tokenchars '-_'"
            );
            CREATE TRIGGER IF NOT EXISTS poc_records_insert AFTER INSERT ON records BEGIN
                INSERT INTO poc_record_terms(rowid, terms) VALUES (new.sequence, new.terms);
            END;
            """
        )
        if not exists:
            self._connection.execute(
                "INSERT INTO poc_record_terms(poc_record_terms) VALUES ('rebuild')"
            )
            self._connection.commit()

    def _insert_record(
        self, record_id: str, context_id: str, record: dict, *, active: bool = True
    ) -> None:
        self._connection.execute(
            """INSERT INTO records
                (id, context_id, kind, value, source, source_ref, active, supersedes_id, terms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record_id,
                context_id,
                record["kind"],
                record["value"],
                record["source"],
                record["source_ref"],
                int(active),
                record.get("supersedes_id"),
                " ".join(sorted(_candidate_terms(record["value"]))),
            ),
        )

