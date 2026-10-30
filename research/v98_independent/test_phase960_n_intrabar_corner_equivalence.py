from phase960_n_intrabar_corner_equivalence import audit

def test_all_16_corners_equivalent_to_frozen_six():
    result=audit(samples=5000)
    assert result['six_vs_16_mismatches']==0
    assert result['full16_fail']>0
    assert result['full16_pass']>0

def test_seed_reproducibility():
    assert audit(seed=42,samples=1000)==audit(seed=42,samples=1000)
