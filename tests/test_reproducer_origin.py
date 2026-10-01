"""Reproducer origin evidence (F-043) on a SYNTHETIC library: verbatim must be byte-identical, adaptations keep a diff."""
import copy
import json
import os
import subprocess
import sys
import unittest

from reprogate.evidence import verify_hashes
from reprogate.invariants import validate_outcome
from reprogate.pipeline import evaluate
from tests import helpers as H

FAST = dict(runs=3, timeout=20, min_completed=3)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OriginEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = H.tmpdir()
        self.repo = H.make_repo(os.path.join(self.tmp, "buggy"))
        self.claim = H.verified_claim()
        self.repro = H.write_repro(self.tmp, "repro.py", H.GOOD_REPRO)
        self.src_identical = H.write_repro(self.tmp, "same.txt", H.GOOD_REPRO)
        self.src_other = H.write_repro(self.tmp, "other.txt", ">>> from minilib import Box\n>>> b = Box(1)\n")

    def tearDown(self):
        H.cleanup(self.tmp)

    def run_case(self, name, **kw):
        out = os.path.join(self.tmp, "ev-" + name)
        return evaluate(self.repo, H.PYTHON, self.claim, self.repro, out, **dict(FAST, **kw)), out

    def refuses(self, name, **kw):
        out = os.path.join(self.tmp, "ev-" + name)
        with self.assertRaises(ValueError):
            evaluate(self.repo, H.PYTHON, self.claim, self.repro, out, **dict(FAST, **kw))
        self.assertFalse(os.path.exists(os.path.join(out, "outcome.json")))

    def test_adapted_without_a_source_is_recorded_as_undocumented(self):
        o, out = self.run_case("a0", origin="AGENT_ADAPTED")
        self.assertEqual(o["reproducer_origin_evidence"], "NONE")
        self.assertNotIn("reproducer_origin_source_sha256", o)
        self.assertFalse(os.path.exists(os.path.join(out, "origin")))

    def test_adapted_with_a_source_keeps_source_diff_and_hashes(self):
        o, out = self.run_case("a1", origin="AGENT_ADAPTED", origin_source=self.src_other)
        self.assertEqual(o["reproducer_origin_evidence"], "SOURCE_AND_DIFF")
        diff = os.path.join(out, "origin", "adaptation.diff")
        self.assertTrue(os.path.isfile(os.path.join(out, "origin", "source.txt")))
        self.assertGreater(os.path.getsize(diff), 0)
        self.assertIn("reproducer_origin_source_sha256", o)
        self.assertIn("reproducer_origin_diff_sha256", o)
        self.assertEqual(validate_outcome(o), [])

    def test_adapted_with_an_identical_source_has_an_empty_diff(self):
        o, out = self.run_case("a2", origin="AGENT_ADAPTED", origin_source=self.src_identical)
        self.assertEqual(o["reproducer_origin_evidence"], "SOURCE_AND_DIFF")
        self.assertEqual(os.path.getsize(os.path.join(out, "origin", "adaptation.diff")), 0)

    def test_verbatim_with_an_identical_source_is_accepted(self):
        o, out = self.run_case("v1", origin="ISSUE_VERBATIM_SNIPPET", origin_source=self.src_identical)
        self.assertEqual(o["reproducer_origin_evidence"], "IDENTICAL_TO_SOURCE")
        self.assertEqual(o["reproducer_origin_source_sha256"], o["reproducer_sha256"])
        self.assertFalse(os.path.exists(os.path.join(out, "origin", "adaptation.diff")))
        self.assertEqual(validate_outcome(o), [])

    def test_verbatim_one_extra_byte_is_refused_before_anything_runs(self):
        src = H.write_repro(self.tmp, "extra.txt", H.GOOD_REPRO + b"\n")
        self.refuses("v2", origin="ISSUE_VERBATIM_SNIPPET", origin_source=src)

    def test_verbatim_without_a_source_is_refused(self):
        self.refuses("v3", origin="ISSUE_VERBATIM_SNIPPET")

    def test_authored_origins_take_no_source(self):
        o, _ = self.run_case("h1", origin="HUMAN_AUTHORED")
        self.assertEqual(o["reproducer_origin_evidence"], "NOT_APPLICABLE")
        self.refuses("h2", origin="AGENT_AUTHORED", origin_source=self.src_identical)

    def test_an_edited_diff_is_caught_by_the_bundle_hashes(self):
        _, out = self.run_case("e1", origin="AGENT_ADAPTED", origin_source=self.src_other)
        self.assertTrue(verify_hashes(out)[0])
        with open(os.path.join(out, "origin", "adaptation.diff"), "ab") as f:
            f.write(b"# edited\n")
        ok, problems = verify_hashes(out)
        self.assertFalse(ok)
        self.assertEqual(len(problems), 1)

    def test_invariants_on_the_recorded_fields(self):
        o, _ = self.run_case("i1", origin="AGENT_ADAPTED", origin_source=self.src_other)

        def violations(mutate):
            x = copy.deepcopy(o)
            mutate(x)
            return len(validate_outcome(x))
        self.assertEqual(violations(lambda x: None), 0)
        self.assertEqual(violations(lambda x: x.pop("reproducer_origin_diff_sha256")), 1)
        self.assertEqual(violations(lambda x: x.update(reproducer_origin_evidence="BOGUS")), 1)
        self.assertEqual(violations(lambda x: x.update(reproducer_origin_evidence="IDENTICAL_TO_SOURCE",
                                                       reproducer_origin_source_sha256="0" * 64)), 1)

        def old_record(x):
            for k in ("reproducer_origin_evidence", "reproducer_origin_source_sha256", "reproducer_origin_diff_sha256"):
                x.pop(k, None)
        self.assertEqual(violations(old_record), 0)

    def test_cli_refuses_a_verbatim_label_without_a_source_with_exit_code_2(self):
        claim = os.path.join(self.tmp, "claim.json")
        with open(claim, "w") as f:
            json.dump(self.claim, f)
        p = subprocess.run([sys.executable, "-m", "reprogate", "run", "--repo", self.repo, "--python", H.PYTHON,
                            "--claim", claim, "--reproducer", self.repro, "--out", os.path.join(self.tmp, "cli-out"),
                            "--origin", "ISSUE_VERBATIM_SNIPPET", "--allow-host-execution"],
                           cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("ISSUE_VERBATIM_SNIPPET", p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "cli-out", "outcome.json")))


if __name__ == "__main__":
    unittest.main()
