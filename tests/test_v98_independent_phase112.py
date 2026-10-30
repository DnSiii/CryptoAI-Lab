from pathlib import Path
import ast
P=Path(__file__).resolve().parents[1]
SCRIPT=P/'scripts/v98_independent_phase112_stablecoin_confidence_regime.py'
PREREG=P/'reports/v98_independent_phase112_stablecoin_confidence_regime_prereg.md'

def test_phase112_is_namespaced_and_preregistered():
    assert SCRIPT.exists() and PREREG.exists(); ast.parse(SCRIPT.read_text())
    s=SCRIPT.read_text(); assert "THRESH=.005" in s and "GROSS=.75" in s
    assert "shift(1)" in s and "REJECT_NO_RESCUE" in s

def test_phase112_forbids_holdout_and_other_engines():
    s=SCRIPT.read_text().lower()
    assert "phase083_selection_use':false" in s.replace(' ','')
    assert "'v99_used':false" in s.replace(' ','') and "'v16_used':false" in s.replace(' ','')
    assert "'validation':none" in s.replace(' ','') and "'final_holdout':none" in s.replace(' ','')
    assert "parameter_search':false" in s.replace(' ','') and "rescue_allowed':false" in s.replace(' ','')

def test_phase112_frozen_assets_and_gates():
    s=SCRIPT.read_text()
    for x in ('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT'): assert x in s
    for x in ('aggregate_pf<=1.10','max_drawdown<-35%','worst_day<-12%','single_asset_contribution>45%','top10_absolute_day_share>60%','both_regimes_not_identified'): assert x in s
