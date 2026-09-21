# V98 Independent — Phase067 decision

Status: **REJECT_NO_RESCUE**

Phase067 was frozen before PnL as a 20-day cross-sectional realized-volatility defensive spread. The completed training execution failed the frozen gate decisively and validation remains closed.

Observed BASE training (2023-01-01 through 2025-12-31): total return -78.6544%, CAGR -40.2306%, max drawdown -83.2712%, daily Profit Factor 0.7612, payoff 0.7114, win rate 51.6895% (566 positive / 529 negative days). Chronological folds all failed: 2023 -61.0441%, PF 0.6402; 2024 -41.4207%, PF 0.7638; 2025 -6.2463%, PF 0.9734. Severe return -81.4912%; supersevere -85.1476%.

This is a scientific rejection, not an infrastructure failure. No inversion, lookback change, basket change, regime filter, gross change, threshold, cadence change, cost change, or other rescue is permitted for this frozen family. The high daily win rate alongside PF < 1 and payoff < 1 confirms adverse loss asymmetry rather than a near-pass. The improving yearly trajectory does not justify rescue because every frozen annual return/PF gate still failed.

Validation was not inspected. Final holdout 2026-08-01 through 2026-09-15 remains untouched. V99 and V16 were neither used for selection nor modified. Current V98 Independent champion remains none.
