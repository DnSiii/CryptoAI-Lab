# V13 original-ledger reconciliation — 2026-11-21 19:49 BRT

Status: **FAIL CLOSED / NO PROMOTION**. This is a read-only analysis of GitHub Actions run 44937575061, artifact 14720735592 (SHA-256 artifact digest 11dacb99432f8f5d216b8f07c01e3375fb9a645ebaba3388a30ab928cdb9336f), using paper-results commit 9c16c06a305ce720621044070a84b229196bca39. Do not rewrite historical orders or treat simulated notional as exchange fills.

## Raw evidence

Artifact v13_discrepancy_triage.json reports: 1,425 missing raw notional, 280 mismatches, 3 matches, 1 subcent simulated notional. Per asset: BTC 681 missing raw / 140 mismatches / 1 match / 1 subcent; ETH 681 missing raw / 140 mismatches / 2 matches; SAND 28 missing; TRX 31 missing; XMR 4 missing. Maximum absolute differences BTC R$130.848460375646 and ETH R$188.888439346111.

First mismatch: decision 681, adjustment 1, ETHUSDT 2026-11-04T19:00:00Z, row hash a10cae09b407999c5918497250b9f0222d15d69df2efe525c55ab899f23c199b: shown R$7.81 vs raw R$7.7148818969287944 (R$0.095118 difference). Another: decision 693, adjustment 1, ETHUSDT 2026-11-06T01:00:00Z, row hash f68e4d7d84afb26320b653fece9525e17cb2d145310bc95029f7105c353bf24a: shown R$5636.99 vs raw R$5825.878439346111 (R$188.888439 difference). These are not cent rounding.

## New diagnostic inference (not yet root-cause proof)

The 280 mismatches are exactly 140 BTC and 140 ETH, all from 2026-11-04T19:00Z through 2026-11-21T16:00Z; earlier missing-raw rows cannot be retrospectively certified. The shown/raw ratios among mismatches range approximately 0.96552–1.28000, median 1.09543. This rules out a *single constant* conversion factor across all mismatches and suggests investigating time-varying notional normalization, capital/equity denominators, or generator revisions. Do not assume which is causal without provenance.

Current scripts/paper_once_v13.py computes order_value_brl and order_value_brl_unrounded from the same to_brl(asset_order_notional) expression. Current verifier correctly rejects non-cent-aligned raw/display pairs and zero amounts without strictly positive sub-half-cent raw evidence. Current generator logic alone does not establish historical provenance.

## Shortest safe next path

1. Retrieve original paper-results ledger and generator revision *at each affected timestamp*, plus exact data input and base_equity used for the run; compare independent reconstructed notional and source revision. Preserve SHA-256 and row identifiers.
2. Classify missing-raw as **unverifiable**, not automatically invalid or valid. Classify 280 mismatches as **inconsistent pending original evidence**, not subcent. Keep verifier failing and paper refresh quarantined.
3. If provenance proves a calculation bug, repair only forward calculation in a separate branch, run adversarial tests and GitHub Actions on historical input without rewriting published trades; publish a clearly labeled stale/research-only notice.
4. Keep V99 Frozen, V16 Frozen, validation/holdout, paper-results and legacy champion immutable. No orders, no promotion, no invented performance.
