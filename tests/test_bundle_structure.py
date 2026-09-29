"""Hash problems in inspect and the structure check of verify (F-036)."""
import importlib.util
import os
import unittest

from reprogate.pipeline import evaluate, structure_problems
from reprogate.util import read_json
from tests import helpers as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAST = dict(runs=3, timeout=20, min_completed=3)

# the predictions in labs/bundle-structure/PREDICTIONS.md
EXPECTED = {
    "h01": ("exit 1", "-"), "h02": ("exit 1", "-"), "h03": ("exit 1", "-"),
    "h04": ("exit 2", "INVALID_BUNDLE"), "h05": ("exit 2", "INVALID_BUNDLE"),
    "h06": ("exit 2", "INVALID_BUNDLE"), "h07": ("exit 2", "INVALID_BUNDLE"),
    "h08": ("exit 1", "-"), "h09": ("exit 1", "-"),
    "h10": ("exit 1", "-"), "h11": ("exit 1", "-"), "h12": ("exit 1", "-"), "h13": ("exit 1", "-"),
    "h14": ("exit 1", "-"), "h15": ("exit 1", "-"),
}


def _load_cases():
    path = os.path.join(ROOT, "labs", "bundle-structure", "cases.py")
    spec = importlib.util.spec_from_file_location("bundle_structure_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = _load_cases()


class StructureCaseTests(unittest.TestCase):
    def test_every_case_as_predicted(self):
        self.assertEqual(len(CASES.CASES), len(EXPECTED))
        for case in CASES.CASES:
            fields = [x.strip() for x in CASES.run_case(*case).split("|")]
            self.assertEqual((fields[2], fields[3]), EXPECTED[case[0][:3]], case[0])


class StructureRuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.bundle = CASES.full(os.path.join(self.tmp, "b"))
        self.rec = CASES.valid_outcome()
        self.env = {"git": {"commit": None}}
        self.claim = {"claim": {"kind": "exception"}}

    def tearDown(self):
        H.cleanup(self.tmp)

    def problems(self, **changes):
        rec = dict(self.rec)
        rec.update(changes)
        return structure_problems(self.bundle, rec, self.env, self.claim)

    def test_valid_synthetic_bundle_has_no_problem(self):
        self.assertEqual(self.problems(), [])

    def test_each_rule_on_its_own(self):
        self.assertEqual(structure_problems(self.bundle, self.rec, {"git": {}}, self.claim),
                         ["environment.json has no git.commit"])
        self.assertEqual(structure_problems(self.bundle, self.rec, self.env, {"issue": 1}),
                         ["claim.json has no claim object"])
        self.assertEqual(self.problems(reproducer_name="other.py"), ["missing reproducer/other.py"])
        self.assertEqual(self.problems(reproducer_origin=3), ["outcome.json reproducer_origin is not a string"])
        self.assertEqual(self.problems(runs_requested=0), ["outcome.json runs_requested is not an integer >= 1"])
        self.assertEqual(self.problems(runs_requested=True), ["outcome.json runs_requested is not an integer >= 1"])
        self.assertEqual(self.problems(attempts_before_submission=-1),
                         ["outcome.json attempts_before_submission is not an integer >= 0"])

    def test_reproducer_name_cannot_leave_the_bundle(self):
        for name in ("../r.py", "..", ".", "", "sub/r.py", "sub\\r.py", "C:r.py", "/tmp/r.py", None, 7):
            p = self.problems(reproducer_name=name)
            self.assertEqual(len(p), 1, name)
            self.assertTrue(p[0].startswith("outcome.json reproducer_name is not a plain file name"), name)


class RealBundleTests(unittest.TestCase):
    def test_a_real_bundle_passes_the_structure_check(self):
        tmp = H.tmpdir()
        try:
            buggy = H.make_repo(os.path.join(tmp, "buggy"))
            repro = H.write_repro(tmp, "good.py", H.GOOD_REPRO)
            out = os.path.join(tmp, "ev")
            evaluate(buggy, H.PYTHON, H.verified_claim(), repro, out, **FAST)
            docs = [read_json(os.path.join(out, n)) for n in ("outcome.json", "environment.json", "claim.json")]
            self.assertEqual(structure_problems(out, *docs), [])
        finally:
            H.cleanup(tmp)


if __name__ == "__main__":
    unittest.main()
