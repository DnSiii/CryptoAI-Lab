# AR execution semantics correction — pre-economic review, 2026-10-23

**Status: PRE-ECONOMIC IMPLEMENTATION CORRECTION, NOT PERFORMANCE TUNING.**

Before opening any AR historical economic receipts or reconciliation, static inspection found a material mismatch between the preregistered event contracts and the executable allocator: Opportunity is specified as a 168-hour exposure and Stress/Recovery as 72-hour exposure, but the initial AR allocator rebalanced only every 336 hours. An event starting between epochs could be skipped, and a position opened at an epoch could persist beyond its contracted expiry. This is a genuine causal execution defect, not a signal/parameter failure.

The initial workflow run `40042298175` is **invalid for economic promotion**, regardless of any eventual PnL; its economic outputs must not be used to select or retune AR. At this correction decision only syntax/source causal checks and 18/18 mechanical survival of one path were observed, **no CAGR, annual PnL, sleeve marginal PnL, drawdown or economic comparison was read**.

**Single deterministic correction:** keep all AR source functions, windows, signs, portfolio priors, funding/cost assumptions, 336h scheduled epochs and risk governor unchanged. In addition to the scheduled epochs, trigger a real next-open rebalance whenever the completed-close Opportunity or Stress/Recovery source vector changes (event entry/expiry/recovery). The current completed-close signal is executed no earlier than the following actual opening. This honors the 168h/72h event clocks and accounts for every extra real turnover, fee and slippage in the unchanged signed ledger. No opportunistic performance-driven change permitted.

Freeze this corrected AR implementation before its first valid economic 90-cell run. Evaluate only the corrected run on authenticated 2023/24 Clean-4; both-OS 90/90 survival, base/severe yearly net log wealth and strictly positive yearly sleeve marginals remain unchanged gates. If fail, reject AR permanently; do not rescue. 2025/2026+, XRP, old holdout and V14/V15/V99 untouched; V16/V99 Frozen and paper unchanged.
