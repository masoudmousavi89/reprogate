import unittest

from reprogate import constants as C
from reprogate.outcome import aggregate


def run(status=C.RUN_COMPLETED, match=False, clean=False, invalid=None):
    return {"status": status, "symptom_match": match, "clean_completion": clean, "invalid_reason": invalid}


class OutcomeTests(unittest.TestCase):
    def test_all_match(self):
        r = aggregate([run(match=True)] * 5)
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.SYMPTOM_REPRODUCED, C.NONE))

    def test_flaky(self):
        r = aggregate([run(match=True)] * 3 + [run()] * 2)
        self.assertEqual(r["outcome"], C.SYMPTOM_REPRODUCED_FLAKY)

    def test_single_match_inconclusive(self):
        r = aggregate([run(match=True)] + [run()] * 4)
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.INCONCLUSIVE, C.SINGLE_MATCH_ONLY))

    def test_no_match(self):
        r = aggregate([run(clean=True)] * 5)
        self.assertEqual(r["outcome"], C.NO_MATCHING_REPRODUCTION_FOUND)

    def test_env_failures_are_not_mismatches(self):
        r = aggregate([run(match=True)] * 3 + [run(C.RUN_ENV_FAILURE)] * 2)
        self.assertEqual(r["outcome"], C.SYMPTOM_REPRODUCED)  # 3/3 valid runs, 2 excluded but recorded
        self.assertEqual(r["counts"]["env_failures"], 2)

    def test_all_env_failure(self):
        r = aggregate([run(C.RUN_ENV_FAILURE)] * 5)
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.NOT_EVALUATED, C.ENVIRONMENT_UNAVAILABLE))

    def test_too_few_valid_runs(self):
        r = aggregate([run(match=True)] * 2 + [run(C.RUN_ENV_FAILURE)] * 3)
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.INCONCLUSIVE, C.INSUFFICIENT_VALID_RUNS))

    def test_timeouts_never_reproduce(self):
        r = aggregate([run(C.RUN_TIMEOUT)] * 5)
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.INCONCLUSIVE, C.TIMEOUT_NOT_CLAIMED))

    def test_repo_modified_dominates(self):
        r = aggregate([run(match=True)] * 4 + [run(C.RUN_INVALID, invalid=C.REPOSITORY_MODIFIED)])
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.INCONCLUSIVE, C.REPOSITORY_MODIFIED))

    def test_reproducer_rejected_short_circuits(self):
        r = aggregate([], reproducer_status=C.GATE_UNSAFE)
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.NOT_EVALUATED, C.REPRODUCER_UNSAFE))

    def test_insufficient_provenance_blocks_reproduced(self):
        r = aggregate([run(match=True)] * 5, provenance="INSUFFICIENT")
        self.assertEqual((r["outcome"], r["outcome_reason"]), (C.INCONCLUSIVE, C.CLAIM_PROVENANCE_INSUFFICIENT))

    def test_unverified_provenance_is_qualified(self):
        r = aggregate([run(match=True)] * 5, provenance="UNVERIFIED_ALLOWED")
        self.assertEqual(r["outcome"], C.SYMPTOM_REPRODUCED)
        self.assertEqual(r["outcome_qualifier"], "PROVENANCE_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
