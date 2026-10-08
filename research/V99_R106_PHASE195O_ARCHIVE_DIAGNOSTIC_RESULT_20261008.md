# Phase195-O result and source-selection correction

GitHub Actions run 37842081363: 11 deterministic synthetic controls passed. EthStaker and ChainSafe each returned HTTP 404 for both the finalized-header control and the fixed historical-header query. The preceding Phase195-N historical block HTTP 500 results therefore cannot be attributed specifically to pruning of old history; the endpoint service/capability itself was not demonstrated.

The community checkpoint-sync registry marks both operators as State and Verification providers, but NOT Block providers. These were unsuitable for the historical-block objective. Do not promote any result or infer cryptographic mismatch from the transport failures.
