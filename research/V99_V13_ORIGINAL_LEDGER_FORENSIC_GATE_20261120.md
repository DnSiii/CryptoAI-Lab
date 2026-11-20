# V13 original ledger — forensic decision, 2026-11-20

Status: **FAIL CLOSED / NO PROMOTION**. This is a read-only research note; do not edit published ledgers.

## Evidence
- Failed original paper run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/42032849643
- Independent audit run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44747798630
- Audit artifact: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44747798630/artifacts/14634375640
- The independent audit classified 1,438 positive displayed adjustments without unrounded notional and one zero displayed adjustment without unrounded notional. The audit job ran and deliberately failed its provenance gate. **Missing raw values do not prove economic inconsistency.**
- The unresolved zero is BTCUSDT, 2026-11-04 19:00 UTC; an approximate 0.00223 BRL inferred from weights is not proof of executed notional.

## Exact code path to reconcile
In main:scripts/paper_continuation.py, `merge_ledger.scaled` rounds every numeric `*_brl` field to 2 decimals after multiplying by `factor = old.equity_curve[-1].capital_brl / segment.base_capital_brl`. Consequently `order_value_brl` loses subcent precision at serialization. This is a *mechanism hypothesis*, not proof of the original order amount. The PR #23 candidate must be checked against the original `segment` produced before `scaled`, with the same factor and cutoff.

## Required next execution and acceptance gates
1. On an isolated checkout of the exact failed-run code and original source artifacts, generate the unscaled continuation segment in a scratch directory. Capture the precise BTCUSDT order notional, its underlying turnover/position delta, segment base capital, factor, timestamp, and input digests. Do not overwrite published files.
2. Independently recompute `raw_brl = segment_order_brl * factor` with decimal-safe rounding and check `round(raw_brl, 2) == displayed_brl`, `0 < raw_brl < 0.005` for the zero row, and consistency with the executed turnover and positions. Reconcile all other newly generated rows; legacy rows without raw remain explicitly unproven.
3. Run original verifier plus adversarial tests (zero without raw, NaN, infinity, negative, raw/display mismatch, scale mismatch, missing hour, changed historical prefix) in Actions. Require a clean real paper refresh, a prefix hash match and explicit stale/research-only dashboard messaging before merge or publication.
4. Preserve immutable V16/V99 Frozen, legacy paper, train/validation/holdout. Never synthesize trades, place orders or promote a strategy from CI success.

Research architecture I1 remains blocked by missing licensed original Deribit option history (658/661 days). D1 and C1 are rejected. No profitable V99 has been independently validated.
