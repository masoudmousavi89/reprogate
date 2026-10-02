"""Layer 2 rules (labs/layer2-rules/PREDICTIONS.md): required fields of an exception claim (req_003) and the timeout rule (req_010)."""
import copy
import os
import tempfile
import unittest

from reprogate import claims
from reprogate import constants as C
from reprogate.invariants import validate_outcome
from reprogate.outcome import aggregate
from reprogate.pipeline import evaluate
from tests import helpers as H
from tests.test_outcome import run

FAST = dict(runs=3, timeout=30, min_completed=3)


class ExceptionClaimFieldTests(unittest.TestCase):
    def check(self, claim):
        return claims.support(claim)

    def test_valid_claims_stay_ready(self):
        for c in ({"exception_type": "IndexError"},
                  {"exception_type": "IndexError", "message": "pop from an empty deque"},
                  {"kind": "exception", "exception_type": "KeyError", "location": {"file": "a/b.py"}},
                  {"exception_type": "KeyError", "location": {"function": "f"}},
                  {"exception_type": "KeyError", "location": {"file": "a.py", "function": "f"}, "message": None}):
            self.assertEqual(self.check(c), (claims.READY, None), c)

    def test_missing_or_bad_type_is_unsupported(self):
        for c in ({}, {"kind": "exception"}, {"exception_type": ""}, {"exception_type": "   "}, {"exception_type": None},
                  {"exception_type": 5}, {"exception_type": ["IndexError"]}):
            status, note = self.check(c)
            self.assertEqual(status, claims.UNSUPPORTED, c)
            self.assertIn("exception_type", note)

    def test_bad_optional_fields_are_unsupported_with_their_name(self):
        cases = [({"exception_type": "E", "message": 5}, "message"),
                 ({"exception_type": "E", "location": "a.py"}, "location"),
                 ({"exception_type": "E", "location": {"file": ""}}, "location.file"),
                 ({"exception_type": "E", "location": {"function": None}}, "location.function")]
        for c, name in cases:
            status, note = self.check(c)
            self.assertEqual(status, claims.UNSUPPORTED, c)
            self.assertIn(name, note)

    def test_non_object_claim_is_unsupported(self):
        for c in (None, "IndexError", ["x"], 3):
            self.assertEqual(self.check(c)[0], claims.UNSUPPORTED)

    def test_wrong_output_and_unknown_kinds_are_unchanged(self):
        self.assertEqual(self.check({"kind": "unexpected_exit"})[0], claims.UNSUPPORTED)
        self.assertEqual(self.check({"kind": "wrong_output"})[0], claims.UNSUPPORTED)  # no target

    def test_real_run_without_type_is_not_evaluated_and_valid(self):
        tmp = H.tmpdir()
        self.addCleanup(H.cleanup, tmp)
        buggy = H.make_repo(os.path.join(tmp, "buggy"))
        doc = copy.deepcopy(H.CLAIM)  # unfrozen: a frozen claim that is edited is refused earlier (F-042)
        del doc["claim"]["exception_type"]
        repro = H.write_repro(tmp, "r.py", H.GOOD_REPRO)
        o = evaluate(buggy, H.PYTHON, doc, repro, os.path.join(tmp, "ev"), allow_unverified_provenance=True, **FAST)
        self.assertEqual((o["claim_status"], o["outcome"], o["outcome_reason"]),
                         ("UNSUPPORTED", C.NOT_EVALUATED, C.CLAIM_UNSUPPORTED))
        self.assertEqual(o["run_status"], [])
        self.assertIn("exception_type", o["claim_support_note"])
        self.assertEqual(validate_outcome(o), [])


class TimeoutRuleTests(unittest.TestCase):
    def verdict(self, runs, **kw):
        r = aggregate(runs, **kw)
        return r["outcome"], r["outcome_reason"]

    TIMEOUT = (C.INCONCLUSIVE, C.TIMEOUT_NOT_CLAIMED)

    def test_any_timeout_is_inconclusive(self):
        T = run(C.RUN_TIMEOUT)
        self.assertEqual(self.verdict([run(match=True)] * 4 + [T]), self.TIMEOUT)  # was SYMPTOM_REPRODUCED
        self.assertEqual(self.verdict([run(clean=True)] * 3 + [T] * 2), self.TIMEOUT)  # was NO_MATCHING
        self.assertEqual(self.verdict([T] + [run(C.RUN_ENV_FAILURE)] * 4), self.TIMEOUT)  # was INSUFFICIENT_VALID_RUNS
        self.assertEqual(self.verdict([T] * 5), self.TIMEOUT)  # unchanged
        self.assertEqual(self.verdict([run(match=True)] * 3 + [run()] * 1 + [T]), self.TIMEOUT)  # was FLAKY

    def test_dominating_reasons_still_win(self):
        T = run(C.RUN_TIMEOUT)
        mod = run(C.RUN_INVALID, invalid=C.REPOSITORY_MODIFIED)
        self.assertEqual(self.verdict([T, mod] + [run(match=True)] * 3), (C.INCONCLUSIVE, C.REPOSITORY_MODIFIED))
        harness = run(C.RUN_INVALID, invalid="HARNESS_ERROR")
        self.assertEqual(self.verdict([T, harness] + [run(match=True)] * 3), (C.INCONCLUSIVE, C.VERIFIER_INTERNAL_ERROR))
        self.assertEqual(self.verdict([T] * 2, claim_status="UNSUPPORTED"), (C.NOT_EVALUATED, C.CLAIM_UNSUPPORTED))
        self.assertEqual(self.verdict([T], reproducer_status=C.GATE_REJECTED), (C.NOT_EVALUATED, C.REPRODUCER_REJECTED))

    def test_no_timeout_means_old_behaviour(self):
        self.assertEqual(self.verdict([run(match=True)] * 5), (C.SYMPTOM_REPRODUCED, C.NONE))
        self.assertEqual(self.verdict([run(match=True)] * 3 + [run(C.RUN_ENV_FAILURE)] * 2), (C.SYMPTOM_REPRODUCED, C.NONE))
        self.assertEqual(self.verdict([run(match=True)] * 2 + [run(C.RUN_ENV_FAILURE)] * 3),
                         (C.INCONCLUSIVE, C.INSUFFICIENT_VALID_RUNS))

    def _outcome_record(self, runs):
        r = aggregate(runs)
        return {"outcome": r["outcome"], "outcome_reason": r["outcome_reason"], "outcome_qualifier": None,
                "claim_status": "READY", "reproducer_status": C.GATE_VALID, "claim_provenance": "VERIFIED",
                "run_status": [x["status"] for x in runs], "counts": r["counts"], "min_completed": 3,
                "runs_requested": len(runs), "oracle_required": False}

    def test_invariants_accept_the_new_shape_and_old_shape_and_refuse_a_lie(self):
        T = run(C.RUN_TIMEOUT)
        self.assertEqual(validate_outcome(self._outcome_record([run(match=True)] * 4 + [T])), [])  # new: some completed
        self.assertEqual(validate_outcome(self._outcome_record([T] * 5)), [])  # old: none completed
        bad = self._outcome_record([run(clean=True)] * 5)
        bad["outcome"], bad["outcome_reason"] = C.INCONCLUSIVE, C.TIMEOUT_NOT_CLAIMED  # claims a timeout that is not there
        self.assertTrue(any(v.startswith("RUN_LINK") for v in validate_outcome(bad)))


if __name__ == "__main__":
    unittest.main()
