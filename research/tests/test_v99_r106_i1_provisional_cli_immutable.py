"""Adversarial publication controls only; no original economic TRAIN evidence."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_original_to_provisional_numeric import main


class ProvisionalCLIImmutablePublication(unittest.TestCase):
    def args(self, directory):
        return ("missing-signal.json", "missing-quotes", "missing-journal.json",
                str(Path(directory) / "report.json"))

    def report(self):
        return {
            "status": "PROVISIONAL_ORIGINAL_BBO_ONLY_NOT_NATIVE_ECONOMICS",
            "original_quote_event_identities_checked": 2,
            "original_options_economic_train_certified": False,
            "promotion_authorized": False,
            "orders_enabled": False,
        }

    def assert_no_temp(self, root):
        self.assertEqual(list(Path(root).glob(".v99-i1-provisional-*.tmp")), [])

    def test_existing_result_blocks_source_execution_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            args = self.args(root)
            Path(args[-1]).write_bytes(b"original-preserved")
            with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.run") as source:
                with self.assertRaisesRegex(ValueError, "EXISTING_PROVISIONAL_RESULT_IMMUTABLE"):
                    main(*args)
                source.assert_not_called()
            self.assertEqual(Path(args[-1]).read_bytes(), b"original-preserved")

    def test_dangling_symlink_blocks_source_execution(self):
        with tempfile.TemporaryDirectory() as root:
            args = self.args(root)
            target = Path(args[-1])
            target.symlink_to(Path(root) / "nonexistent")
            with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.run") as source:
                with self.assertRaisesRegex(ValueError, "EXISTING_PROVISIONAL_RESULT_IMMUTABLE"):
                    main(*args)
                source.assert_not_called()
            self.assertTrue(target.is_symlink())

    def test_serialization_failure_never_creates_partial_report(self):
        with tempfile.TemporaryDirectory() as root:
            args = self.args(root)
            with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.run",
                       return_value={**self.report(), "bad": object()}):
                with self.assertRaises(TypeError):
                    main(*args)
            self.assertFalse(Path(args[-1]).exists())
            self.assert_no_temp(root)

    def test_disk_failure_removes_temporary_and_preserves_destination(self):
        with tempfile.TemporaryDirectory() as root:
            args = self.args(root)
            with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.run",
                       return_value=self.report()):
                with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.os.fsync",
                           side_effect=OSError("simulated disk error")):
                    with self.assertRaisesRegex(OSError, "simulated disk error"):
                        main(*args)
            self.assertFalse(Path(args[-1]).exists())
            self.assert_no_temp(root)

    def test_racing_writer_wins_and_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as root:
            args = self.args(root)
            actual_link = os.link
            def racing_link(source, destination):
                Path(destination).write_bytes(b"other-writer")
                return actual_link(source, destination)
            with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.run",
                       return_value=self.report()):
                with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.os.link",
                           side_effect=racing_link):
                    with self.assertRaisesRegex(ValueError, "EXISTING_PROVISIONAL_RESULT_IMMUTABLE"):
                        main(*args)
            self.assertEqual(Path(args[-1]).read_bytes(), b"other-writer")
            self.assert_no_temp(root)

    def test_success_atomic_provisional_only_and_new_parent(self):
        with tempfile.TemporaryDirectory() as root:
            args = list(self.args(root))
            args[-1] = str(Path(root) / "new" / "report.json")
            with patch("research.tools.v99_r106_i1_original_to_provisional_numeric.run",
                       return_value=self.report()):
                result = main(*args)
            self.assertEqual(result, self.report())
            self.assertEqual(json.loads(Path(args[-1]).read_text()), self.report())
            self.assertFalse(result["original_options_economic_train_certified"])
            self.assertFalse(result["promotion_authorized"])
            self.assert_no_temp(Path(args[-1]).parent)


if __name__ == "__main__":
    unittest.main()
