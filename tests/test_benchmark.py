import tempfile
import unittest
from pathlib import Path
from benchmark import generate_rows, evaluate, summarize, select_candidate, POLICIES, run

class MemoryTraceTests(unittest.TestCase):
    def test_generator_is_deterministic(self):
        self.assertEqual(generate_rows(4, 7), generate_rows(4, 7))

    def test_candidate_count(self):
        self.assertEqual(len(generate_rows(9, 11)), 54)

    def test_every_policy_has_one_decision_per_scenario(self):
        rows = generate_rows(12, 13)
        decisions = evaluate(rows)
        self.assertEqual(len(decisions), 12 * len(POLICIES))

    def test_strict_policy_never_selects_unverified_or_unconsented(self):
        rows = generate_rows(50, 99)
        ds = [d for d in evaluate(rows) if d["policy"] == "strict_evidence" and d["answered"]]
        for d in ds:
            self.assertEqual(d["selected_verified"], 1)
            self.assertEqual(d["selected_consented"], 1)
            self.assertEqual(d["selected_stale"], 0)

    def test_summary_has_all_policies(self):
        summary = summarize(evaluate(generate_rows(8, 2)))
        self.assertEqual({r["policy"] for r in summary}, set(POLICIES))

    def test_empty_eligible_pool_abstains(self):
        rows = [{"scenario_id":"x","relevant":0,"source_verified":0,"consented":0,
                 "age_days":0,"validity_days":5,"lexical_match":.9,"evidence_quality":.9,
                 "answer":"active","memory_id":"x1"}]
        self.assertIsNone(select_candidate(rows, "provenance_gate"))
        self.assertIsNone(select_candidate(rows, "strict_evidence"))

    def test_run_writes_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            summary = run(3, 4, td)
            self.assertEqual(len(summary), 4)
            self.assertTrue((Path(td)/"data/scenarios.csv").exists())
            self.assertTrue((Path(td)/"outputs/summary.json").exists())

if __name__ == "__main__":
    unittest.main()
