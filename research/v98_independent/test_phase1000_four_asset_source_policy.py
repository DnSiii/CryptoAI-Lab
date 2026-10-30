"""V98 Phase1000 offline checksum/source parser and four-exception policy tests."""
import hashlib
import io
import unittest
import zipfile
from unittest.mock import patch
import phase1000_four_asset_source_policy as p


class Phase1000Tests(unittest.TestCase):
    def test_four_exception_sha_pins(self):
        self.assertEqual(set(p.MONTH_PINS), {"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"})
        self.assertEqual(len(set(p.MONTH_PINS.values())), 4)

    def test_official_zip_checksum_and_header(self):
        name = "ETHUSDT-1h-2023-02-24.zip"
        header = "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore\n"
        row = "1677196800000,100,101,99,100,0,1677200399999,0,0,0,0,0\n"
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w") as z:
            z.writestr(name[:-4]+".csv", header+row)
        raw = mem.getvalue()
        sha = hashlib.sha256(raw).hexdigest()
        def fake(base,url):
            return (sha+"  "+name).encode() if url.endswith(".CHECKSUM") else raw
        with patch.object(p, "download_from", side_effect=fake):
            rows, digest = p.official_rows(p.DAILY_BASE, "ETHUSDT", name)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "1677196800000")
        self.assertEqual(digest, sha)

    def test_checksum_mismatch_rejected(self):
        name = "BNBUSDT-1h-2023-02-24.zip"
        def fake(base,url):
            return ("0"*64+"  "+name).encode() if url.endswith(".CHECKSUM") else b"bad"
        with patch.object(p, "download_from", side_effect=fake):
            with self.assertRaisesRegex(ValueError, "VENDOR_CHECKSUM_MISMATCH"):
                p.official_rows(p.DAILY_BASE, "BNBUSDT", name)


if __name__=="__main__":
    unittest.main()
