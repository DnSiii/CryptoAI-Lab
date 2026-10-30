from __future__ import annotations

import run_candidate_v99 as runner

from cryptoai_v13.v99_r4 import V99R4ControlSpec, asymmetric_v99_targets_r4


# Reuse the mature reporting/gating framework while swapping only the candidate
# transform under test. The compatibility key remains named r3_control inside
# the shared runner, but its schema is V99R4ControlSpec in this execution.
runner.V99R3ControlSpec = V99R4ControlSpec
runner.asymmetric_v99_targets_r3 = asymmetric_v99_targets_r4


if __name__ == "__main__":
    runner.main()
