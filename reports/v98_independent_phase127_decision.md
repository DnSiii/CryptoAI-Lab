# V98 Independent — Phase127 GSCPI DATA_ONLY decision

Decision: **FAIL_DATA_NO_ALPHA / CLOSED_NO_RESCUE**.

The preregistered Phase127 GSCPI gate executed on run 314. HTTP access itself succeeded, but the frozen required-column/schema gate failed; consequently there were 0 in-window rows, 0 finite rows, 0.0 finite coverage, and the >=34-row and >=95% coverage gates failed. Date-order, duplicate-date and malformed-date integrity checks remained clean because no observations were admitted.

Scientific handling is intentionally strict: numeric values were not exposed, alpha/PnL was not inspected, and there is no parser/source/schema substitution, alternate endpoint, manual extraction, interpolation, partial-era rescue, threshold relaxation, or retry-to-shop-for-a-pass. This exact GSCPI source/schema family is closed.

Isolation remained intact: validation and final holdout were not opened; V16, V99 and Phase083 were not used; no parameter search was performed. The V98 invariant suite passed 37/37 before the gate.

Next research must use a genuinely distinct preregistered family and begin DATA_ONLY before any alpha/PnL inspection.
