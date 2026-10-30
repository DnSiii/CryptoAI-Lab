# V98 Independent Phase1184 — AC independent trade-level FIFO accounting preregistration

Date 2026-10-23, before complete Phase1182 economic receipts are available. This is a **read-only observer** for the frozen AC actual-open executor, not a change to AC signals, parameters, risk or fills.

## Contract
- Per asset, keep FIFO signed lots with entry quantity, entry actual-fill price, remaining entry fees and signed funding cash attributed while held. On partial close or long/short reversal, match old lots FIFO and allocate entry fees/funding pro rata to closed quantity. Allocate exit fees to closed quantity; any remainder becomes the entry fee of a new reversed lot.
- Closed trade net PnL = signed (exit actual fill - entry actual fill) x closed quantity - allocated entry fee - allocated exit fee + allocated funding cash. Report true trade-level Profit Factor, payoff and win rate; do not substitute daily gain/loss proxies.
- Funding cash for each asset at a settlement event is distributed across currently carried signed lots proportional to absolute units. Nonzero funding with no inventory fails closed. Entry/exit slippage is already included in actual-fill prices and must not be charged twice.
- At every hour, reconcile total closed-trade realized PnL + remaining open-lot mark-to-market PnL (including remaining entry fees and attributed funding) against the independent cash+inventory self-financing NAV delta, within fixed absolute tolerance 1e-6 per $10k initial capital scaled by initial capital. Any discrepancy is a hard accounting failure, not a rescue.
- Preserve exact 2023 and 2024 fold boundaries; open positions crossing the fold remain open, not fictitiously closed. Report realized and unrealized components separately and avoid labeling partial-fold realized PF as complete economic PF without the open-lot disclosure.
- All tests are synthetic first: partial close, reversal, long/short, zero inventory, fee/funding allocation, open lots, trade-level PF and reconciliation. Do not inspect 2025, external V14/V15/V99 or change frozen AC code.

## Decision
If the economic AC candidate fails Phase1183, retain this FIFO implementation only as independent accounting infrastructure; **do not** use it to rescue the rejected candidate. If AC passes all other gates, use it for independent read-only trade-level audit before any promotion or validation.
