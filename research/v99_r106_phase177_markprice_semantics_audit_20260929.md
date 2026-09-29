# V99 R106 — Phase177 mark-price semantics / reconstruction audit

Date: 2026-09-29
Status: DATA/INTEGRITY only. No Phase177 PnL authorized.

## New evidence and implication

Deribit documents option mark price as a risk-system fair-value estimate, usually related to best bid/ask but subject to additional checks/bandwidths. Deribit also explicitly warns in its mark-price documentation that mark price should not be relied upon for trading decisions because stabilization can lag genuine market moves.

Therefore Phase177 must not treat option mark price itself as a directly tradable price or execution proxy. Its only admissible role is as an exchange-published input for reconstructing a volatility-state feature, provided historical point-in-time availability is proven.

## Failure mechanisms to measure before alpha

1. **Smoothing / latency contamination** — exchange risk smoothing may attenuate or delay volatility shocks. Coverage alone is insufficient; timestamp age and update cadence must be reported.
2. **Sparse/stale contract marks** — an option can retain an apparently valid mark while the underlying surface has moved. Staleness must be measured per instrument and per surface timestamp; no silent forward fill.
3. **Synthetic-forward dependence** — inverse-option IV uses a forward price; Deribit documents that when no matching future exists a synthetic future is used. Historical reconstruction must use only contemporaneously available forward/index fields and never current metadata.
4. **Settlement-window pathology** — expiry/settlement mechanics can distort Greeks/marks around 08:00 UTC. The data audit must separately report coverage and numerical failures around settlement rather than optimize an exclusion window after seeing returns.
5. **Cross-sectional survivorship** — strike/expiry choice must come from the contemporaneous listed universe. A hindsight list of instruments is forbidden.
6. **Tradability separation** — future alpha evaluation must apply the project's underlying execution/cost model; option marks cannot be counted as executable PnL.

## Additional deterministic diagnostics

Before any alpha specification, the canonical surface report must add:
- update-age distribution (p50/p90/p99/max) by month and temporal fold;
- fraction of contracts/surfaces unchanged across consecutive decision timestamps;
- ATM-bracket availability and width distribution;
- forward/index field availability and provenance;
- settlement-adjacent diagnostic bucket fixed ex ante as 07:30–08:30 UTC (diagnostic only, not an exclusion rule);
- call/put parity residual diagnostics where required inputs exist;
- cross-run identical canonical SHA-256.

## Decision

Phase177 remains NOT ADMITTED for alpha/PnL. The next admissibility step is proof of a first-party historical replay/archive covering the immutable TRAIN interval with point-in-time option mark/IV inputs. If that cannot be established, Phase177 is rejected at the data gate rather than rescued with third-party history or post-hoc parameterization.

V16 Frozen, V99 Frozen and holdout remain untouched.