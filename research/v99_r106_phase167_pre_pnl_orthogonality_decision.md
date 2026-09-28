# V99 R106 Phase167 — pre-PnL orthogonality decision

## Decision
Phase167 may complete strictly as a **DATA-only source audit**, but it is **not eligible to open a Phase168 cross-venue OHLC alpha**.

## Independent audit finding
After preregistration/implementation, the branch-wide research inventory was re-audited and surfaced two prior constraints that must dominate the new idea:

- Phase136/137 already introduced cross-venue OKX/Binance price-dislocation research.
- More importantly, `v99_r106_phase149_157_crossvenue_ohlc_family_closeout.md` explicitly closes the cross-venue OHLC family after the Phase149–157 sequence.

Coinbase is a new venue/source, but changing the venue does **not** make OHLC dislocation a scientifically distinct mechanism. Treating it as a fresh alpha family would violate the anti-overfit/anti-busywork standard.

## Consequence
- The Phase167 workflow is allowed to finish because it computes **no PnL** and can add reusable source-quality evidence.
- Regardless of PASS/FAIL_DATA_ONLY, **no Coinbase-vs-Binance OHLC alpha, threshold rescue, sign flip, lookback search, or Phase168 PnL is authorized from Phase167**.
- `pnl_computed=false`, holdout construction/selection remain 0/0.
- V16 Frozen and V99 Frozen remain untouched.
- Next alpha work must move to a genuinely orthogonal information family, not merely another venue carrying OHLC.

This decision is recorded before any Phase167/168 PnL and therefore cannot be conditioned on the DATA result.
