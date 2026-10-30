# V98 Independent Phase1236 — AH signed volatility-expansion opportunity prereg (2026-10-23)

Separate AH Opportunity Sleeve, no import of rejected AG/AD/AE/AF signals. At completed close t, compute per-asset hourly log-return RMS over prior **12h** and **96h** (including completed bar t). A new event is eligible only if RMS12 > **1.4 x** RMS96. Direction is +1 only if close[t] > max(high[t-24:t]); -1 only if close[t] < min(low[t-24:t]); otherwise no event. Both ranges exclude current-bar high/low, and t's close is usable only at t+1 open.

On event, set a fixed **12-completed-hour** signed holding state; a later opposite event may reverse the state only if its independent criteria hold. Decay to zero after 12h without event. Normalize signed output by absolute gross across Clean-4, without assigning leverage, funding or PnL. The eventual AH actual futures ledger will pay all fees, funding, slippage and margin. No 2025/2026, XRP, contaminated Phase083 or external benchmark access.

Precommitted tests: long/short positive controls, TTL expiry, future perturbation invariance, deterministic two-OS hashes, invalid geometry fail-closed. No post-result threshold/window/fixture rescue; complete seven-slot structural gate controls promotion.
