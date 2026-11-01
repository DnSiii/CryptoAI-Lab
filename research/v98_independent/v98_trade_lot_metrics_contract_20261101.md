# V98 independent net-asset round-trip metrics — accounting contract (2026-11-01)

This is **infrastructure, not a trading candidate or proof of PnL**. The prior V98 complete-system receipts report hourly NAV profit factor/payoff/win rate, not trade-level statistics. A future complete candidate must additionally report an independently reconstructed trade definition.

A *trade* here is one **net asset position episode** from zero net quantity to flat or sign flip, with weighted-average entry, partial close realized price PnL, proportional one-way net turnover fee/slippage, and signed worst-side native funding cash attributed to the old or new position according to the predeclared funding order. At a sign flip the old episode closes and a new episode opens. Open episodes at sample end are excluded from closed-trade PF/payoff/win rate and marked separately. This is NOT a virtual-sleeve trade count, fill attestation, realized broker statement, exact markPrice settlement or live execution proof.

The independent audit must reconcile closed episode PnL + open marked PnL to final physical NAV minus USD10k, reconstruct all hourly net turnover costs and funding, and fail closed on mismatch. Closed PF = sum positive net episode PnL / abs(sum negative); payoff = average positive / abs(average negative); win rate = positive closed episodes / all closed episodes. No trades/zero losses -> null PF/payoff, never infinity. Future economic gates cannot be passed on synthetic tests alone. Existing rejected PU/PT/PS/PR outcomes remain frozen and may not be selected using these metrics.

Scope: only V98 Independent; no external benchmarks, 2026+ training, contaminated holdout, V16/V99 Frozen or paper.
