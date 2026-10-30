#!/usr/bin/env python3
"""Y Phase1136 pre-freeze safety: synthetic-only, no historical access."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import phase1136_y_frozen_training_path as p

class TestY1136(unittest.TestCase):
    def test_freeze_is_mandatory_before_source(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(p,'MANIFEST',Path(td)/'missing.json'):
                with self.assertRaises(FileNotFoundError):p.verify_freeze()
    def test_git_blob_digest(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'fixture.py';f.write_bytes(b'alpha')
            expected=hashlib.sha1(b'blob 5\x00alpha').hexdigest()
            self.assertEqual(p.blob_sha(f),expected)
    def test_only_v98_frozen_code(self):
        self.assertTrue(all(name.startswith('phase') and '_y_' in name
            or name=='phase1070_s_typed_native_mark.py'
            for name in p.FROZEN_FILES))
    def test_no_unregistered_path(self):
        with self.assertRaisesRegex(ValueError,'UNREGISTERED_PATH'):
            p.run('Y_tuned_after_pnl')
if __name__=='__main__':unittest.main()
