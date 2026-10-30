# V98 Independent Phase241 — accounting caveats (pre-results, 2026-10-07)

This is a pre-performance static accounting note, not a new hypothesis or a change to the frozen Phase241 grid or promotion gates.

The evaluator computes max drawdown as equity divided by cumulative maximum of observed equity. Since initial capital 1.0 is not included in the running maximum, an immediate loss at the first measured bar is omitted from max drawdown. A correct supplemental audit should prepend initial equity 1.0; this is diagnostic and must not silently relax any gate.

The evaluator reports bull/bear/sideways positive-day fractions by selecting hours first and then resampling the selected hourly series to calendar days. This can count calendar days with no observations in the selected regime as zero-return days, depressing the regime-specific positive-day fraction. Overall positive_days is not affected by this particular selection issue.

At fold ends, events initiated within a fold can hold positions past the fold boundary; the reported fold PnL and turnover mask excludes those subsequent bars, and no explicit forced-liquidation turnover is charged at the boundary. Report this boundary convention in stress diagnostics; do not retrofit a different convention after seeing performance.

These caveats must be evaluated on synthetic fixtures independently of 2026+ holdout or V99 evidence before interpreting any Phase241 decision-grade result. Frozen primary validator remains authoritative until a prospective, explicitly documented protocol decision; no post-result rescue or threshold changes.
