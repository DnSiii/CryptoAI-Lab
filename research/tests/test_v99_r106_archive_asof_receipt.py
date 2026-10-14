"""Fail-closed Binance Vision archive receipts: synthetic zipped OHLCV, no networking."""
from __future__ import annotations
import copy
import hashlib
import io
import zipfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from research.tools import v99_r106_archive_asof_receipt as m

DAY=(datetime.now(timezone.utc)-timedelta(days=2)).strftime("%Y-%m-%d")
SYMBOL=m.SYMBOLS[0]

def makezip(sym=SYMBOL,day=DAY,micro=False,mutate=None):
    initial=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
    rows=[]
    for i in range(24):
        start=initial+i*3600000
        close=start+3600000-1
        if micro: start=start*1000;close=close*1000+999
        row=[str(start),"101","103","99","102","250",str(close),"25500","50","100","900","0"]
        if mutate:mutate(i,row)
        rows.append(",".join(row))
    raw="\n".join(rows).encode()
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{sym}-1h-{day}.csv",raw)
    return b.getvalue()

def checksum(data,sym=SYMBOL,day=DAY):
    return (hashlib.sha256(data).hexdigest()+f"  {sym}-1h-{day}.zip\n").encode()

def receipt(url,raw):
    t=m.iso(datetime.now(timezone.utc))
    return {"bytes":raw,"source_url":url,"request_utc":t,"received_utc":t,
            "http_date":None,"http_content_type":"application/zip",
            "http_etag":None,"byte_count":len(raw),
            "sha256":hashlib.sha256(raw).hexdigest()}

class TestSourceArchive(unittest.TestCase):
    def test_published_bounded_source_url(self):
        self.assertIn("data.binance.vision",m.canonical_url(SYMBOL,DAY))
        with self.assertRaises(ValueError):m.canonical_url("EVILUSDT",DAY)

    def test_future_archive_rejected(self):
        now=datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self.assertRaisesRegex(ValueError,"today/future"):m.canonical_url(SYMBOL,now)

    def test_checksum_authenticates_received_bytes(self):
        data=makezip()
        self.assertEqual(m.check_checksum(data,checksum(data),SYMBOL,DAY),hashlib.sha256(data).hexdigest())

    def test_checksum_payload_mismatch(self):
        data=makezip()
        with self.assertRaisesRegex(ValueError,"checksum mismatch"):
            m.check_checksum(data,checksum(b'other'),SYMBOL,DAY)

    def test_checksum_filename_must_match(self):
        data=makezip()
        with self.assertRaisesRegex(ValueError,"filename mismatch"):
            m.check_checksum(data,checksum(data,sym="WRONGUSDT"),SYMBOL,DAY)

    def test_parse_whole_day_millisecond_zip(self):
        parsed=m.parse_zip(makezip(),SYMBOL,DAY)
        self.assertEqual(parsed["rows"],24)
        self.assertTrue(parsed["last_candle_open_utc"].endswith("23:00:00+00:00"))
        self.assertTrue(parsed["last_candle_close_utc"].endswith("00:00:00+00:00"))

    def test_parse_whole_day_microsecond_zip(self):
        parsed=m.parse_zip(makezip(micro=True),SYMBOL,DAY)
        self.assertEqual(parsed["rows"],24)

    def test_daily_candles_must_have_24(self):
        data=makezip(mutate=lambda i,row:row.__setitem__(0,str(int(row[0])+1)) if i==12 else None)
        with self.assertRaisesRegex(ValueError,"out-of-day"):
            m.parse_zip(data,SYMBOL,DAY)

    def test_tampered_close_rejected(self):
        def tamper(i,row):
            if i==0:row[6]=str(int(row[6])-100)
        with self.assertRaisesRegex(ValueError,"out-of-day"):
            m.parse_zip(makezip(mutate=tamper),SYMBOL,DAY)

    def test_negative_volume_rejected(self):
        def tamper(i,row):
            if i==0:row[5]="-100"
        with self.assertRaisesRegex(ValueError,"OHLCV"):
            m.parse_zip(makezip(mutate=tamper),SYMBOL,DAY)

    def test_nonfinite_quote_volume_rejected(self):
        def tamper(i,row):
            if i==0:row[7]="NaN"
        with self.assertRaisesRegex(ValueError,"OHLCV"):
            m.parse_zip(makezip(mutate=tamper),SYMBOL,DAY)

    def test_wrong_csv_member_rejected(self):
        original=makezip()
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w") as z:
            z.writestr("../../../evil.csv","a,b")
        with self.assertRaisesRegex(ValueError,"unexpected archive member"):
            m.parse_zip(b.getvalue(),SYMBOL,DAY)

    def test_no_trades_or_holdout_in_manifest(self):
        def fake_get(url,limit):
            sym=next(s for s in m.SYMBOLS if f"/{s}/" in url)
            original=makezip(sym)
            blob=checksum(original,sym) if url.endswith(".CHECKSUM") else original
            return receipt(url,blob)
        with patch.object(m,"get",side_effect=fake_get):
            manifest,files=m.collect(DAY)
        self.assertEqual(len(files),3)
        self.assertEqual(set(manifest["assets"]),set(m.SYMBOLS))
        self.assertFalse(manifest["paper_publication_authorized"])
        self.assertFalse(manifest["promotion_authorized"])
        self.assertFalse(manifest["holdout_accessed"])
        self.assertFalse(manifest["historical_first_seen_authenticated"])
        self.assertEqual(manifest["economic_trials"],0)
        self.assertTrue(manifest["source_content_checksum_verified"])

    def test_only_old_day_not_new_paper_gain(self):
        with self.assertRaises(ValueError):
            m.canonical_url(SYMBOL,"2027-01-01")

    def test_reject_unsafe_query(self):
        with self.assertRaises(ValueError):
            m.get(m.BASE+"/BTCUSDT?source=untrusted",100)

    def test_first_safe_decision_after_observation(self):
        observed="2026-10-14T19:20:31+00:00"
        self.assertEqual(m.first_safe(observed),"2026-10-14T21:00:00+00:00")

if __name__=="__main__":
    unittest.main()
