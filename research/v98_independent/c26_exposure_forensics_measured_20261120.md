# C26 — measured exposure failure, authenticated artifact (2026-11-20)

Evidence: [GitHub Actions run 44690686823](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44690686823), artifact ID `14607914061`, SHA-256 digest `6644bbaa363312fca5430b8b0549ab9bb4606a3138b8e98291135c81c9cc54f1`. Downloaded ZIP and independently streamed all 27,047 JSONL rows for each of 1x, 2x, 4x. No holdout access.

| Cost scenario | pre-fill rows >40% asset | post-fill rows >40% asset | max pre-fill asset | max post-fill asset | rows >90% total | off-calendar trades |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1x | 560 | 557 | 45.2547% | 45.2547% | 0 | 0 |
| 2x | 560 | 557 | 45.2547% | 45.2547% | 0 | 0 |
| 4x | 560 | 557 | 45.2547% | 45.2547% | 0 | 0 |

First offending index: 7850, 40.5412% single asset, 58.6958% aggregate. Maximum pre-fill aggregate 59.9199%, post-fill 59.7997%. The 557 post-fill breaches are not false positives from a momentary intrabar mark: the weekly buy-and-hold schedule carries excess asset weight after the hourly fill boundary. The result is independent of cost scale because weight drift is driven by the same price/funding path.

**Decision:** C26 remains REJECTED. Do not alter C26 to rescue it. These figures are forensic exposure counts, not audited profit. Next: implement separately preregistered C27 with a causal two-clock safety governor and independently prove post-fill limits, including gap behavior, before economic promotion.
