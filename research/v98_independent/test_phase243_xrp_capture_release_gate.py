"""V98 Phase243: preregistered XRP publisher-sidecar capture release gate.

DATA_ONLY. Fails on the currently known double-escaped checksum pattern.
Never opens holdout, downloads market data, or changes trading parameters.
"""
import unittest
from pathlib import Path
import phase243_xrp_source_capture as capture


class XRPSourceCaptureReleaseGate(unittest.TestCase):
    def test_module_anchored_namespace(self):
        self.assertEqual(capture.ROOT, Path(capture.__file__).resolve().parent)
        self.assertIn('v98_independent', capture.ROOT.parts)

    def test_actual_provider_sidecar_syntax(self):
        name = 'XRPUSDT-1h-2023-11.zip'
        sha = '29b7a4a3b9360f7b3be131af6b1fd619f18e7344eea99b5c964e955e667027a7'
        for sep in ('  ', ' *'):
            line = (sha + sep + name + '\n').encode()
            match = capture.CHECKSUM.fullmatch(line)
            self.assertIsNotNone(match, 'publisher checksum syntax rejected')
            self.assertEqual(match.group(1).decode().lower(), sha)
            self.assertEqual(match.group(2), name.encode())

    def test_wrong_checksum_basename_rejected(self):
        line = (('a' * 64) + '  BTCUSDT-1h-2023-11.zip\n').encode()
        match = capture.CHECKSUM.fullmatch(line)
        self.assertIsNotNone(match)
        self.assertNotEqual(match.group(2), b'XRPUSDT-1h-2023-11.zip')


if __name__ == '__main__':
    unittest.main()
