from __future__ import annotations

import run_candidate_v99 as runner

from cryptoai_v13.v99_r4 import V99R4ControlSpec
from cryptoai_v13.v99_r5 import asymmetric_v99_targets_r5


runner.V99R3ControlSpec = V99R4ControlSpec
runner.asymmetric_v99_targets_r3 = asymmetric_v99_targets_r5


if __name__ == "__main__":
    runner.main()
