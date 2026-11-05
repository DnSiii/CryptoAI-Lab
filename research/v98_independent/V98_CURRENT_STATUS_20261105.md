# V98 Independent — current decision status (2026-11-05)

## What is no longer blocking the project

AJ is not waiting for exact markPrice to learn whether it works. The frozen AJ1261 historical economic run already executed on authenticated 2023-2024 Clean-4 data.

All ten per-path/per-OS training jobs succeeded and all 18 cells per path survived mechanically. The parent run concluded failure only because the first reconciliation tolerance rejected a tiny cross-OS turnover delta (~6.4e-5 USD on ~7.86m USD turnover) before producing its summary.

The preserved AJ_full receipt itself is economically negative:
- USD10k BASE carried-before-fill 2023: +0.4930%
- 2024: -56.0752%
- combined net return: -55.8586%
- two-year CAGR: -33.5425%
- max drawdown: 67.1368%
- hourly PF: 0.9369

Therefore AJ is not a candidate for live or paper deployment and must not be described as awaiting only exact funding marks.

Subsequent complete architectures AK through CH were also frozen and historically rejected under their own preregistered gates.

## Best surviving partial architecture

Phase252 remains the best non-rejected V98 partial candidate:
- 2023-2025 BASE return +550.57%
- CAGR 86.66%
- daily PF 1.2169
- max drawdown -52.64%
- severe return +493.66%
- supersevere return +408.80%
- 2023 +281.17%
- 2024 +83.46%
- 2025 -8.36%

Phase252 is not a complete final V98 and is not validated for live money.

## Forward paper start

A quarantined Phase252 forward-paper contract and agent were frozen on 2026-11-05:
- v98_phase252_forward_paper_prereg_20261105.md
- v98_phase252_forward_paper.py
- V98_PHASE252_FORWARD_PAPER.md

Forward paper results are observation-only and forbidden as V98 model-selection feedback.

The exact feed uses only official Binance USD-M /fapi/v1/klines and /fapi/v1/fundingRate. Hosted GitHub runners currently receive HTTP 451 from the required futures REST API. The agent therefore fails closed and never switches provider/host. It can run immediately on a lawfully authorized network or self-hosted runner.

## Research direction

Continue building a genuinely superior complete V98. Do not wait on AJ. Do not use rejected AK-CH architectures as rescue candidates. Keep Phase252 as provisional paper-only reference while final V98 research continues independently.
