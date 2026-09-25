# V98 Independent Phase140 — governing full PIT decision

Status: **PASS_PIT_DATA_ONLY**.

The governing ALFRED point-in-time audit passed before any admissible Treasury-curve economic result was inspected.

Evidence:
- frozen series: T10Y2Y;
- 783 expected weekday vintages across 2023-2025;
- 748 valid PIT observations;
- coverage: 2023 95.7692%, 2024 95.4198%, 2025 95.4023%;
- global coverage: 95.5300%;
- zero duplicate rows, malformed cells or future-value leaks;
- two independent complete acquisitions matched exactly on normalized PIT SHA-256, coverage, counts and integrity metadata;
- 66 batched ALFRED requests per full pass, two complete passes;
- no crypto data, return, correlation, direction, economic lookback, threshold, alpha or PnL was accessed by the gate.

The earlier month-end `PASS_PIT_SHORTCUT` remains supporting evidence only. This full audit is the governing authorization.

The premature Phase141 run remains VOID_PRECONDITION and inadmissible; its generated economic report was removed from branch HEAD without being opened for research selection.

Phase140 authorizes exactly one separately preregistered Treasury-curve economic hypothesis. Validation and all holdouts remain closed.
