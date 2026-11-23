"""Integration contract tests only; do not constitute economic validation."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research.v98_independent.v98_c27_verified_kernel_integration import replay_verified_inputs

class IntegrationTests(unittest.TestCase):
    def test_digest_rejected_before_market_read(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as tmp:
            root=Path(tmp)/"v98_independent"
            root.mkdir()
            state=root/"checkpoint.json"
            state.write_text("{}")
            with patch("research.v98_independent.v98_c27_verified_kernel_integration.prepare") as prepare:
                with self.assertRaisesRegex(ValueError,"DIGEST"):
                    replay_verified_inputs(root,root/"receipt.json",state,"0"*64)
                prepare.assert_not_called()

    def test_verified_input_is_not_promotion(self):
        with tempfile.TemporaryDirectory(prefix="v98_independent_") as tmp:
            root=Path(tmp)/"v98_independent"
            root.mkdir()
            state=root/"checkpoint.json"
            state.write_text(json.dumps({"example":"unattested"}))
            digest=hashlib.sha256(state.read_bytes()).hexdigest()
            package={"source_gate":{"hours":2},"bars":{"x":[]},"funding_by_hour":{"x":{}}}
            with patch("research.v98_independent.v98_c27_verified_kernel_integration.prepare",return_value=package), patch("research.v98_independent.v98_c27_verified_kernel_integration.continue_replay",return_value={"final_equity":123.}) as kernel:
                out=replay_verified_inputs(root,root/"receipt.json",state,digest)
                self.assertFalse(out["economic_replay_allowed"])
                self.assertIn("UNATTESTED",out["status"])
                kernel.assert_called_once()

if __name__=="__main__":
    unittest.main()
