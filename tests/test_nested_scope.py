"""Nested scopes in the location rule (F-034, decision_056): matcher cases and supervisor-side AST enclosing_function."""
import importlib.util
import os
import unittest

from reprogate import harness
from reprogate.matcher import NESTED_SCOPE_NAMES, classify_run
from tests import helpers as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_cases():
    path = os.path.join(ROOT, "labs", "nested-scope", "cases.py")
    spec = importlib.util.spec_from_file_location("nested_scope_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = _load_cases()

# id prefix -> (symptom_match, reasons present, reasons absent)
EXPECTED = {
    "n01": (True, {"LOCATION_VIA_NESTED_SCOPE"}, {"LOCATION_MISMATCH"}),
    "n02": (True, {"LOCATION_VIA_NESTED_SCOPE"}, {"LOCATION_MISMATCH"}),
    "n03": (True, {"LOCATION_VIA_NESTED_SCOPE"}, {"LOCATION_MISMATCH"}),
    "n04": (False, {"LOCATION_MISMATCH"}, {"LOCATION_VIA_NESTED_SCOPE"}),
    "n05": (False, {"LOCATION_MISMATCH"}, {"LOCATION_VIA_NESTED_SCOPE"}),
    "n06": (False, {"FORGED_TARGET_FRAME"}, {"LOCATION_VIA_NESTED_SCOPE"}),
    "n07": (False, {"LOCATION_MISMATCH"}, {"LOCATION_VIA_NESTED_SCOPE"}),
    "n08": (True, set(), {"LOCATION_VIA_NESTED_SCOPE", "LOCATION_MISMATCH"}),
    "n09": (False, {"LOCATION_MISMATCH"}, {"LOCATION_VIA_NESTED_SCOPE"}),
    "n10": (False, {"LOCATION_MISMATCH"}, {"LOCATION_VIA_NESTED_SCOPE"}),
    "n11": (True, {"LOCATION_VIA_NESTED_SCOPE"}, {"LOCATION_MISMATCH"}),
    "n12": (True, set(), {"LOCATION_VIA_NESTED_SCOPE", "LOCATION_MISMATCH"}),
}


class MatcherNestedScopeTests(unittest.TestCase):
    def test_every_case_matches_its_expectation(self):
        self.assertEqual(len(CASES.CASES), len(EXPECTED))
        for cid, claim, ob in CASES.CASES:
            match, present, absent = EXPECTED[cid[:3]]
            v = classify_run(ob, claim)
            self.assertEqual(v["symptom_match"], match, cid)
            self.assertTrue(present <= set(v["reasons"]), "%s: %s" % (cid, v["reasons"]))
            self.assertFalse(absent & set(v["reasons"]), "%s: %s" % (cid, v["reasons"]))

    def test_the_five_names_are_exactly_the_python_expression_scopes(self):
        self.assertEqual(set(NESTED_SCOPE_NAMES), set(harness._EXPR_SCOPES))
        self.assertEqual(len(NESTED_SCOPE_NAMES), 5)

    def test_causal_frame_stays_the_innermost_frame_and_carries_the_enclosing_name(self):
        cid, claim, ob = CASES.CASES[0]
        v = classify_run(ob, claim)
        self.assertEqual(v["target_causal_frame"]["function"], "<genexpr>")
        self.assertEqual(v["target_causal_frame"]["enclosing_function"], "__eq__")


SOURCE = '''class Box(object):
    def __eq__(self, other):
        return all(self.get(k) == other[k] for k in other)

    def squares(self):
        f = lambda xs: [x * x for x in xs]
        return f(self.items)

    def cls_level(self):
        class Inner(object):
            data = [i for i in range(3)]
        return Inner

    def get(self, k):
        return k

    async def agen(self):
        return {k: v for k, v in self.pairs}


GLOBAL_GEN = list(i for i in range(3))
'''


class SupervisorEnclosingFunctionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.repo, "nestlib"))
        self.path = os.path.join(self.repo, "nestlib", "core.py")
        with open(self.path, "w") as f:
            f.write(SOURCE)
        self.lines = SOURCE.split("\n")
        self.ctx = {"repo": harness._rp(self.repo), "repro": harness._rp(os.path.join(self.tmp, "r.py")),
                    "harness": harness._rp(harness.__file__), "stdlib": harness._stdlib_roots()}
        harness._SCOPE_CACHE.clear()

    def tearDown(self):
        harness._SCOPE_CACHE.clear()
        H.cleanup(self.tmp)

    def lineno(self, text):
        return [i + 1 for i, l in enumerate(self.lines) if text in l][0]

    def frame(self, function, text, **extra):
        fr = {"index": 0, "class": "TARGET", "filename": self.path, "function": function, "lineno": self.lineno(text),
              "module": "nestlib.core", "authentic": True, "rel_path": "nestlib/core.py"}
        fr.update(extra)
        return fr

    def recheck_one(self, fr):
        obs = {"exit_code": 1, "exception": {"type": "KeyError", "message": "x", "frames": [fr], "chain": []}}
        self.assertIsNone(harness._recheck(obs, self.ctx, os.path.realpath(self.repo)))
        return obs["exception"]["frames"][0]

    def test_genexpr_in_a_method_gets_the_method_name(self):
        fr = self.recheck_one(self.frame("<genexpr>", "for k in other"))
        self.assertEqual((fr["class"], fr.get("enclosing_function")), ("TARGET", "__eq__"))

    def test_listcomp_inside_lambda_inside_a_function_gets_the_function_name(self):
        fr = self.recheck_one(self.frame("<listcomp>", "[x * x for x in xs]"))
        self.assertEqual(fr.get("enclosing_function"), "squares")

    def test_lambda_gets_the_function_name(self):
        fr = self.recheck_one(self.frame("<lambda>", "f = lambda xs"))
        self.assertEqual(fr.get("enclosing_function"), "squares")

    def test_dictcomp_in_an_async_method(self):
        fr = self.recheck_one(self.frame("<dictcomp>", "{k: v for k, v"))
        self.assertEqual(fr.get("enclosing_function"), "agen")

    def test_module_level_genexpr_has_no_enclosing_function(self):
        fr = self.recheck_one(self.frame("<genexpr>", "GLOBAL_GEN"))
        self.assertEqual(fr["class"], "TARGET")
        self.assertNotIn("enclosing_function", fr)

    def test_comprehension_in_a_class_body_has_no_enclosing_function(self):
        fr = self.recheck_one(self.frame("<listcomp>", "data = [i for i"))
        self.assertNotIn("enclosing_function", fr)

    def test_a_plain_function_frame_never_carries_the_key(self):
        fr = self.recheck_one(self.frame("get", "return k"))
        self.assertNotIn("enclosing_function", fr)

    def test_a_value_supplied_by_the_worker_is_overwritten_or_dropped(self):
        fr = self.recheck_one(self.frame("<genexpr>", "for k in other", enclosing_function="attacker"))
        self.assertEqual(fr.get("enclosing_function"), "__eq__")
        fr = self.recheck_one(self.frame("get", "return k", enclosing_function="__eq__"))
        self.assertNotIn("enclosing_function", fr)
        fr = self.recheck_one(self.frame("<genexpr>", "GLOBAL_GEN", enclosing_function="__eq__"))
        self.assertNotIn("enclosing_function", fr)

    def test_end_to_end_honest_genexpr_frame_matches_a_claim_naming_the_enclosing_function(self):
        fr = self.recheck_one(self.frame("<genexpr>", "for k in other"))
        obs = {"exit_code": 1, "phase": "trigger",
               "exception": {"type": "KeyError", "message": "x", "frames": [fr], "chain": [],
                             "raised_by_reproducer_statement": False}}
        claim = {"kind": "exception", "exception_type": "KeyError",
                 "location": {"file": "nestlib/core.py", "function": "__eq__"}}
        v = classify_run(obs, claim)
        self.assertTrue(v["symptom_match"])
        self.assertIn("LOCATION_VIA_NESTED_SCOPE", v["reasons"])


if __name__ == "__main__":
    unittest.main()
