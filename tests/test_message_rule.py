"""F-020: message anchor is required when the claim has one; oracle_required flag."""
import os
import unittest

from reprogate.matcher import classify_run
from reprogate.pipeline import evaluate, oracle
from tests import helpers as H


def obs(message, function="__setitem__", rel="lib/core.py"):
    frames = [{"index": 0, "class": "REPRODUCER", "function": "<module>"},
              {"index": 1, "class": "TARGET", "function": function, "rel_path": rel, "authentic": True}]
    return {"exit_code": 1, "phase": "trigger",
            "exception": {"type": "ValueError", "message": message, "frames": frames, "chain": []}}


CLAIM_MSG = {"kind": "exception", "exception_type": "ValueError", "message": "value too large",
             "location": {"file": "lib/core.py", "function": "__setitem__"}}
CLAIM_NOMSG = {"kind": "exception", "exception_type": "ValueError", "location": {"file": "lib/core.py", "function": "__setitem__"}}


class MessageRuleTests(unittest.TestCase):
    def test_message_match_with_location(self):
        self.assertTrue(classify_run(obs("value too large"), CLAIM_MSG)["symptom_match"])

    def test_other_message_same_location_no_longer_matches(self):
        v = classify_run(obs("invalid literal for int()"), CLAIM_MSG)
        self.assertFalse(v["symptom_match"])
        self.assertIn("MESSAGE_MISMATCH", v["reasons"])

    def test_claim_without_message_still_matches_by_location(self):
        self.assertTrue(classify_run(obs("anything"), CLAIM_NOMSG)["symptom_match"])
        self.assertFalse(classify_run(obs("anything", function="other"), CLAIM_NOMSG)["symptom_match"])


class OracleFlagTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.buggy = H.make_repo(os.path.join(self.tmp, "b"))
        self.fixed = H.make_repo(os.path.join(self.tmp, "f"), fixed=True)
        self.repro = H.write_repro(self.tmp, "good.py", H.GOOD_REPRO)

    def tearDown(self):
        H.cleanup(self.tmp)

    def test_plain_run_requires_oracle_and_oracle_bundles_do_not(self):
        kw = dict(runs=3, timeout=20, min_completed=3)
        o = evaluate(self.buggy, H.PYTHON, H.verified_claim(), self.repro, os.path.join(self.tmp, "run"), **kw)
        self.assertTrue(o["oracle_required"])
        oracle(self.buggy, self.fixed, H.PYTHON, H.verified_claim(), self.repro, os.path.join(self.tmp, "orc"), **kw)
        from reprogate.util import read_json
        self.assertFalse(read_json(os.path.join(self.tmp, "orc", "before", "outcome.json"))["oracle_required"])

    def test_no_symptom_no_flag(self):
        o = evaluate(self.fixed, H.PYTHON, H.verified_claim(), self.repro, os.path.join(self.tmp, "run2"),
                     runs=3, timeout=20, min_completed=3)
        self.assertFalse(o["oracle_required"])


if __name__ == "__main__":
    unittest.main()
