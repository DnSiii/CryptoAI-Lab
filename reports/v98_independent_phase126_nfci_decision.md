# V98 Independent — Phase126 NFCI decision

Decision: **FAIL_DATA_NO_ALPHA / CLOSED_NO_RESCUE**.

Run #312 completed successfully at workflow level, but the preregistered DATA_ONLY gate failed before any numeric series values, alpha, correlation, returns, or PnL were inspected. The fetch did not satisfy HTTP 200, required columns, minimum 150 in-window rows, or >=95% finite coverage. Integrity evidence contained zero in-window rows and the empty-manifest SHA256.

Scientific handling: close the NFCI family under the preregistered no-rescue rule. Do not retry with alternate endpoint, timeout, parser/column adaptation, interpolation, fill, or transformed NFCI proxy. A source/infrastructure failure is not evidence against the economic hypothesis, but changing the acquisition contract after observing the failed gate would be a retrospective rescue.

Isolation remained intact: validation and final holdout unopened; V16 and V99 unused; Phase083 unused; no parameter search. The V98 invariant suite passed 37/37 immediately before the gate.

Champion status: none.
