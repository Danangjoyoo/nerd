# Writing for Google Sheets

## Use When

The document is a register, requirements matrix, test case catalog, comparison,
or tracked evidence set. Keep narrative decisions in a short overview tab or
linked document. A spreadsheet should make records easier to inspect, filter,
and maintain, rather than reproduce pages of prose inside cells.

## Design the Workbook

1. Define what one row represents, such as one requirement or one test case.
2. Give each record a stable ID and each column one clear meaning.
3. Separate editable inputs, derived values, and evidence references.
4. Define status vocabulary, units, date conventions, and blank-cell meaning.
5. Place the key counts or blockers first, followed by the detailed register.

Use descriptive tab names, a single header row per register, and consistent
types. Freeze headers for long registers and use filters for lookup. Avoid
merged cells in a data region, repeated mini-tables, or color-only status.
Use wrapped text for short notes; link long explanations rather than hiding
multiple requirements in a single cell.

## Example: Test Documentation Workbook

Fictional workbook structure:

| Tab | Purpose | Row meaning |
| --- | --- | --- |
| Overview | Scope, environment, status key, release blockers | Summary item |
| Cases | Reproducible cases linked to requirements | One test case |
| Runs | Actual execution evidence | One case run in one environment/build |

Example `Cases` tab:

| Case ID | Requirement | Scenario | Preconditions | Expected result |
| --- | --- | --- | --- | --- |
| TC-01 | R1 | Administrator requests CSV | Administrator in account A | Accepted job belongs to account A |
| TC-02 | R2 | Viewer requests CSV | Viewer in account A | Access denied; no job created |
| TC-03 | R3 | Expired link is opened | Ready job with expired link | No file content returned |

Example `Runs` tab:

| Run ID | Case ID | Build | Environment | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| RUN-01 | TC-01 | export-demo-12 | staging-demo | Passed | Demo evidence log E1 |
| RUN-02 | TC-02 | export-demo-12 | staging-demo | Blocked | Demo fixture unavailable |
| RUN-03 | TC-03 | export-demo-12 | staging-demo | Not run | None yet |

Define statuses: `Not run`, `Passed`, `Failed`, `Blocked`. A blocked or unrun case
is never a pass. Real evidence cells should contain actual retrievable links;
the rows above are illustrative and do not establish test results.

## Formulas and Data Quality

- If formulas are needed, document what each summary measures and its range.
  For the example status column, `=COUNTIF(Runs!E2:E1000,"Failed")` counts failed
  run records, not distinct failing cases. Label that distinction.
- Keep expected results separate from actual results; do not overwrite test
  definitions every time a run finishes.
- Do not convert missing values to zero or replace an unknown result with a
  success-looking blank. Use an explicit status or documented null convention.
- Preserve IDs and relationships when sorting. Validate ranges, formulas,
  duplicates, and relevant data types with the tools available.

## Delivery Check

Confirm tab roles, headers, row granularity, status meanings, links, and summary
consistency. Inspect formulas and rendered layout when producing a spreadsheet
file. Use the spreadsheet artifact skill for an actual workbook when available.

For unavailable native access, provide a requested workbook file or one clearly
labeled CSV/TSV per tab plus an overview. CSV does not preserve tabs, formatting,
or native validation; do not claim it does. Never claim a Sheet was created
without a confirmed platform write.

## Platform Reference

See Google's guidance on
[sorting and filtering](https://support.google.com/docs/answer/3540681?hl=en) and
[freezing rows and columns](https://support.google.com/docs/answer/9060449?hl=en).
Check current help before supplying UI-specific menu paths.
