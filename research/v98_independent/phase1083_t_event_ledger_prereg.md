# V98 Independent Phase1083 — T event-driven signed ledger preregistration (pre-economic)

T architecture already preregistered in Phase1080. This is an execution-contract specification **before any T PnL**. S's frozen alpha and source hashes remain untouched; mechanical signed 16-corner cash/margin oracle and chronological metrics can be reused read-only because they are risk/accounting infrastructure, not S trading signals.

At each open t, use only target[t-1], prior quote volume[t-1], prior shock envelope[t-1], and prior funding bound[t-1]. Execute signed LP only when **daily-latched target changes** or carried positions fail the pretrade 16-corner risk/funding-reserve check; otherwise hold inventory without hourly rebalancing. Never skip post-funding intrabar/close 16-corner checks. Funding settlement conservatively charges carried-before-fill or new-after-fill signed mark low/high; all costs and cash movements explicit. All 3 fees, 2 orders, 3 capacities remain preregistered. Any noncausal access, missing fold, unaccounted fee, breach or unreproducible target blocks/rejects without rescue.

Before historical PnL: synthetic zero-inventory, shock, funding-sign, no-trade, t-1 and capacity tests. Before economic run: repeat authenticated T source crossrunner attestation and freeze immutable T source+ledger+target manifest. No 2025+, XRP, Phase083, V14/V15/V99.
