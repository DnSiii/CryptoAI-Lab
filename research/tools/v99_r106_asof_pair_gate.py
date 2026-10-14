"""Read-only paired prospective OKX price + terms DATA_ONLY integrity gate.

Rechecks original ZIP/HTTP raw hashes and source provenance in the separate
append-only receipt branch. No PnL/returns, research promotion, paper
publishing, holdout access or portfolio tuning. Never opens old V99 paper.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from research.tools import v99_r106_receipt_append as prices
from research.tools import v99_r106_terms_append as terms

def checked_original(source,expected,verifier):
    if not (source/"receipt_commit_provenance.json").is_file():
        raise ValueError("permanent receipt provenance missing")
    provenance=prices.strict((source/"receipt_commit_provenance.json").read_bytes())
    if provenance.get("paper_or_model_changes_allowed") is not False:
        raise ValueError("source receipt must never authorize trading")
    manifest_sha=hashlib.sha256((source/"manifest.json").read_bytes()).hexdigest()
    expected_sha=provenance.get("manifest_sha256",provenance.get("sha256_manifest"))
    if manifest_sha!=expected_sha:
        raise ValueError("archived manifest does not match append provenance")
    if provenance.get("run_id") is None:
        raise ValueError("missing source workflow run")
    with tempfile.TemporaryDirectory(prefix="v99-asof-audit-") as tmp:
        root=Path(tmp)
        for name in expected:
            raw=source/name
            if not raw.is_file() or raw.is_symlink():
                raise ValueError("missing/untrusted source raw bytes: "+name)
            shutil.copyfile(raw,root/name)
        return verifier(root),provenance

def audit(markets_dir:Path,terms_dir:Path):
    market,pmarket=checked_original(markets_dir,prices.EXPECTED,prices.verify_source)
    contract,pcontract=checked_original(terms_dir,terms.FILES,terms.validate)
    pm=prices.utc(market["last_received_utc"])
    pt=prices.utc(contract["acquisition_last_utc"])
    if pm.strftime("%Y-%m-%dT%H")!=pt.strftime("%Y-%m-%dT%H"):
        raise ValueError("market and contract observations in different UTC hours")
    if abs((pm-pt).total_seconds())>25*60:
        raise ValueError("terms/market observation >25m apart")
    first=max(prices.utc(market["earliest_candidate_decision_utc"]),
              prices.utc(contract["earliest_safe_decision_utc"]))
    safe=max(pm,pt).replace(minute=0,second=0,microsecond=0)+timedelta(hours=2)
    if first!=safe:
        raise ValueError("earliest source-safe decision not aligned")
    if set(market["instruments"])!=set(contract["contracts"]):
        raise ValueError("native pricing/funding symbols differ")
    latest={asset["latest_confirmed_close_utc"] for asset in market["instruments"].values()}
    if len(latest)!=1:
        raise ValueError("not the same five confirmed source closes")
    if prices.utc(next(iter(latest)))>min(pm,pt):
        raise ValueError("claimed price candle unclosed at observation time")
    if markets_dir.name!=pm.strftime("%Y-%m-%dT%H") or terms_dir.name!=pt.strftime("%Y-%m-%dT%H"):
        raise ValueError("archived evidence assigned to wrong UTC bucket")
    summary={}
    for inst in sorted(market["instruments"]):
        info=contract["contracts"][inst]["contract"]
        f=contract["contracts"][inst]["funding_notice"]
        if f.get("settled_cashflow_authenticated") is not False:
            raise ValueError("funding projection mislabelled as settled")
        summary[inst]={
          "bar_close_utc":market["instruments"][inst]["latest_confirmed_close_utc"],
          "contract_native_value":info["ctVal"],
          "contract_native_currency":info["ctValCcy"],
          "funding_observed_not_settled":f["observed_rate_not_settled"],
          "raw_bar_sha256":market["instruments"][inst]["source_raw_sha256"],
          "raw_funding_sha256":contract["contracts"][inst]["funding_raw_sha256"],
        }
    return {
        "status":"TWO_FIRST_PARTY_SOURCE_STREAMS_CONSISTENT_DATA_ONLY",
        "market_source_run":pmarket["run_id"],
        "terms_source_run":pcontract["run_id"],
        "market_acquired_utc":market["last_received_utc"],
        "terms_acquired_utc":contract["acquisition_last_utc"],
        "last_verified_bar_close_utc":next(iter(latest)),
        "earliest_safe_decision_utc":prices.iso(safe) if hasattr(prices,"iso") else safe.isoformat(),
        "assets":summary,
        "venue":"OKX_NOT_BINANCE",
        "exchange_signed_source_time":False,
        "historical_discovery_receipts_proven":False,
        "native_fee_tiers_attested":False,
        "funding_settlements_attested":False,
        "binance_r106_sleeve_transfer_validated":False,
        "continuous_forward_pnl_ledger":False,
        "paper_publication_authorized":False,
        "promotion_authorized":False,
        "holdout_accessed":False,
        "economic_trials":0,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--market",type=Path,required=True)
    p.add_argument("--terms",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=audit(args.market,args.terms)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"instruments":len(report["assets"]),
                      "market_run":report["market_source_run"],
                      "terms_run":report["terms_source_run"],
                      "publication_authorized":False},sort_keys=True))

if __name__=="__main__":
    main()
