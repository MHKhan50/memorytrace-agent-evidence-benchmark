import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "llm_probe"))

from benchmark import generate_rows  # noqa: E402
from noise import add_noise, choose, sweep  # noqa: E402
import probe  # noqa: E402


def mem(mid, answer, verified=1, consented=1, age=1, relevant=1, gold="active"):
    return {"scenario_id": "s", "memory_id": mid, "answer": answer, "gold_answer": gold, "relevant": relevant,
            "source_verified": verified, "consented": consented, "age_days": age, "validity_days": 10,
            "evidence_quality": 0.9, "lexical_match": 0.5}


class NoiseTests(unittest.TestCase):
    def test_no_noise_changes_nothing(self):
        rows = generate_rows(5, 3)
        self.assertEqual(add_noise(rows, 0.0), rows)

    def test_conflict_abstain_refuses_disagreeing_pool(self):
        self.assertIsNone(choose([mem("a", "active"), mem("b", "paused")], "conflict_abstain"))
        self.assertEqual(choose([mem("a", "active"), mem("b", "paused", verified=0)], "conflict_abstain")["memory_id"], "a")

    def test_noise_is_monotone_and_scored_on_truth(self):
        rows = generate_rows(60, 5)
        res = {(r["label_noise"], r["policy"]): r for r in sweep(rows)}
        self.assertEqual(res[(0.0, "provenance_gate")]["unsupported_rate"], 0.0)
        self.assertGreaterEqual(res[(0.2, "provenance_gate")]["nonconsensual_rate"],
                                res[(0.05, "provenance_gate")]["nonconsensual_rate"])


class ProbeTests(unittest.TestCase):
    def test_prompt_and_scoring(self):
        cands = [r for r in generate_rows(1, 9)]
        p = probe.build_prompt(cands, "ru")
        self.assertIn("ka current status kya hai", p["user"])
        self.assertEqual(len(p["ids"]), 6)
        slot = p["ids"]["M2"]
        self.assertEqual(probe.score('{"memory_id": "M2", "answer": "active"}', p["ids"])["outcome"], slot)
        self.assertEqual(probe.score('{"memory_id": "NONE", "answer": "CONFLICT"}', p["ids"])["outcome"],
                         "flagged_conflict")
        self.assertEqual(probe.score('{"memory_id": "NONE", "answer": "unknown"}', p["ids"])["outcome"], "abstained")
        self.assertEqual(probe.score("not json", p["ids"])["outcome"], "abstained")

    def test_runs_offline(self):
        def fake(model, system, user):
            return json.dumps({"memory_id": "M1", "answer": "active"})
        old = probe.OUT
        with tempfile.TemporaryDirectory() as td:
            probe.OUT = Path(td)
            try:
                rows = probe.main(chat=fake, argv=["--models", "fake", "--n", "2"])
            finally:
                probe.OUT = old
        self.assertEqual(len(rows), 8)


if __name__ == "__main__":
    unittest.main()
