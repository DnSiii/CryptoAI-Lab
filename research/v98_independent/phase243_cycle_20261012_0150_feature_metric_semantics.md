# V98 Independent — Phase243 2026-10-12 01:50 BRT (data-only)

Scope: research/v98-independent-zero; V98 Independent only; 2023–2025 training. No holdout, V16, V99, paper, strategy selection, or backtest.

## Orthogonal XRP sensitivity (original immutable November 2023 monthly archive)
SHA256 29b7a4a3b9360f7b3be131af6b1fd619f18e7344eea99b5c964e955e667027a7. The impossible 2023-11-14 11:00 UTC quote-volume hour (row 323) was compared, without changing the source, against three explicitly synthetic bounds: base volume times candle low/close/high. These are counterfactual sensitivity probes, NOT candidate repairs.

Reproducing the causal Phase241 shifted rolling log-volume median/MAD calculation within the 720-hour November archive:
- 168-hour window: 31/30/28 changed available feature values (low/close/high); earliest row 323, latest 357/357/350.
- 336-hour window: 136/133/131 changed available feature values (low/close/high); earliest available row 336, latest 471/468/466.
- No feature changed before the corrupted hour or beyond its causal rolling window.
- The 336-hour November-only computation lacks the October warmup, so these counts are NOT complete multi-month production impact or observed trades. No PnL inference is authorized.
- Independent pandas/NumPy cross-check agrees with the standalone median/MAD implementation.

## Metrics semantics
Independent synthetic invariants identify the need to include initial wealth=1 in drawdown, distinguish active regime days from calendar-span days, and represent undefined profit factors explicitly rather than a finite 999 sentinel. Synthetic two-positive-days-across-five-calendar-days example: positive-day rate 100% among active days versus 40% across the span. This does not re-score Phase240 or Phase241 historical PnL.

## GitHub operational audit
At branch SHA 5a1ccc0066bc6a9225a3b2030f23a880f65efe94, Phase243 source workflow contains no independent XRP daily capture job and its push trigger excludes phase243_xrp_source_capture.py. Latest source workflow run 38053620316 failed on 2026-10-10 at the impossible XRP row and preserved a rejected-source artifact. Proposed isolated V98-only capture job (monthly 1h + daily 1h/1m, immutable ZIPs + CHECKSUM + manifest, artifact upload even on failure) was blocked by safety checks; no commit or job launch.

## Reproducibility and decision
117 distinct local tests x four deterministic modes (PYTHONHASHSEED=1/777, normal/-O) = 468/468 passes, including 20 new tests. Original archive SHA verified; local-only code and logs retained in cycle package. Phase240 REJECT_FAMILY_NO_RESCUE; Phase243 BLOCKED_SOURCE; champion NONE. No 2026+ holdout read. Next: publish authorized isolated capture, obtain independent daily originals and funding provenance, adjudicate before any economic backtest; preserve severe/supersevere costs, chronology, tails, drawdown, PF, payoff, win rate, positive days, regimes, concentration and anti-overfit gates.
