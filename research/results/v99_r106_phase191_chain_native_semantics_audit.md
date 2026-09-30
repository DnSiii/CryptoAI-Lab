# V99 R106 — Phase191 chain-native stablecoin semantics audit

Scope: DATA_ONLY. No price, PnL, regime return, benchmark return, or holdout values inspected.

## Purpose

Audit the post-Phase190 proposal before any economic trial. The prior idea described stablecoin issuance/redemption as ERC-20 Transfer events involving the zero address. That representation is not portable across USDT and USDC and must not be used blindly.

## Ethereum / provenance facts

Ethereum JSON-RPC exposes historical logs by contract address/topics/block range through `eth_getLogs`, and block identifiers include `safe` and `finalized`. Historical block/receipt data are append-only chain records; finality can therefore be fixed ex ante and event-time provenance can be tied to block number/hash/timestamp.

## USDC Ethereum semantics

Canonical Ethereum USDC is the Circle FiatToken proxy at `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` (6 decimals). Circle's FiatToken design explicitly states that mint emits both `Mint(minter,to,amount)` and `Transfer(0x00,to,amount)`, while burn emits both `Burn(minter,amount)` and `Transfer(minter,0x00,amount)`. Thus zero-address Transfer decoding is valid for canonical USDC issuance/destruction, but native Mint/Burn events are the preferred semantic source and provide a cross-check.

## USDT Ethereum semantics — critical correction

Canonical Ethereum USDt is Tether's contract `0xdAC17F958D2ee523a2206206994597C13D831ec7`. Its historical TetherToken implementation changes `_totalSupply` inside `issue(uint)` / `redeem(uint)` and emits native `Issue(amount)` / `Redeem(amount)` events. It does **not** implement issuance/redemption by emitting ERC-20 zero-address Transfer events in those functions.

Therefore a generic `Transfer(from/to == 0x00)` collector would systematically miss canonical USDT issuance/redemption and create a false cross-token feature. This is a pre-PnL semantic rejection of that decoder, not an economic failure.

## Multi-chain boundary

Both issuers operate on multiple chains. Ethereum-only net mint/burn is not total global stablecoin supply change. For a first admissible trial, the feature may only be described as **Ethereum-native issuance/redemption flow**, not global issuance, global liquidity, or aggregate stablecoin supply. Cross-chain burn-and-mint can also represent relocation rather than fiat creation/redemption, especially for USDC; interpretation must remain venue-specific.

## Admission decision

PASS only for a corrected DATA_ONLY collector with token-native event semantics:

- USDC: decode native `Mint` and `Burn`; independently reconcile amounts/counts against zero-address `Transfer` events over sampled finalized block windows.
- USDT: decode native `Issue` and `Redeem`; zero-address Transfer is not the issuance/redemption source.
- Persist block number, block hash, transaction hash, log index, contract address, event type, raw amount and block timestamp.
- Fixed finality rule before economics; no current token metadata may decide historical inclusion.
- Detect duplicate `(blockHash, txHash, logIndex)` records and fail closed.
- Fail closed on proxy/implementation or contract migration ambiguity.
- Do not access price/PnL/holdout during source audit.

No Phase191 economic rule is preregistered yet. First execute the corrected provenance/coverage collector on TRAIN-era block windows and demonstrate deterministic decoding/reconciliation. Only then may one frozen hypothesis be registered before PnL.

## Multiple-testing ledger

Stablecoin economic trials remain at zero. Phase190 failed source PIT provenance; this audit corrected Phase191 source semantics before economics. No hidden PnL trial has occurred.
