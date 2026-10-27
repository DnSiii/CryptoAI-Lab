#!/usr/bin/env python3
"""HX official Binance spot taker-buy quote source ONLY, HQ checksum protocol, 2022-12..2024-12.
No prices are synthesized; 2023-03-24 partial/missing hours remain masked. No PnL.
"""
from __future__ import annotations
import csv,hashlib,io,json,zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import hq_gap_aware_spot_source as hq

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"hx_spot_flow_training"
FIELDS=("open_time_ms","asset","taker_buy_quote","spot_quote","full_hour")

def month(asset,ym):
    y,m=ym
    filename=f"{asset}-1h-{y}-{m:02d}.zip"
    url=f"{hq.SOURCE}/{asset}/1h/{filename}"
    raw=hq.get(url)
    checksum=hq.get(url+".CHECKSUM").decode("ascii").strip().split()
    if len(checksum)!=2 or checksum[1].lstrip("*")!=filename or hq.sha(raw)!=checksum[0].lower():
        raise ValueError("HX_SPOT_PUBLISHER_CHECKSUM_"+filename)
    if (y,m)==(2023,3) and hq.sha(raw)!=hq.PINNED_MARCH[asset]:
        raise ValueError("HX_SPOT_PINNED_MARCH_"+asset)
    validated,missing=hq.parse_month(raw,asset,y,m)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        rows=list(csv.reader(io.TextIOWrapper(z.open(filename[:-4]+".csv"),encoding="utf-8",newline="")))
    mapped={int(r[0]):r for r in rows}
    output=[]
    for item in validated:
        t=int(item[1]);eligible=int(item[3])
        if eligible:
            row=mapped[t]
            q=float(row[7]);buy=float(row[10])
            if q<=0 or not (0<=buy<=q+1e-6*max(1.,q)):
                raise ValueError("HX_SPOT_TAKER_VOLUME_"+filename)
            output.append((t,asset,row[10],row[7],1))
        else:
            output.append((t,asset,"","",0))
    return asset,ym,output,hq.sha(raw),len(missing)

def run():
    jobs=[(asset,ym) for asset in hq.ASSETS for ym in hq.MONTHS]
    result={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        tasks={pool.submit(month,a,ym):(a,ym) for a,ym in jobs}
        for f in as_completed(tasks):
            a,ym=tasks[f]
            try:result[(a,ym)]=f.result()
            except Exception as exc:raise ValueError(f"HX_SPOT_SOURCE_{a}_{ym}_{exc}") from exc
    receipts=[];matrix=[]
    for asset in hq.ASSETS:
        for ym in hq.MONTHS:
            _,_,rows,digest,gaps=result[(asset,ym)]
            matrix.extend(rows)
            receipts.append({"asset":asset,"month":f"{ym[0]}-{ym[1]:02d}","sha256":digest,"missing":gaps})
    manifest="".join(f'{r["asset"]}|{r["month"]}|{r["sha256"]}\n' for r in receipts).encode()
    if hq.sha(manifest)!=hq.PINNED_100_SHA_MANIFEST:
        raise ValueError("HX_SPOT_PINNED_MANIFEST")
    if len(matrix)!=73152 or sum(x[-1] for x in matrix)!=73144:
        raise ValueError("HX_SPOT_FULL_HOUR_COVERAGE")
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/"hx_spot_taker_quote.csv"
    with p.open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(FIELDS)
        # Canonical row-major hourly order, then BTC ETH BNB SOL.
        order={a:i for i,a in enumerate(hq.ASSETS)}
        w.writerows(sorted(matrix,key=lambda x:(x[0],order[x[1]])))
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    receipt={"decision":"PASS_HX_SPOT_TAKER_SOURCE_ONLY","csv_sha256":digest,
             "publisher_manifest_sha256":hq.PINNED_100_SHA_MANIFEST,
             "archives":len(receipts),"calendar_asset_hours":len(matrix),
             "eligible_asset_hours":73144,"masked_asset_hours":8,
             "missing_20230324_13_utc":4,"partial_20230324_12_utc":4,
             "validation_2025_read":False,"data_2026_read":False,
             "historical_system_pnl_computed":False,"trading_authorized":False}
    (OUT/"hx_spot_flow_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("HX_SPOT_TAKER_SOURCE_PASS",digest,flush=True)
if __name__=="__main__":run()
