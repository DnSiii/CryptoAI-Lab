#!/usr/bin/env python3
"""V98 Independent read-only official spot Dec-2022 gap forensics after source failure.
No gap filling, no PnL, no alternate source, no 2025.
"""
import csv,datetime as dt,hashlib,io,json,urllib.request,zipfile
from pathlib import Path
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
OUT=Path(__file__).resolve().parent/"spot_perp_gap_forensics.json"
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"V98-independent-gap-audit/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:return r.read()
def run():
    expected=[int((dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)+dt.timedelta(hours=h)).timestamp()*1000) for h in range(744)]
    result={}
    for asset in ASSETS:
        filename=f"{asset}-1h-2022-12.zip"
        url=f"https://data.binance.vision/data/spot/monthly/klines/{asset}/1h/{filename}"
        raw=get(url)
        digest=hashlib.sha256(raw).hexdigest()
        provider=get(url+".CHECKSUM").decode("ascii").strip().split()[0].lower()
        if digest!=provider:raise ValueError("FORENSIC_PROVIDER_SHA_MISMATCH "+asset)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            members=[n for n in z.namelist() if not n.endswith("/")]
            if members!=[filename.replace(".zip",".csv")]:raise ValueError("FORENSIC_ZIP_MEMBER "+asset)
            rows=list(csv.reader(io.TextIOWrapper(z.open(members[0]),encoding="utf-8")))
        times=[int(row[0]) for row in rows]
        if len(set(times))!=len(times):raise ValueError("FORENSIC_DUPLICATES "+asset)
        missing=sorted(set(expected)-set(times))
        extras=sorted(set(times)-set(expected))
        def iso(x):return dt.datetime.fromtimestamp(x/1000,dt.timezone.utc).isoformat()
        result[asset]={"provider_sha256":provider,"archive_rows":len(rows),
           "expected_hours":744,"missing_utc":[iso(x) for x in missing],
           "unexpected_utc":[iso(x) for x in extras],
           "strictly_increasing":all(x<y for x,y in zip(times,times[1:]))}
        print("SPOT_GAP_FORENSIC",asset,result[asset],flush=True)
    payload={"decision":"READ_ONLY_OFFICIAL_SPOT_GAP_EVIDENCE_NO_SOURCE_RESCUE",
       "historical_system_pnl_computed":False,"holdout_2025_read":False,
       "trading_authorized":False,"data":result}
    OUT.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":run()
