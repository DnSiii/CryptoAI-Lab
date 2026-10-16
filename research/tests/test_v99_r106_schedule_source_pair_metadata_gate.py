"""DATA_ONLY synthetic GitHub source metadata invariants."""
import unittest
from research.tools import v99_r106_schedule_source_pair_metadata_gate as g

def run(i, name, hour="11", **kw):
    d=dict(id=i,name=name,event="schedule",head_branch="main",status="completed",
           conclusion="success",created_at="2026-10-16T"+hour+":40:00Z")
    d.update(kw)
    return d

def artifact(i, prefix, aid):
    return dict(id=aid,name=prefix+str(i),expired=False,size_in_bytes=100,
                workflow_run=dict(id=i))

class TestSourceMetadata(unittest.TestCase):
    def test_split_same_hour_never_atomic(self):
        a=run(38895514913,g.SPLIT)
        b=run(38896439936,g.SPLIT)
        d={a["id"]:[artifact(a["id"],g.SPLIT_PREFIX["market"],101)],
           b["id"]:[artifact(b["id"],g.SPLIT_PREFIX["terms"],102)]}
        out=g.audit([a,b],d.__getitem__)
        self.assertEqual(len(out["split_run_same_created_hour_collisions"]),1)
        self.assertEqual(out["atomic_metadata_candidates"],[])
        self.assertFalse(out["promotion_authorized"])
        self.assertFalse(out["minimum_two_consecutive_atomic_hours_authenticated"])

    def test_both_original_streams_same_run_are_metadata_only(self):
        r=run(38882428617,g.ATOMIC,hour="09")
        a=[artifact(r["id"],g.PREFIX["market"],103),
           artifact(r["id"],g.PREFIX["terms"],104)]
        out=g.audit([r],lambda _:a)
        self.assertEqual(len(out["atomic_metadata_candidates"]),1)
        self.assertFalse(out["paper_publication_authorized"])
        self.assertEqual(out["economic_trials"],0)

    def test_incomplete_atomic_denied(self):
        r=run(38882428617,g.ATOMIC)
        with self.assertRaisesRegex(ValueError,"incomplete_atomic"):
            g.audit([r],lambda i:[artifact(i,g.PREFIX["market"],101)])

    def test_mismatched_run_id_denied(self):
        r=run(38882428617,g.ATOMIC)
        a=artifact(r["id"],g.PREFIX["market"],101)
        a["workflow_run"]["id"]=999
        with self.assertRaisesRegex(ValueError,"invalid_source_artifact"):
            g.audit([r],lambda _:[a])

    def test_manual_run_cannot_qualify(self):
        r=run(38882428617,g.ATOMIC,event="workflow_dispatch")
        self.assertEqual(g.audit([r],lambda _:[])["atomic_metadata_candidates"],[])

    def test_two_nonadjacent_runs_never_prove_continuity(self):
        runs=[run(38850472892,g.ATOMIC,hour="04"),run(38882428617,g.ATOMIC,hour="09")]
        out=g.audit(runs,lambda i:[artifact(i,g.PREFIX["market"],i+1),
                                   artifact(i,g.PREFIX["terms"],i+2)])
        self.assertEqual(len(out["atomic_metadata_candidates"]),2)
        self.assertFalse(out["minimum_two_consecutive_atomic_hours_authenticated"])

if __name__=="__main__":
    unittest.main()
