# V99 R106 — Phase177 DVOL endpoint audit

Date: 2026-09-28
Scope: independent DATA/CAUSALITY audit; no PnL.

## Finding

First-party Deribit API change logs show that Deribit Volatility Index instruments were added to the market-data interface (historically BTC-VIX / ETH-VIX; later renamed BTCDVOL_USDC-DERIBIT-INDEX / ETHDVOL_USDC-DERIBIT-INDEX). This independently confirms that DVOL was a published market-data object, not a retrospectively manufactured research series.

Current public API documentation was searched for a dedicated historical volatility-index endpoint. The inspected documentation did not establish a first-party historical DVOL time-series endpoint with guaranteed full frozen-TRAIN coverage. Therefore Phase177 may not treat present-day DVOL availability as proof of retrievable historical point-in-time DVOL observations.

## Anti-lookahead consequence

The safest admissible path remains reconstruction from first-party historical option instruments/trades only if the separately preregistered reconstruction/data gate can prove all required contemporaneous inputs. A modern DVOL value or partner backfill cannot be used to fill historical gaps.

## Decision

Phase177 remains NOT ADMITTED for PnL. The evidence now establishes three distinct provenance facts: (1) DVOL existed before TRAIN, (2) it was published as exchange market data, and (3) Deribit provides first-party historical option trade/instrument endpoints. What remains unresolved is a deterministic, complete historical IV-state reconstruction with all contemporaneous inputs and integrity manifests.

No holdout access. No formula tuning. No changes to V16 Frozen or V99 Frozen.
