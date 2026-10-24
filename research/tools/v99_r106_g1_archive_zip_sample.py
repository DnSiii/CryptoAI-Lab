"""G1 original OKX FUTURES-chain 1m monthly ZIP source sample, no economic replay.

Uses the alternative official bulk listing confirmed in GitHub Actions 40047178570.
Only March 2022 and September 2023, both within sealed TRAIN. Never download
the adjacent April 2022 / October 2023 files returned by inclusive listing.
"""
from __future__ import annotations
import hashlib,io,json,sys,time,zipfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen

SAMPLES=(("2022-03","220325"),("2023-09","230929"))
ASSETS=("BTC","ETH")
MAX_ZIP=150_000_000
MAX_CSV=1_000_000_000
TRAIN_END=1696118400000

def ms(date):
    return int(datetime.fromisoformat(date).replace(tzinfo=timezone.utc).timestamp()*1000)

def get(url,limit):
    req=Request(url,headers={"User-Agent":"CryptoAI-V99-G1-source-only/1.0"})
    with urlopen(req,timeout=90) as resp:
        host=urlsplit(resp.geturl()).hostname
        if resp.status!=200 or host not in ("www.okx.com","static.okx.com"):
            raise ValueError("UNTRUSTED_OR_UNSUCCESSFUL_OKX_RESPONSE")
        data=resp.read(limit+1)
    if not data or len(data)>limit:raise ValueError("EMPTY_OR_OVERSIZED_ORIGINAL_RESPONSE")
    return data

def main(outdir):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    results=[]
    for month,expiry in SAMPLES:
        y,m=map(int,month.split("-"))
        nxt=f"{y+1}-01" if m==12 else f"{y}-{m+1:02d}"
        begin=ms(month+"-01T00:00:00")
        end=ms(nxt+"-01T00:00:00")-1
        assert end<TRAIN_END
        for asset in ASSETS:
            inst=f"{asset}-USDT"
            params={"module":"2","instType":"FUTURES","instFamilyList":inst,
                    "dateAggrType":"monthly","begin":str(begin),"end":str(end)}
            url="https://www.okx.com/api/v5/public/market-data-history?"+urlencode(params)
            record={"asset":asset,"month":month,"target_contract":f"{asset}-USDT-{expiry}",
                    "status":"BLOCKED_NO_ARCHIVE","issue":None}
            try:
                listing=get(url,250000)
                obj=json.loads(listing)
                if obj.get("code")!="0":raise ValueError("OKX_LISTING_CODE_"+str(obj.get("code")))
                items=[]
                for group in obj.get("data",[]):
                    for detail in group.get("details",[]):
                        items.extend(detail.get("groupDetails",[]))
                exact=f"{inst}-futureschain-candlesticks-{month}.zip"
                found=[v for v in items if v.get("filename")==exact]
                if len(found)!=1:raise ValueError("NO_UNIQUE_FIRST_PARTY_MONTHLY_ARCHIVE")
                download_url=found[0]["url"]
                u=urlsplit(download_url)
                if u.scheme!="https" or u.hostname!="static.okx.com" or not u.path.endswith("/"+exact):
                    raise ValueError("UNTRUSTED_FIRST_PARTY_ARCHIVE_URL")
                archive=get(download_url,MAX_ZIP)
                (out/exact).write_bytes(archive)
                record.update({"archive_file":exact,"archive_sha256":hashlib.sha256(archive).hexdigest(),
                               "archive_bytes":len(archive),
                               "listing_sha256":hashlib.sha256(listing).hexdigest()})
                (out/(exact+".listing.json")).write_bytes(listing)
                count=0;members=[];first_match=None
                with zipfile.ZipFile(io.BytesIO(archive)) as z:
                    for member in z.infolist():
                        if not member.filename.lower().endswith(".csv"):continue
                        if member.file_size>MAX_CSV:raise ValueError("OVERSIZED_CSV_MEMBER")
                        members.append({"name":member.filename,"size":member.file_size})
                        with z.open(member) as f:
                            for line in f:
                                if record["target_contract"].encode() in line:
                                    count+=1
                                    if first_match is None:first_match=line[:250].decode("utf-8","replace").strip()
                record.update({"status":"CONTRACT_ROWS_PRESENT" if count else "BLOCKED_NO_TARGET_CONTRACT_ROWS",
                               "target_contract_line_count":count,"csv_members":members,
                               "first_match_excerpt":first_match})
            except Exception as exc:
                record["issue"]=type(exc).__name__+":"+str(exc)[:300]
            results.append(record)
            print(json.dumps({k:record.get(k) for k in ("asset","month","status","target_contract_line_count","archive_bytes","issue")},sort_keys=True),flush=True)
            time.sleep(.25)
    report={"schema":"G1_FIRST_PARTY_EXPIRED_FUTURES_ARCHIVE_ZIP_SAMPLE_V1",
            "preregistration_commit":"5ff7194efde234309d52be64042f2af06cf2f8b8",
            "samples":results,
            "all_sample_contracts_present":all(x["status"]=="CONTRACT_ROWS_PRESENT" for x in results),
            "full_train_source_verified":False,"historical_economic_train_executed":False,
            "roi_computed":False,"validation_opened":False,"holdout_opened":False,
            "orders_enabled":False,"promotion_authorized":False}
    (out/"g1_zip_sample.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: python -m research.tools.v99_r106_g1_archive_zip_sample OUT")
    main(sys.argv[1])
