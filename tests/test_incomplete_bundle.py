"""Incomplete and unreadable bundles (F-035): exit 2 with INVALID_BUNDLE, exit 1 kept for readable invalid bundles."""
import contextlib
import importlib.util
import io
import os
import unittest

from reprogate import cli
from reprogate.evidence import BundleError, load_bundle_json
from reprogate.pipeline import evaluate
from tests import helpers as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAST = dict(runs=3, timeout=20, min_completed=3)

# case id -> (exit code, INVALID_BUNDLE on stderr); the predictions in labs/incomplete-bundle/PREDICTIONS.md
EXPECTED = {
    "b01": ("exit 2", "INVALID_BUNDLE"), "b02": ("exit 2", "INVALID_BUNDLE"), "b03": ("exit 2", "INVALID_BUNDLE"),
    "b04": ("exit 2", "INVALID_BUNDLE"), "b05": ("exit 2", "INVALID_BUNDLE"), "b06": ("exit 1", "-"),
    "b07": ("exit 0", "-"), "b08": ("exit 0", "-"), "b09": ("exit 1", "-"),
    "b10": ("exit 2", "INVALID_BUNDLE"), "b11": ("exit 2", "INVALID_BUNDLE"), "b12": ("exit 2", "INVALID_BUNDLE"),
    "b13": ("exit 2", "INVALID_BUNDLE"), "b14": ("exit 1", "-"), "b15": ("exit 2", "INVALID_BUNDLE"),
}


def _load_cases():
    path = os.path.join(ROOT, "labs", "incomplete-bundle", "cases.py")
    spec = importlib.util.spec_from_file_location("incomplete_bundle_cases", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES = _load_cases()


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


class SyntheticBundleTests(unittest.TestCase):
    def test_every_case_as_predicted(self):
        self.assertEqual(len(CASES.CASES), len(EXPECTED))
        for case in CASES.CASES:
            fields = [x.strip() for x in CASES.run_case(*case).split("|")]
            self.assertEqual((fields[2], fields[3]), EXPECTED[case[0][:3]], case[0])

    def test_problems_are_named(self):
        tmp = H.tmpdir()
        try:
            with self.assertRaises(BundleError) as cm:
                load_bundle_json(os.path.join(tmp, "absent"), ["outcome.json"])
            self.assertEqual(cm.exception.problems, ["evidence path is not a folder"])
            bundle = CASES.real_shape(os.path.join(tmp, "b"))
            with self.assertRaises(BundleError) as cm:
                load_bundle_json(bundle, ["outcome.json", "environment.json", "claim.json"])
            self.assertEqual(cm.exception.problems, ["missing outcome.json", "missing environment.json"])
            code, _out, err = _run(["inspect", "--evidence", bundle])
            self.assertEqual(code, 2)
            self.assertIn("INVALID_BUNDLE: missing outcome.json", err)
        finally:
            H.cleanup(tmp)

    def test_missing_optional_field_is_printed_as_dash(self):
        tmp = H.tmpdir()
        try:
            bundle = CASES.without_sandbox(os.path.join(tmp, "b"))
            code, out, _err = _run(["inspect", "--evidence", bundle])
            self.assertEqual(code, 0)
            self.assertIn("sandbox            : -", out)
        finally:
            H.cleanup(tmp)


class RealBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.buggy = H.make_repo(os.path.join(self.tmp, "buggy"))

    def tearDown(self):
        H.cleanup(self.tmp)

    def test_complete_bundle_still_verifies_through_the_cli(self):
        repro = H.write_repro(self.tmp, "good.py", H.GOOD_REPRO)
        out = os.path.join(self.tmp, "ev")
        evaluate(self.buggy, H.PYTHON, H.verified_claim(), repro, out, **FAST)
        code, text, err = _run(["inspect", "--evidence", out])
        self.assertEqual(code, 0)
        self.assertNotIn("INVALID_BUNDLE", err)
        code, text, err = _run(["verify", "--evidence", out, "--repo", self.buggy, "--python", H.PYTHON,
                                "--allow-host-execution"])
        self.assertEqual(code, 0, err)
        self.assertIn("VERIFY PASS", text)


if __name__ == "__main__":
    unittest.main()
