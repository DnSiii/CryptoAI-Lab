# Phase195-N prereg — historical beacon archive availability (fixed providers)

Phase195-M run 37836363044: 5 synthetic controls passed, but Publicnode beacon returned HTTP 403 for the fixed TRAIN slot. This is transport HOLD, not a consensus mismatch.

Before probing, freeze two alternate consensus operators listed in the community checkpoint-sync registry: EthStaker (beaconstate.ethstaker.cc) and ChainSafe (beaconstate-mainnet.chainsafe.io). Probe each exactly once for the SAME slot derived from the independently verified execution header at height 17,000,000; do not shift slots or select by outcome. Record HTTP status, reported finalized/optimistic flags, and execution payload block hash/root parity when available. A successful provider response is still unanchored and not a cryptographic consensus proof. All results DATA_ONLY, zero economic trials, no holdout or Frozen modifications, no promotion.
