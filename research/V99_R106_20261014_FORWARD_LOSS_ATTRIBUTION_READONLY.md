# V99 / V16 — read-only forward loss attribution (2026-10-14)

**Scope:** forensic analysis only, never a new economic selection trial. V16 Frozen and V99 Frozen unchanged; untouched final holdout not opened. No production paper ledger altered. The forward observations below are not authorized as TRAIN for parameter tuning, promotion, or cherry-picking.

## Evidence and cutoffs

- Official GitHub Actions run `38584300742`, archived artifact `11904489960` (`paper-v13-opportunities-38584300742`).
- Archive SHA256 independently recomputed: `e48ec817a4ec2fa68391a4b6b733bb1282adfc537764a758cfebd0a36af11a44`, matching GitHub artifact digest.
- Individual ledgers from the ZIP: `reports/paper_v99_ledger.json` and `reports/paper_v16_ledger.json`; paper only, no real orders. Economic close: **2026-10-14T13:00:00Z**.
- V99 own original paper boundary: `2026-09-06T22:00:00Z`. Its 903 subsequent hourly returns are analyzed without modification. V16's original paper boundary is earlier, so matched-window comparisons independently rebase V16 at the exact V99 boundary rather than comparing lifetime ROI.

## Quantified failure

- V99 initial simulated BRL 10,000.00 → **8,525.60**; **−14.744% / −BRL 1,474.40**, observed peak BRL 10,205.76; max observed drawdown from that peak **−16.692%**.
- V99 negative hours **487/903** and positive hours **416/903**. **21 negative days out of 39 UTC calendar days** in the sample.
- Worst five UTC day contributions: Sep 23 **−BRL 592.14**; Oct 5 **−BRL 482.30**; Sep 15 **−BRL 415.22**; Sep 7 **−BRL 360.03**; Oct 13 **−BRL 295.43**. They sum to **−BRL 2,145.12**; other days together contributed roughly **+BRL 670.77**. Consequently the loss is mainly *tail concentration*, not a steady small hourly leak.
- Ten worst hourly results sum to **−BRL 1,995.41**, while all other hours together contribute roughly **+BRL 521.06**. Largest V99 hour: **2026-09-23T15:00Z −BRL 256.81 (−2.638%)**, second largest **2026-10-05T14:00Z −BRL 248.81 (−2.691%)**.
- V99 and V16 same-window hourly return Pearson correlation is **0.99876** (903 matched hours); V99 **−14.744%** vs V16 **−15.346%** normalized from the same starting timestamp. The small V99 benefit does not establish a robust edge, only near-identical risk structure.
- Same-period reference returns (rebased to 2026-09-06T22:00Z, descriptive only, no selection): V13 **−5.505%**, V14 **−8.204%**, V15 **−6.821%**, V16 **−15.346%**, V99 **−14.744%**. Different legacy strategies/capital states remain; this is NOT a validated benchmark envelope.

## Mechanism and limitations

1. V99 Frozen composes a V16-derived **Core** with a consensus-gated **satellite capped at 10%** (`FROZEN_MAX_SATELLITE=0.10`) and **720-hour/30-day** rebalance (`src/cryptoai_v13/v99_frozen.py`). This architecture explains the near-unity correlation: it is structurally dominated by V16. It is not a separate hedge.
2. V16 published ledger decision at **2026-10-05T13:00Z**, preceding a severe losing hour, has `new_weight` **+0.2586 BTCUSDT, +0.8483 ETHUSDT, +0.6481 SANDUSDT**. These three alone represent ~**1.755 gross long weight**, permissible under a 2.0 gross guard but vulnerable to a correlated selloff. V99 suffered a nearly identical next-hour loss, **−BRL 248.81** vs V16 **−BRL 251.08**. These are decision snapshots, not a full per-asset PnL oracle.
3. V16 original full-window ledger decomposition: **gross PnL −BRL 1,158.66**, fees **BRL 225.87**, negative funding **BRL 29.23**, costs **BRL 255.10**, net **−BRL 1,413.76**. Thus market PnL explains ~82% and transaction/funding costs ~18% of its net loss. These figures are **V16**, not an invented V99 cost attribution. In the exact matched V99 window, V16 gross **−BRL 1,343.30**, fees **BRL 183.69**, funding **−BRL 29.51**, net ~**−BRL 1,556.4**.
4. Published V99 ledger carries only aggregate `hour_result_brl` and no independent per-hour gross, fees, funding or sleeve-transfer breakdown. A V99-specific attribution **cannot** be verified yet.
5. The V16 risk guard is a **temporary cooldown**, not a permanent max-drawdown hard stop. Under `src/cryptoai_v13/backtest.py`, after the configured cooldown expires, `peak_equity` resets to current equity. V99 parent uses a 5.8% threshold, 0.1 exposure multiplier and 72-hour cooldown; the satellite uses a shorter separate guard. This explains why multiple drawdowns can accumulate beyond 5.8% over a long forward window. Its effectiveness under shocks remains to be stress-tested; no bug conclusively established here.
6. Source provenance remains problematic in ongoing V99 Phase195. A GitHub artifact SHA256 is byte-integrity proof, not exchange timestamp authentication. Following the paper continuity migration, an internally consistent published paper curve is not equivalent to independently tradable PnL.

## Scientific decision

**Reject any claim that current V99 Frozen is better than V16 merely because of its historical backtest or tiny matched-paper delta.** No promotion. Do not change either frozen engine; do not optimize parameters on this forward window.

Propose a **distinct TRAIN-only preregistration** to challenge the high-exposure, correlated-shock mechanism: validate a separate, causal risk-governor and regime-loss hypothesis with strict t−1, independent PIT receipts, fold stability, severe/supersevere costs, 3×2 regime matrix, benchmark envelope, worst-hour concentration and peak-to-trough drawdown. Compare it to the original frozen configuration as a locked external benchmark, never use these forward dates to select settings. Require a native V99 sleeve-level independent funding/fees/transfer PnL audit before claiming alpha attribution.

**No investor money was touched; all measured losses in this document belong to PAPER_ONLY simulated tracks.**
