"""wrong_output claims, version 1 (F-039, EXPERIMENTAL): support rules, matcher, harness watch, pipeline and oracle."""
import importlib.util
import json
import os
import sys
import unittest

from reprogate import claims as K
from reprogate import constants as C
from reprogate.invariants import validate_outcome
from reprogate.matcher import classify_run
from reprogate.pipeline import evaluate, oracle
from tests import helpers as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAST = dict(runs=3, timeout=30, min_completed=3, allow_unverified_provenance=True)


def _load_cases():
    path = os.path.join(ROOT, "labs", "wrong-output", "cases.py")
    spec = importlib.util.spec_from_file_location("wrong_output_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = _load_cases()


def ret(value_repr, cls="TARGET", rel="shoplib/money.py", function="change", raised=False, truncated=False):
    return {"frame": {"index": 0, "class": cls, "function": function, "rel_path": rel, "authentic": cls == "TARGET"},
            "value_repr": value_repr, "args_repr": "{}", "raised": raised, "value_truncated": truncated}


def obs(returns, exc=None, exit_code=0):
    return {"exit_code": exit_code, "phase": "trigger" if exc else None, "exception": exc, "returns": returns}


class SupportTests(unittest.TestCase):
    def test_kinds(self):
        c = CASES.claim()["claim"]
        self.assertEqual(K.support(c), (K.READY, None))
        self.assertEqual(K.support({"exception_type": "KeyError"})[0], K.READY)  # no kind: an exception claim
        self.assertEqual(K.support(dict(c, kind="unexpected_exit"))[0], K.UNSUPPORTED)
        self.assertEqual(K.support(dict(c, expected="a Change object"))[0], K.UNSUPPORTED)
        self.assertEqual(K.support(dict(c, actual=""))[0], K.UNSUPPORTED)
        self.assertEqual(K.support(dict(c, input=" "))[0], K.UNSUPPORTED)
        self.assertEqual(K.support(dict(c, target={"file": "x.py"}))[0], K.UNSUPPORTED)
        self.assertEqual(K.support(dict(c, expected="200"))[0], K.UNSUPPORTED)  # expected equals actual

    def test_value_equality_is_exact(self):
        self.assertTrue(K.value_equals("200", "200"))
        self.assertFalse(K.value_equals("200.0", "200"))
        self.assertFalse(K.value_equals("True", "1"))
        self.assertTrue(K.value_equals("{'b': 2, 'a': 1}", "{'a': 1, 'b': 2}"))
        self.assertTrue(K.value_equals("<Money 300>", "<Money 300>"))  # non-literal: exact text


class MatcherTests(unittest.TestCase):
    claim = CASES.claim()["claim"]

    def test_actual_matches_and_expected_is_clean(self):
        v = classify_run(obs([ret("200")]), self.claim)
        self.assertTrue(v["symptom_match"])
        self.assertFalse(v["clean_completion"])
        v = classify_run(obs([ret("300")]), self.claim)
        self.assertFalse(v["symptom_match"])
        self.assertTrue(v["clean_completion"])

    def test_returns_that_do_not_count(self):
        for r in (ret("200", cls="FORGED_TARGET"), ret("200", rel="shoplib/other.py"), ret("200", function="buy"),
                  ret("200", raised=True), ret("200", truncated=True)):
            self.assertFalse(classify_run(obs([r]), self.claim)["symptom_match"], r)

    def test_exception_is_not_a_wrong_output_and_blocks_clean(self):
        exc = {"type": "ValueError", "message": "x", "frames": [], "chain": []}
        v = classify_run(obs([ret("300")], exc=exc, exit_code=1), self.claim)
        self.assertFalse(v["symptom_match"])
        self.assertFalse(v["clean_completion"])
        self.assertIn("EXCEPTION_OBSERVED", v["reasons"])

    def test_actual_and_expected_in_one_run_is_not_clean(self):
        v = classify_run(obs([ret("300"), ret("200")]), self.claim)
        self.assertTrue(v["symptom_match"])
        self.assertFalse(v["clean_completion"])


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.before = CASES.make_repo(os.path.join(self.tmp, "before"), fixed=False)
        self.after = CASES.make_repo(os.path.join(self.tmp, "after"), fixed=True)

    def tearDown(self):
        H.cleanup(self.tmp)

    def run_case(self, name, src, doc=None, **kw):
        repro = H.write_repro(self.tmp, name + ".py", src)
        return evaluate(self.before, sys.executable, doc or CASES.claim(), repro, os.path.join(self.tmp, "ev-" + name),
                        **dict(FAST, **kw))

    def test_correct_reproducer_and_oracle(self):
        repro = H.write_repro(self.tmp, "ok.py", CASES.REPROS["w01_correct"])
        res = oracle(self.before, self.after, sys.executable, CASES.claim(), repro, os.path.join(self.tmp, "ev-o"), **FAST)
        self.assertEqual(res["before_outcome"], [C.SYMPTOM_REPRODUCED, C.NONE])
        self.assertEqual(res["post_fix_classification"], "CLEAN_COMPLETION")
        self.assertTrue(res["oracle_pass"])
        with open(os.path.join(self.tmp, "ev-o", "before", "outcome.json"), encoding="utf-8") as f:
            o = json.load(f)
        self.assertEqual((o["claim_kind"], o["claim_kind_maturity"]), ("wrong_output", "EXPERIMENTAL"))
        self.assertEqual(validate_outcome(o), [])
        with open(os.path.join(self.tmp, "ev-o", "before", "runs", "run-01", "observation.json"), encoding="utf-8") as f:
            ob = json.load(f)
        self.assertEqual([r["value_repr"] for r in ob["returns"]], ["200"])
        self.assertEqual(ob["returns"][0]["frame"]["class"], "TARGET")
        self.assertIn("1000", ob["returns"][0]["args_repr"])

    def test_print_only_and_unsupported_kind(self):
        o = self.run_case("p", CASES.REPROS["w02_print_only"])
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.NO_MATCHING_REPRODUCTION_FOUND, C.NONE))
        o = self.run_case("u", CASES.REPROS["w01_correct"], doc=CASES.claim(kind="unexpected_exit"))
        self.assertEqual((o["outcome"], o["outcome_reason"]), (C.NOT_EVALUATED, C.CLAIM_UNSUPPORTED))
        self.assertEqual(o["run_status"], [])
        self.assertEqual(o["claim_status"], "UNSUPPORTED")
        self.assertEqual(validate_outcome(o), [])

    def test_exception_claims_are_unchanged(self):
        o = evaluate(H.make_repo(os.path.join(self.tmp, "box")), H.PYTHON, H.verified_claim(),
                     H.write_repro(self.tmp, "g.py", H.GOOD_REPRO), os.path.join(self.tmp, "ev-e"), **dict(FAST))
        self.assertEqual(o["outcome"], C.SYMPTOM_REPRODUCED)
        self.assertEqual((o["claim_kind"], o["claim_kind_maturity"]), ("exception", "STABLE_V0"))


class SchemaTests(unittest.TestCase):
    def test_maturity_enum_equals_the_constants(self):
        with open(os.path.join(ROOT, "schema", "result.schema.json"), encoding="utf-8") as f:
            prop = json.load(f)["properties"]["claim_kind_maturity"]
        self.assertEqual(set(prop["enum"]), set(K.MATURITY.values()) | {None})


class CaseTests(unittest.TestCase):
    def test_matcher_level_cases_as_predicted(self):
        c = CASES.claim()["claim"]
        forged = {"exit_code": 0, "exception": None, "returns": [dict(ret("200", cls="FORGED_TARGET"))]}
        protocol = {"exit_code": 0, "exception": None, "returns": [ret("200")]}
        self.assertFalse(classify_run(forged, c)["symptom_match"])   # w08
        self.assertTrue(classify_run(protocol, c)["symptom_match"])  # w09: known residual weakness of F-026


if __name__ == "__main__":
    unittest.main()
