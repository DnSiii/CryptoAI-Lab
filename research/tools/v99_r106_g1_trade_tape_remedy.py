"""G1 first-party 2022-03-20 FUTURES trades source remedy, no PnL.

Checks whether original daily trade tape contains the preregistered 220325
contracts missing/misidentified in the 2022-03 futureschain candle ZIP.
"""
from __future__ import annotations
import collections,csv,hashlib,io,json,sys,time,zipfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen

DAY="2022-03-20"
TARGET_SUFFIX="220325"
START=int(datetime(2022,3,20,tzinfo=timezone.utc).timestamp()*1000)
END=START+86400000-1

def get(url,limit):
    with urlopen(Request(url,headers={"User-Agent":"V99-G1-2022-original-trade-source/1.0"}),timeout=80) as response:
        if response.status!=200 or urlsplit(response.geturl()).hostname not in ("www.okx.com","static.okx.com"):
            raise ValueError("UNTRUSTED_OKX_REDIRECT")
        raw=response.read(limit+1)
    if not raw or len(raw)>limit:raise ValueError("ORIGINAL_RESPONSE_SIZE_INVALID")
    return raw

def main(folder):
    out=Path(folder);out.mkdir(parents=True,exist_ok=True)
    records=[]
    for asset in ("BTC","ETH"):
        target=f"{asset}-USDT-{TARGET_SUFFIX}"
        row={"asset":asset,"target":target,"status":"BLOCKED","issue":None}
        try:
            params={"module":"1","instType":"FUTURES","instFamilyList":asset+"-USDT",
                    "dateAggrType":"daily","begin":str(START),"end":str(END)}
            raw=get("https://www.okx.com/api/v5/public/market-data-history?"+urlencode(params),200000)
            obj=json.loads(raw)
            if obj.get("code")!="0":raise ValueError("LISTING_CODE_"+str(obj.get("code")))
            found=[]
            for g in obj.get("data",[]):
                for d in g.get("details",[]):
                    found.extend(d.get("groupDetails",[]))
            # Do not infer daily archive naming from a successful monthly response.
            matching=[x for x in found if x.get("filename","").startswith(asset+"-USDT-futureschain-trades-")
                      and DAY in x.get("filename","")]
            row["listing_filenames"]=[x.get("filename") for x in found]
            (out/(asset+"_listing.json")).write_bytes(raw)
            row["listing_sha256"]=hashlib.sha256(raw).hexdigest()
            if len(matching)!=1:raise ValueError("NO_UNIQUE_DAILY_ORIGINAL_TRADE_TAPE")
            item=matching[0];url=item["url"];p=urlsplit(url)
            if p.scheme!="https" or p.hostname!="static.okx.com" or not p.path.endswith("/"+item["filename"]):
                raise ValueError("UNTRUSTED_TRADE_ARCHIVE")
            data=get(url,120000000)
            (out/item["filename"]).write_bytes(data)
            row.update({"archive_file":item["filename"],"archive_sha256":hashlib.sha256(data).hexdigest(),
                        "archive_bytes":len(data)})
            counts=collections.Counter();first=[]
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for member in z.infolist():
                    if not member.filename.lower().endswith(".csv"):continue
                    if member.file_size>900000000:raise ValueError("OVERSIZED_TRADE_TAPE")
                    with z.open(member) as f:
                        for line in f:
                            if len(first)<2:first.append(line[:200].decode("utf-8","replace").strip())
                            if target.encode() in line:counts[target]+=1
            row.update({"status":"TARGET_TRADE_ROWS_PRESENT" if counts[target] else "TARGET_NOT_IN_TRADE_TAPE",
                        "target_line_count":counts[target],"first_csv_lines":first})
        except Exception as exc:
            row["issue"]=type(exc).__name__+":"+str(exc)[:300]
        records.append(row)
        print(json.dumps(row,sort_keys=True),flush=True)
        time.sleep(.25)
    report={"schema":"G1_MARCH_2022_OFFICIAL_DAILY_TRADE_TAPE_REMEDY",
            "records":records,"all_target_tapes_present":all(x["status"]=="TARGET_TRADE_ROWS_PRESENT" for x in records),
            "full_train_source_verified":False,"economic_train_executed":False,"roi_computed":False,
            "validation_opened":False,"holdout_opened":False,"orders_enabled":False,"promotion_authorized":False}
    (out/"trade_tape_probe.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: python -m research.tools.v99_r106_g1_trade_tape_remedy OUT")
    main(sys.argv[1])
