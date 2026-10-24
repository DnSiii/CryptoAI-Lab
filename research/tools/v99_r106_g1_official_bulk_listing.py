"""G1 alternative first-party OKX bulk-archive discovery for expired dated futures.

READ ONLY; no market returns, strategy evaluation, orders, validation or holdout.
Tests only the two public historical archive modules (trade/candle) and fixed
early/late TRAIN months; saves original listing bytes and hashes.
"""
from __future__ import annotations
import hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

END_TRAIN=1696118400000
MODULES=("1","2")
ASSETS=("BTC","ETH")
MONTHS=("2022-03","2023-09")

def ms(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()*1000)

def main(outdir):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    probes=[]
    for month in MONTHS:
        year,mo=map(int,month.split("-"))
        next_month=f"{year+1}-01" if mo==12 else f"{year}-{mo+1:02d}"
        begin=ms(month+"-01T00:00:00")
        end=ms(next_month+"-01T00:00:00")-1
        assert end<END_TRAIN
        for asset in ASSETS:
            for module in MODULES:
                params={"module":module,"instType":"FUTURES",
                        "instFamilyList":asset+"-USDT",
                        "dateAggrType":"monthly","begin":str(begin),"end":str(end)}
                url="https://www.okx.com/api/v5/public/market-data-history?"+urlencode(params)
                raw=b"";status=None;error=None
                try:
                    with urlopen(Request(url,headers={"User-Agent":"V99-G1-archive-listing/1.0"}),timeout=25) as response:
                        status=response.status;raw=response.read(1000000)
                except HTTPError as exc:
                    status=exc.code;raw=exc.read(1000000);error="HTTP_"+str(status)
                except (URLError,TimeoutError,OSError) as exc:
                    error=type(exc).__name__
                name=f"{asset}_{month}_module{module}.json"
                (out/name).write_bytes(raw)
                obj=None; filenames=[]
                try:
                    obj=json.loads(raw)
                    for group in obj.get("data",[]):
                        for detail in group.get("details",[]):
                            for entry in detail.get("groupDetails",[]):
                                if isinstance(entry,dict) and isinstance(entry.get("filename"),str):
                                    filenames.append(entry["filename"])
                except (ValueError,TypeError,AttributeError):
                    error=error or "UNPARSEABLE_LISTING"
                probes.append({"asset":asset,"month":month,"module":module,
                               "request_url":url,"http_status":status,
                               "okx_code":obj.get("code") if isinstance(obj,dict) else None,
                               "okx_message":obj.get("msg") if isinstance(obj,dict) else None,
                               "filenames":filenames,
                               "file":name,"raw_sha256":hashlib.sha256(raw).hexdigest(),
                               "raw_bytes":len(raw),"error":error})
                print(json.dumps({k:probes[-1][k] for k in ("asset","month","module","okx_code","filenames","error")},sort_keys=True),flush=True)
                time.sleep(.25)
    report={"schema":"G1_FIRST_PARTY_BULK_LISTING_ONLY_V1","probes":probes,
            "status":"SOURCE_LISTING_ONLY_NOT_CONTRACT_VERIFIED",
            "preregistration_commit":"5ff7194efde234309d52be64042f2af06cf2f8b8",
            "full_futures_train_verified":False,"economic_train_executed":False,
            "roi_computed":False,"validation_opened":False,"holdout_opened":False,
            "orders_enabled":False,"promotion_authorized":False}
    (out/"g1_bulk_listing.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: python -m research.tools.v99_r106_g1_official_bulk_listing OUT")
    main(sys.argv[1])
