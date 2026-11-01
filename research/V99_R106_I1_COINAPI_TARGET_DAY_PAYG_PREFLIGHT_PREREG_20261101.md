# V99 I1 — fixed 2022-01-23 CoinAPI source listing decision (preregistered 2026-11-01)

**SOURCE PROCUREMENT ONLY; NO MARKET DATA, ROI, ORDERS OR PROMOTION.**

## Decisive vendor constraints, independently checked on 2026-11-01

Tardis official billing FAQ (https://docs.tardis.dev/faq/billing-and-subscriptions) explicitly says **no one-off date or instrument purchases**, **no custom exports**, and free historical samples only on the first UTC day of each month. A current free trial covers days 1–10 of the **previous month**, not our immutable 2022-01-23 target. Academic/Solo/Professional yearly subscriptions include 4 years; bank-transfer yearly invoices add 12 months; Business yearly includes all available history. In November 2026, a standard four-year yearly plan cannot cover the required 2021-12-09 TRAIN start. No payment is authorized; Tardis must not be described as offering a paid single-day sample.

CoinAPI's **official** Flat Files documentation (https://www.coinapi.io/products/flat-files/docs/ and https://www.coinapi.io/products/flat-files/docs/datasets/quotes) describes historical S3 `coinapi/T-QUOTES/D-YYYYMMDD/E-DERIBIT/` partitions and BBO/size with exchange and collector clocks. The official pricing (https://www.coinapi.io/products/flat-files/pricing) offers pay-as-you-go usage rather than a required annual subscription. **Neither historical 2022-01-23 Deribit BTC/ETH option file presence, completeness, actual price, original native size units nor lawful entitlement has been independently established.** Listing may itself consume usage credits; do not list without an existing authorized credential.

## Fixed ex-ante targeted technical probe (not an alpha search)

Preserve original source-feasibility target **Sunday 2022-01-23 UTC**, before fixed **Monday 2022-01-24 00:00 UTC** in TRAIN fold 1, and fixed 28–35-day two-put same-expiry structure. Do not choose another day after inspecting any new source bytes. Add a read-only authenticated CoinAPI S3 **LIST-only** target preflight. It must enumerate the exact `T-QUOTES/D-20220123/E-DERIBIT/` prefix with pagination bounded to 20 x 1000 objects, validate returned object keys, nonnegative byte sizes and continuation tokens, and separately count filenames matching BTC/ETH native put symbols. Never download quotes, use public/secret keys in output, invent coverage, or infer native lot units or economic viability from object names. Reject truncated, malformed, cross-exchange or unbound listings; no key means a precise external block.

The preflight's purpose is to determine whether a potentially cheaper **single-date, usage-priced** provider route exists before any full 661-day acquisition. Even a positive object inventory is **NOT** proof of 24h capture, all expiry/strike universe, synchronized two-sided original BBO/size, historical exchange/collector clocks, license, fee tier, settlement or profitability. Obtain written license and a small lawfully acquired original file with SHA256 and completeness/gap documentation before economic conversion. Reuse existing independent original-source and native accounting gates; no source retune.

**Standing decision:** SOURCE HOLD / NO PROMOTION. 658/661 original days absent and 0/180 option lifecycles economically certified. Preserve V16/V99 Frozen, champion, paper, dashboard, sealed validation and final holdout. No orders.
